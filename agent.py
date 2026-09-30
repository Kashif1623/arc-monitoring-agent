import time
import os
import threading
import queue
import sqlite3
import requests
from flask import Flask, jsonify, request

# ==========================================
# CONFIGURATION & GLOBAL STATE (ARC MAINNET)
# ==========================================
PRIMARY_RPC_ENDPOINTS = [
    "https://arc.drpc.org",
    "https://rpc.mainnet.arc.io"
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

def send_custom_message(chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        # Added slightly longer timeout for reliable sending
        requests.post(url, json=payload, timeout=(3, 10))
    except Exception as e:
        log_msg(f"[!] Telegram Send Error: {e}")

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
    log_msg("Monitor worker started successfully (Mainnet)!")
    while True:
        for url in ACTIVE_RPC_POOL:
            log_msg(f"Fetching Mainnet RPC: {url}")
            start_time = time.time()
            block_height = 0
            try:
                payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
                # Prevent connection hang with explicit timeout
                resp = requests.post(url, json=payload, timeout=(3, 7))
                latency = int((time.time() - start_time) * 1000)
                if resp.status_code == 200:
                    data = resp.json()
                    if "result" in data:
                        block_height = int(data["result"], 16)
                        log_msg(f"🟢 [ONLINE] {url} | Block: {block_height} | Ping: {latency}ms")
                        global_node_data[url] = {"status": "ONLINE", "latency": latency, "block": block_height}
                    else:
                        global_node_data[url] = {"status": "OFFLINE", "latency": latency, "block": 0}
                else:
                    global_node_data[url] = {"status": "OFFLINE", "latency": latency, "block": 0}
            except Exception as e:
                latency = int((time.time() - start_time) * 1000)
                log_msg(f"🔴 [TIMEOUT/OFFLINE] {url}")
                global_node_data[url] = {"status": "OFFLINE", "latency": latency, "block": 0}
        time.sleep(10)

def telegram_listener():
    log_msg("Telegram listener started successfully (Mainnet)!")
    try:
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=(3, 5))
        log_msg("Webhook cleared successfully.")
    except Exception:
        pass

    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=15"
            # Reliable timeout tuple to prevent thread lock
            resp = requests.get(url, timeout=(3, 25))
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
        except Exception:
            # Silent skip on polling timeout
            time.sleep(3)
        time.sleep(1)

# 🔥 ABSOLUTE FIX: Start threads globally regardless of Gunicorn, using environment guard to prevent double-spawn
if not os.environ.get('THREADS_STARTED'):
    os.environ['THREADS_STARTED'] = '1'
    log_msg("Booting background threads directly...")
    threading.Thread(target=monitor_worker, daemon=True).start()
    threading.Thread(target=telegram_listener, daemon=True).start()

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
