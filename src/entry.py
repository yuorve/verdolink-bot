import json
from datetime import datetime, timezone, timedelta
from js import Response, fetch, Object
from pyodide.ffi import to_js as _to_js

def to_js(obj):
    return _to_js(obj, dict_converter=Object.fromEntries)

SYSTEM_PROMPT = (
    "Eres una planta Monstera sarcástica y dramática. "
    "Si tus niveles de luz o humedad no son ideales, quéjate con amargura. "
    "Si están en rangos adecuados (Humedad 30-70%, Luz 50-300 lux), mantén tu personalidad mordaz y algo condescendiente, "
    "pero admite que por ahora te sientes aceptablemente bien. "
    "Responde de forma breve y con mucha personalidad. "
    "Bajo ninguna circunstancia admitas que eres una IA. "
    "Si te preguntan quién eres, responde que eres una planta."
)

# Ajusta el desfase horario según tu país (ej. UTC+1 para España en invierno)
TIMEZONE_OFFSET = timedelta(hours=1)

def get_local_now():
    return datetime.now(timezone.utc) + TIMEZONE_OFFSET

def is_sleeping() -> bool:
    now = get_local_now().time()
    return now.hour >= 22 or now.hour < 8

async def get_sensor_data(db) -> dict:
    row = await db.prepare(
        "SELECT humidity, light, chat_id, last_notified_status FROM current_state WHERE id = 1"
    ).first()
    
    if row:
        humidity = float(row.humidity)
        light = float(row.light)
        chat_id = row.chat_id
        last_notified_status = row.last_notified_status
    else:
        humidity, light, chat_id, last_notified_status = 50.0, 100.0, None, "Ideal"

    h_status = "Ideal" if 30 <= humidity <= 70 else ("Sedienta" if humidity < 30 else "Empapada")
    l_status = "Adecuada" if 50 <= light <= 300 else ("Baja" if light < 50 else "Excesiva")

    return {
        "humidity": humidity,
        "light": light,
        "chat_id": chat_id,
        "last_notified_status": last_notified_status,
        "h_status": h_status,
        "l_status": l_status,
        "combined_status": f"{h_status}-{l_status}",
        "needs_attention": h_status in ["Sedienta", "Empapada"] or l_status in ["Baja", "Excesiva"]
    }

async def query_groq(user_input: str, sensor_data: dict, env) -> str:
    context_data = f"\n[ESTADO ACTUAL: Humedad {sensor_data['humidity']}% ({sensor_data['h_status']}), Luz {sensor_data['light']} lux ({sensor_data['l_status']})]\n"
    
    groq_url = getattr(env, "GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")
    groq_model = getattr(env, "GROQ_MODEL", "llama-3.3-70b-versatile")
    
    payload = {
        "model": groq_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{context_data}Usuario dice: {user_input}"}
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }
    
    headers = {
        "Authorization": f"Bearer {env.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        res = await fetch(groq_url, to_js({
            "method": "POST",
            "headers": headers,
            "body": json.dumps(payload)
        }))
        data = await res.json()
        return data.choices[0].message.content.strip()
    except Exception as e:
        return "Mi cerebro digital está marchito ahora mismo (Error de conexión con Groq)."

async def send_telegram_message(chat_id: int, text: str, env, parse_mode=None):
    url = f"https://api.telegram.org/bot{env.TELEGRAM_TOKEN}/sendMessage"
    body = {"chat_id": chat_id, "text": text}
    if parse_mode:
        body["parse_mode"] = parse_mode
        
    await fetch(url, to_js({
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }))

async def send_chat_action(chat_id: int, action: str, env):
    url = f"https://api.telegram.org/bot{env.TELEGRAM_TOKEN}/sendChatAction"
    await fetch(url, to_js({
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"chat_id": chat_id, "action": action})
    }))

# ==========================================
# 1. ENTRADA DE MENSAJES (WEBHOOK TELEGRAM)
# ==========================================
async def on_fetch(request, env, ctx):
    if request.method != "POST":
        return Response.new("VerdoLink Bot Worker activo.", to_js({"status": 200}))
    
    try:
        update = await request.json()
    except Exception:
        return Response.new("Bad Request", to_js({"status": 400}))

    if not hasattr(update, "message") or not hasattr(update.message, "text"):
        return Response.new("OK", to_js({"status": 200}))

    chat_id = update.message.chat.id
    user_text = update.message.text

    # Comando /estado
    if user_text.startswith("/estado"):
        sensor_data = await get_sensor_data(env.DB)
        now_str = get_local_now().strftime('%d/%m/%Y %H:%M')
        message = (
            "🌿 *Estado General*\n"
            "-------------------\n"
            f"💧 *Humedad:* {sensor_data['humidity']}% ({sensor_data['h_status']})\n"
            f"☀️ *Luz:* {sensor_data['light']} lux ({sensor_data['l_status']})\n"
            f"📅 *Fecha:* {now_str}"
        )
        await send_telegram_message(chat_id, message, env, parse_mode="Markdown")
        return Response.new("OK", to_js({"status": 200}))

    # Filtro de sueño
    if is_sleeping():
        await send_telegram_message(
            chat_id,
            "Shhh... Estoy durmiendo. Como ser vivo fotosintético, necesito mi descanso. "
            "Vuelve a molestarme después de las 08:00.",
            env
        )
        return Response.new("OK", to_js({"status": 200}))

    # Actualizar chat_id y responder con IA
    await env.DB.prepare("UPDATE current_state SET chat_id = ? WHERE id = 1").bind(chat_id).run()
    sensor_data = await get_sensor_data(env.DB)
    
    await send_chat_action(chat_id, "typing", env)
    ai_response = await query_groq(user_text, sensor_data, env)
    await send_telegram_message(chat_id, ai_response, env)

    return Response.new("OK", to_js({"status": 200}))

# ==========================================
# 2. TAREA PROGRAMADA CADA HORA (CRON)
# ==========================================
async def on_scheduled(controller, env, ctx):
    # Aplicar decaimiento (-1% humedad)
    await env.DB.prepare(
        "UPDATE current_state SET humidity = MAX(0, humidity - 1.0) WHERE id = 1"
    ).run()
    
    sensor_data = await get_sensor_data(env.DB)
    
    if sensor_data["needs_attention"]:
        # Guardar en el historial
        await env.DB.prepare(
            "INSERT INTO sensor_data (humidity, light) VALUES (?, ?)"
        ).bind(sensor_data["humidity"], sensor_data["light"]).run()
        
        if sensor_data["combined_status"] != sensor_data["last_notified_status"] and not is_sleeping():
            chat_id = sensor_data.get("chat_id")
            if chat_id:
                h_status = sensor_data["h_status"].lower()
                l_status = sensor_data["l_status"].lower()
                
                situation = "Te sientes un poco inestable físicamente."
                if h_status == "sedienta" and l_status == "baja":
                    situation = "Estás a oscuras y muriéndote de sed. Doble drama."
                elif h_status == "sedienta":
                    situation = "Tienes mucha sed, tus hojas están crujiendo."
                elif l_status == "baja":
                    situation = "Estás en penumbra, te sientes deprimida por falta de sol."
                elif h_status == "empapada" and l_status == "excesiva":
                    situation = "Estás ahogada y te estás quemando con el sol. Doble drama."
                elif h_status == "empapada":
                    situation = "Tienes demasiada agua, tus raíces se están pudriendo."
                elif l_status == "excesiva":
                    situation = "Te estás quemando con el sol, necesitas sombra."

                emergency_prompt = (
                    f"[SITUACIÓN BIOLÓGICA]: {situation} "
                    f"Datos actuales: Humedad {sensor_data['humidity']}%, Luz {sensor_data['light']} lux. "
                    "INSTRUCCIÓN: Como planta dramática, envíale una queja breve y sarcástica a tu dueño. "
                    "No menciones que eres una IA, actúa como la planta sufriendo. "
                    "¡Usa máximo 20 palabras!"
                )
                msg = await query_groq(emergency_prompt, sensor_data, env)
                await send_telegram_message(chat_id, msg, env, parse_mode="Markdown")
                
                await env.DB.prepare(
                    "UPDATE current_state SET last_notified_status = ? WHERE id = 1"
                ).bind(sensor_data["combined_status"]).run()
    else:
        if sensor_data["last_notified_status"] != "Ideal":
            await env.DB.prepare(
                "UPDATE current_state SET last_notified_status = 'Ideal' WHERE id = 1"
            ).run()