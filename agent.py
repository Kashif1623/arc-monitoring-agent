import time
import os
import threading
import queue
import sqlite3
import requests
from flask import Flask, jsonify, request

# ==========================================
# CONFIGURATION & GLOBAL STATE (MAINNET)
# ==========================================
PRIMARY_RPC_ENDPOINTS = [
    "https://rpc.ankr.com/eth",
    "https://eth.llamarpc.com"
]

TELEGRAM_BOT_TOKEN = "8996901688:AAHEpEeYGzcMDqMkLBcBwUSou6-ojjoKkgY"
DB_FILE = "arc_mainnet_sla.db"
ACTIVE_RPC_POOL = list(PRIMARY_RPC_ENDPOINTS)
global_node_data = {}

app = Flask(__name__)
logs_list = []
logs_lock = threading.Lock()

def log_msg(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"{timestamp} | {message}"
    print(formatted)
    with logs_lock:
        logs_list.append(formatted)
        if len(logs_list) > 100:
            logs_list.pop(0)

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
log_msg("Mainnet Sentinel Core initialized successfully.")

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
    while True:
        for url in ACTIVE_RPC_POOL:
            start_time = time.time()
            block_height = 0
            try:
                payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
                resp = requests.post(url, json=payload, timeout=5)
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
            time.sleep(5)
        time.sleep(1)

# Ensure background threads run only once across multiple Gunicorn workers
LOCK_DIR = "sentinel_worker_lock"
try:
    os.mkdir(LOCK_DIR)
    threading.Thread(target=monitor_worker, daemon=True).start()
    threading.Thread(target=telegram_listener, daemon=True).start()
    log_msg("Primary worker spawned background threads.")
except OSError:
    log_msg("Background threads already active in another worker.")

@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ARC Mainnet Sentinel</title>
        <style>
            body { background-color: #0d0d0d; color: #00ff66; font-family: monospace; padding: 20px; }
            h2 { color: #ffcc00; border-bottom: 1px dashed #ffcc00; padding-bottom: 10px; }
            pre { white-space: pre-wrap; word-wrap: break-word; font-size: 14px; line-height: 1.5; background: #111; padding: 15px; border-radius: 5px; }
            .node-box { background: #161616; padding: 10px; margin-bottom: 10px; border-left: 4px solid #00ff66; }
        </style>
    </head>
    <body>
        <h2>⚡ ARC MAINNET SENTINEL INFRASTRUCTURE</h2>
        <div id="status">Loading node statuses...</div>
        <h3>Live Activity Logs:</h3>
        <pre id="logs">Loading logs...</pre>
        <script>
            function fetchData() {
                fetch('/api/data')
                    .then(res => res.json())
                    .then(data => {
                        let statusHtml = "<h4>Node Statuses:</h4>";
                        if (Object.keys(data.nodes).length === 0) {
                            statusHtml += "<p>Initializing nodes connection...</p>";
                        } else {
                            for (let [url, info] of Object.entries(data.nodes)) {
                                let color = info.status === 'ONLINE' ? '#00ff66' : '#ff3333';
                                statusHtml += `<div class="node-box" style="border-left-color: ${color}">` +
                                              `${info.status === 'ONLINE' ? '🟢' : '🔴'} <b>${url}</b><br>` +
                                              `• Status: <b>${info.status}</b> | Block: <code>${info.block}</code> | Latency: <code>${info.latency}ms</code>` +
                                              `</div>`;
                            }
                        }
                        document.getElementById('status').innerHTML = statusHtml;
                        document.getElementById('logs').textContent = data.logs.join('\\n');
                    })
                    .catch(err => console.log(err));
            }
            fetchData();
            setInterval(fetchData, 4000);
        </script>
    </body>
    </html>
    """

@app.route("/api/data")
def api_data():
    with logs_lock:
        current_logs = list(logs_list)
    return jsonify({
        "nodes": global_node_data,
        "logs": current_logs
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
