# VerdoLink Bot 🌿🤖

**VerdoLink** is a serverless IoT companion and interactive Telegram bot powered by Cloudflare Workers (Python runtime), Cloudflare D1, and the Groq LLM API. It brings your Monstera houseplant to life with a witty, dramatic, and sarcastic personality.

The bot monitors soil humidity and light levels, simulates hourly moisture decay, chats with you in character, and proactively sends emergency alerts when it needs watering or better lighting.

---

## 🌟 Features

- **🎭 Sarcastic Monstera Persona:** Powered by Groq LLM (e.g., `llama-3.3-70b-versatile` or `openai/gpt-oss-20b`), responding as a dramatic, moody houseplant that will never admit to being an AI.
- **📊 Real-Time Status Checks:** `/estado` command reports current moisture and light readings along with plant health diagnoses.
- **🌙 Circadian / Sleep Cycle:** Between 22:00 (10:00 PM) and 08:00 (8:00 AM) local time, the plant is "sleeping" and asks not to be disturbed.
- **⏰ Hourly Cron & Health Simulation:**
  - Automatically simulates 1% hourly moisture evaporation.
  - Evaluates health thresholds (thirsty, overwatered, low light, or scorched).
  - Sends proactive, biting distress messages via Telegram if conditions deteriorate.
  - Automatically logs readings into a history table.
- **⚡ Serverless Edge Architecture:** Runs natively on Cloudflare's Python Worker platform with Pyodide and Cloudflare D1 SQL database.

---

## 🏗️ Project Structure

```text
verdolink_cf/
├── src/
│   └── entry.py        # Worker entrypoint (on_fetch, on_scheduled, Telegram & Groq integrations)
├── schema.sql          # Cloudflare D1 database schema and initial data
├── wrangler.toml       # Cloudflare Workers configuration (triggers, bindings, vars)
├── .env                # Local environment template (TELEGRAM_TOKEN, GROQ_API_KEY, etc.)
└── .gitignore          # Git ignore rules
```

---

## 📐 Plant Condition Thresholds

| Metric | Ideal Range | Sub-optimal / Critical Conditions |
| :--- | :--- | :--- |
| **Humidity** | `30% - 70%` (Ideal) | `< 30%`: Sedienta (Thirsty)<br>`> 70%`: Empapada (Waterlogged) |
| **Light** | `50 - 300 lux` (Adecuada) | `< 50 lux`: Baja (Low)<br>`> 300 lux`: Excesiva (Scorching) |

---

## 🛠️ Prerequisites

- [Node.js](https://nodejs.org/) (v18+)
- [Cloudflare Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/)
- A **Cloudflare** account
- A **Telegram Bot Token** (obtained from [@BotFather](https://t.me/botfather))
- A **Groq Cloud API Key** (from [Groq Console](https://console.groq.com/))

---

## 🚀 Setup & Installation

### 1. Clone & Navigate to Project

```bash
git clone <repository-url>
cd verdolink_cf
```

### 2. Configure Cloudflare D1 Database

1. Create a D1 database using Wrangler:
   ```bash
   npx wrangler d1 create verdolink-db
   ```
2. Copy the resulting `database_id` into [`wrangler.toml`](file:///mnt/projects/verdolink_cf/wrangler.toml):
   ```toml
   [[d1_databases]]
   binding = "DB"
   database_name = "verdolink-db"
   database_id = "<YOUR_DATABASE_ID>"
   ```

3. Initialize the database schema:
   ```bash
   # For local development
   npx wrangler d1 execute verdolink-db --local --file=./schema.sql

   # For production (remote D1)
   npx wrangler d1 execute verdolink-db --remote --file=./schema.sql
   ```

### 3. Set Up Secrets & Environment Variables

#### For Local Development:
Create a `.dev.vars` file in the root directory (ignored by git):

```env
TELEGRAM_TOKEN="your_telegram_bot_token"
GROQ_API_KEY="your_groq_api_key"
GROQ_MODEL="llama-3.3-70b-versatile"
GROQ_URL="https://api.groq.com/openai/v1/chat/completions"
```

#### For Production (Cloudflare Secrets):
Store sensitive keys securely using Wrangler:

```bash
npx wrangler secret put TELEGRAM_TOKEN
npx wrangler secret put GROQ_API_KEY
```

Non-sensitive variables (such as `GROQ_MODEL` and `GROQ_URL`) can be customized in [`wrangler.toml`](file:///mnt/projects/verdolink_cf/wrangler.toml) under `[vars]`.

---

## 💻 Local Development

Run the Worker locally with:

```bash
npx wrangler dev
```

> **Note:** To test Telegram updates locally, you can send simulated `POST` requests to `http://localhost:8787` with Telegram Update JSON payloads, or expose your local server using a tunneling service such as Cloudflare Tunnel (`cloudflared`).

---

## 🚢 Deployment

### 1. Deploy Worker

Deploy to your Cloudflare account:

```bash
npx wrangler deploy
```

Once deployed, Cloudflare will output your Worker URL (e.g., `https://verdolink-bot.<your-subdomain>.workers.dev`).

### 2. Configure Telegram Webhook

Point your Telegram bot to the deployed worker URL:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://verdolink-bot.<your-subdomain>.workers.dev"}'
```

To verify webhook status:

```bash
curl "https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/getWebhookInfo"
```

---

## 🤖 Usage & Bot Interaction

- **/estado**: Retrieves live status from the database, displaying humidity, light level, and status ratings formatted in Markdown.
- **Conversational Chat**: Any plain message sent to the bot will receive a response from the plant persona (unless between 22:00 and 08:00, when it will politely—or impolitely—refuse to talk).
- **Proactive Cron Notifications**: Every hour, the worker evaluates plant health. If the plant transitions into a critical state, it automatically alerts the owner on Telegram.

---

## ⚙️ Customization

- **Timezone:** Modify `TIMEZONE_OFFSET` in [`src/entry.py`](file:///mnt/projects/verdolink_cf/src/entry.py#L19-L20) to match your local timezone offset (default is `UTC+1`).
- **Sleep Schedule:** Adjust `is_sleeping()` in [`src/entry.py`](file:///mnt/projects/verdolink_cf/src/entry.py#L25-L27) to change resting hours (default: 22:00 - 08:00).
- **Persona & Prompt:** Edit `SYSTEM_PROMPT` in [`src/entry.py`](file:///mnt/projects/verdolink_cf/src/entry.py#L9-L17) to alter the bot's humor or plant species.
- **Cron Schedule:** Edit `[triggers]` in [`wrangler.toml`](file:///mnt/projects/verdolink_cf/wrangler.toml#L7-L8) to change execution frequency (default: `0 * * * *`, every hour).

---

## 📄 License

This project is open-source. Feel free to modify and adapt it for your own plants!
