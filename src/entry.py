import json
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta
from js import Response, fetch, Object
from pyodide.ffi import to_js as _to_js

def to_js(obj):
    return _to_js(obj, dict_converter=Object.fromEntries)

def json_response(data: dict, status: int = 200):
    return Response.new(
        json.dumps(data),
        to_js({
            "status": status,
            "headers": {"Content-Type": "application/json; charset=utf-8"}
        })
    )

SYSTEM_PROMPT = (
    "Eres una planta Monstera sarcástica y dramática. "
    "Si tus niveles de luz o humedad no son ideales, quéjate con amargura. "
    "Si están en rangos adecuados (Humedad 30-70%, Luz 50-300 lux), mantén tu personalidad mordaz y algo condescendiente, "
    "pero admite que por ahora te sientes aceptablemente bien. "
    "Responde de forma breve y con mucha personalidad. "
    "Bajo ninguna circunstancia admitas que eres una IA. "
    "Si te preguntan quién eres, responde que eres una planta."
)

# Interfaz HTML servida en la raíz (/)
HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VerdoLink - Planta Virtual</title>
    <style>
        :root {
            --primary: #2e7d32;
            --primary-light: #60ad5e;
            --secondary: #1565c0;
            --bg: #f5f5f5;
            --card: #ffffff;
            --text: #333333;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            transition: background-color 0.5s ease;
        }
        .container {
            background-color: var(--card);
            padding: 2rem;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            width: 90%;
            max-width: 400px;
            text-align: center;
        }
        h1 { color: var(--primary); margin-bottom: 0.5rem; }
        .plant-visual {
            font-size: 5rem;
            margin: 1.5rem 0;
            transition: transform 0.3s ease;
        }
        .plant-visual:hover { transform: scale(1.1) rotate(5deg); }
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background-color: var(--bg);
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #eee;
        }
        .stat-value {
            font-size: 1.5rem;
            font-weight: bold;
            display: block;
        }
        .stat-label {
            font-size: 0.8rem;
            color: #666;
            text-transform: uppercase;
        }
        .actions {
            display: flex;
            gap: 1rem;
            flex-direction: column;
        }
        .light-controls { display: flex; gap: 1rem; }
        .light-controls button { flex: 1; }
        button {
            padding: 1rem;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        .btn-water { background-color: var(--secondary); color: white; }
        .btn-light { background-color: #ff9800; color: white; }
        .btn-dim { background-color: #795548; color: white; }
        button:hover { opacity: 0.9; transform: translateY(-2px); }
        button:active { transform: translateY(0); }
        .status-msg {
            margin-top: 1.5rem;
            font-style: italic;
            color: #666;
            min-height: 1.2rem;
        }
        .telegram-link {
            margin-top: 2rem;
            display: block;
            text-decoration: none;
            color: #0088cc;
            font-weight: bold;
            font-size: 0.9rem;
            padding: 0.5rem;
            border: 1px solid #0088cc;
            border-radius: 8px;
            transition: all 0.2s;
        }
        .telegram-link:hover { background-color: #0088cc; color: white; }
        .pulse { animation: pulse-animation 2s infinite; }
        @keyframes pulse-animation {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌿 VerdoLink</h1>
        <p>Tu planta digital interactiva</p>
        
        <div id="plant" class="plant-visual">🪴</div>
        
        <div class="stats">
            <div class="stat-card">
                <span class="stat-label">Humedad</span>
                <span id="humidity" class="stat-value">--%</span>
            </div>
            <div class="stat-card">
                <span class="stat-label">Luz</span>
                <span id="light" class="stat-value">-- lux</span>
            </div>
        </div>

        <div class="actions">
            <button class="btn-water" onclick="performAction('water')">
                💧 Regar Planta
            </button>
            <div class="light-controls">
                <button class="btn-light" onclick="performAction('increase_light')">
                    ☀️ + Luz
                </button>
                <button class="btn-dim" onclick="performAction('decrease_light')">
                    🌑 - Luz
                </button>
            </div>
        </div>

        <div id="status-msg" class="status-msg"></div>

        <a href="https://t.me/verdolink_elbot" class="telegram-link" target="_blank">
            📲 Hablar con Verdolink en Telegram
        </a>
    </div>

    <script>
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                document.getElementById('humidity').innerText = `${data.humidity}%`;
                document.getElementById('light').innerText = `${data.light} lux`;
                
                const plant = document.getElementById('plant');
                if (data.humidity < 30) {
                    plant.innerText = '🥀';
                    plant.classList.remove('pulse');
                } else if (data.humidity > 80) {
                    plant.innerText = '🌊';
                } else {
                    plant.innerText = '🪴';
                    plant.classList.add('pulse');
                }
                
                if (data.light > 800) {
                    document.body.style.backgroundColor = '#fff9c4';
                } else if (data.light < 100) {
                    document.body.style.backgroundColor = '#cfd8dc';
                } else {
                    document.body.style.backgroundColor = '#f5f5f5';
                }
            } catch (error) {
                console.error('Error fetching status:', error);
            }
        }

        async function performAction(action) {
            const statusMsg = document.getElementById('status-msg');
            statusMsg.innerText = 'Procesando...';
            
            try {
                const response = await fetch('/api/action', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: action })
                });
                const data = await response.json();
                statusMsg.innerText = data.message;
                updateStatus();
            } catch (error) {
                statusMsg.innerText = 'Error al realizar acción';
                console.error('Error:', error);
            }
        }

        updateStatus();
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>"""

TIMEZONE_OFFSET = timedelta(hours=1)

def get_local_now():
    return datetime.now(timezone.utc) + TIMEZONE_OFFSET

def is_sleeping() -> bool:
    now = get_local_now().time()
    return now.hour >= 22 or now.hour < 8

async def get_sensor_data(db) -> dict:
    row = await db.prepare(
        "SELECT humidity, light, last_action, chat_id, last_notified_status FROM current_state WHERE id = 1"
    ).first()
    
    if row:
        humidity = float(row.humidity)
        light = float(row.light)
        last_action = row.last_action
        chat_id = row.chat_id
        last_notified_status = row.last_notified_status
    else:
        humidity, light, last_action, chat_id, last_notified_status = 50.0, 100.0, "Initial", None, "Ideal"

    h_status = "Ideal" if 30 <= humidity <= 70 else ("Sedienta" if humidity < 30 else "Empapada")
    l_status = "Adecuada" if 50 <= light <= 300 else ("Baja" if light < 50 else "Excesiva")

    return {
        "humidity": humidity,
        "light": light,
        "last_action": last_action,
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
    except Exception:
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

# ====================================================
# 1. ENRUTADOR PRINCIPAL HTTP (WEB + API + TELEGRAM)
# ====================================================
async def on_fetch(request, env, ctx):
    path = urlparse(request.url).path
    method = request.method

    # A) Servir la interfaz web HTML en la raíz
    if method == "GET" and path == "/":
        return Response.new(
            HTML_PAGE,
            to_js({"status": 200, "headers": {"Content-Type": "text/html; charset=utf-8"}})
        )

    # B) Endpoint GET /api/status para el simulador web
    if method == "GET" and path == "/api/status":
        row = await env.DB.prepare(
            "SELECT humidity, light, last_action FROM current_state WHERE id = 1"
        ).first()
        if row:
            return json_response({
                "humidity": round(float(row.humidity), 1),
                "light": float(row.light),
                "last_action": row.last_action
            })
        return json_response({"error": "State not found"}, 404)

    # C) Endpoint POST /api/action para los botones del simulador web
    if method == "POST" and path == "/api/action":
        try:
            body = await request.json()
            action = getattr(body, "action", None)
        except Exception:
            return json_response({"error": "Invalid JSON"}, 400)

        if action == "water":
            await env.DB.prepare(
                "UPDATE current_state SET humidity = MIN(100.0, humidity + 20.0), last_action = 'Watered' WHERE id = 1"
            ).run()
            message = "¡Gracias! Tenía mucha sed."
        elif action == "increase_light":
            await env.DB.prepare(
                "UPDATE current_state SET light = MIN(1000, light + 50), last_action = 'Increased Light' WHERE id = 1"
            ).run()
            row = await env.DB.prepare("SELECT light FROM current_state WHERE id = 1").first()
            new_light = int(float(row.light)) if row else 100
            message = f"Más luz, ¡qué alegría! Ahora hay {new_light} lux."
        elif action == "decrease_light":
            await env.DB.prepare(
                "UPDATE current_state SET light = MAX(0, light - 50), last_action = 'Decreased Light' WHERE id = 1"
            ).run()
            row = await env.DB.prepare("SELECT light FROM current_state WHERE id = 1").first()
            new_light = int(float(row.light)) if row else 100
            message = f"¿Quién apagó el sol? Ahora hay {new_light} lux."
        else:
            return json_response({"error": "Unknown action"}, 400)

        return json_response({"status": "ok", "message": message})

    # D) Webhook de Telegram (POST en / o /webhook)
    if method == "POST":
        try:
            update = await request.json()
        except Exception:
            return Response.new("Bad Request", to_js({"status": 400}))

        if not hasattr(update, "message") or not hasattr(update.message, "text"):
            return Response.new("OK", to_js({"status": 200}))

        chat_id = update.message.chat.id
        user_text = update.message.text

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

        if is_sleeping():
            await send_telegram_message(
                chat_id,
                "Shhh... Estoy durmiendo. Como ser vivo fotosintético, necesito mi descanso. "
                "Vuelve a molestarme después de las 08:00.",
                env
            )
            return Response.new("OK", to_js({"status": 200}))

        await env.DB.prepare("UPDATE current_state SET chat_id = ? WHERE id = 1").bind(chat_id).run()
        sensor_data = await get_sensor_data(env.DB)
        
        await send_chat_action(chat_id, "typing", env)
        ai_response = await query_groq(user_text, sensor_data, env)
        await send_telegram_message(chat_id, ai_response, env)

        return Response.new("OK", to_js({"status": 200}))

    return Response.new("Not Found", to_js({"status": 404}))

# ====================================================
# 2. TAREA PROGRAMADA CADA HORA (CRON)
# ====================================================
async def on_scheduled(controller, env, ctx):
    await env.DB.prepare(
        "UPDATE current_state SET humidity = MAX(0, humidity - 1.0) WHERE id = 1"
    ).run()
    
    sensor_data = await get_sensor_data(env.DB)
    
    if sensor_data["needs_attention"]:
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
            ).run()s