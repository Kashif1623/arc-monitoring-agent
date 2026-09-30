import asyncio
import time
import os
import threading
import queue
import sqlite3
import requests
from flask import Flask, Response, jsonify, request

# ==========================================
# CONFIGURATION & GLOBAL STATE (MAINNET)
# ==========================================
PRIMARY_RPC_ENDPOINTS = [
    "https://rpc.ankr.com/eth", # Safe fallback or use valid mainnet endpoints if available, keeping robust
    "https://eth.llamarpc.com"
]

DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"
TELEGRAM_BOT_TOKEN = "8886231393:AAHi9AWl1N07VAP90Tm5_C8DmUqguuc0fLE"
TELEGRAM_CHAT_ID = "8822300532"

FAILURE_THRESHOLD = 3
SUPER_PATIENT_TIMEOUT = 5

DB_FILE = "arc_mainnet_sla.db"
ACTIVE_RPC_POOL = list(PRIMARY_RPC_ENDPOINTS)
global_node_data = {}

app = Flask(__name__)
log_queue = queue.Queue(maxsize=200)

def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS uptime_logs
                     (timestamp TEXT, node_url TEXT, status TEXT, latency_ms INTEGER, block_height INTEGER)''')
        conn.commit()
        conn.close()
    except Exception:
        pass

init_db()

def log_msg(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"{timestamp} | {message}"
    print(formatted)
    try:
        if log_queue.full():
            log_queue.get_nowait()
        log_queue.put_nowait(formatted)
    except Exception:
        pass

def send_custom_message(chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        log_msg(f"[!] Telegram Error: {e}")

def get_status_report():
    report = "⚡ *ARC Mainnet Node Status Report*\n\n"
    for url, data in global_node_data.items():
        status = data.get("status", "UNKNOWN")
        block = data.get("block", 0)
        latency = data.get("latency", 0)
        emoji = "🟢" if status == "ONLINE" else "🔴"
        report += f"{emoji} `{url}`\n   • Status: *{status}*\n   • Block: `{block}`\n   • Latency: `{latency}ms`\n\n"
    if not global_node_data:
        report += "Initializing nodes data, please wait..."
    return report

def monitor_worker():
    log_msg("Mainnet Sentinel Core initialized successfully.")
    while True:
        for url in ACTIVE_RPC_POOL:
            start_time = time.time()
            block_height = 0
            try:
                payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
                resp = requests.post(url, json=payload, timeout=SUPER_PATIENT_TIMEOUT)
                latency = int((time.time() - start_time) * 1000)
                if resp.status_code == 200:
                    data = resp.json()
                    if "result" in data:
                        block_height = int(data["result"], 16)
                        log_msg(f"🟢 [ONLINE] {url} | Block: {block_height} | Ping: {latency}ms")
                        global_node_data[url] = {"status": "ONLINE", "latency": latency, "block": block_height}
                    else:
                        raise ValueError("Invalid JSON-RPC")
                else:
                    raise Exception(f"HTTP {resp.status_code}")
            except Exception as e:
                latency = int((time.time() - start_time) * 1000)
                log_msg(f"🔴 [OFFLINE] {url} | Error: {e}")
                global_node_data[url] = {"status": "OFFLINE", "latency": latency, "block": 0}
        time.sleep(15)

def telegram_listener():
    log_msg("Starting Telegram listener thread...")
    try:
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=5)
        log_msg("Webhook cleared.")
    except Exception as e:
        log_msg(f"[!] Webhook clear warning: {e}")

    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=20"
            resp = requests.get(url, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    message = result.get("message", {})
                    text = message.get("text", "").strip()
                    chat_id = message.get("chat", {}).get("id")
                    
                    if chat_id and text:
                        log_msg(f"[TG] Command received: {text}")
                        if text.startswith("/start") or text.lower() == "start":
                            reply = "⚡ *ARC Mainnet Monitoring Sentinel is Online!*\n\nSend /status to check node statuses."
                            send_custom_message(chat_id, reply)
                        elif text.startswith("/status"):
                            reply = get_status_report()
                            send_custom_message(chat_id, reply)
        except Exception as e:
            time.sleep(3)
        time.sleep(1)

threading.Thread(target=monitor_worker, daemon=True).start()
threading.Thread(target=telegram_listener, daemon=True).start()

@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ARC Mainnet Sentinel</title>
        <style>
            body { background-color: #0d0d0d; color: #00ff66; font-family: monospace; padding: 20px; }
            h2 { color: #ffcc00; border-bottom: 1px dashed #ffcc00; padding-bottom: 10px; }
            pre { white-space: pre-wrap; word-wrap: break-word; font-size: 14px; line-height: 1.5; }
        </style>
    </head>
    <body>
        <h2>⚡ ARC MAINNET SENTINEL INFRASTRUCTURE</h2>
        <pre id="logs">Booting modules...</pre>
        <script>
            const evtSource = new EventSource("/stream");
            evtSource.onmessage = function(event) {
                const logPre = document.getElementById("logs");
                logPre.textContent += "\\n" + event.data;
                window.scrollTo(0, document.getElementById("logs").scrollHeight);
            };
        </script>
    </body>
    </html>
    """
    return html

@app.route("/stream")
def stream():
    def generate():
        while True:
            try:
                msg = log_queue.get(timeout=10)
                yield f"data: {msg}\\n\\n"
            except queue.Empty:
                yield "data: [ heartbeat ]\\n\\n"
    return Response(generate(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
