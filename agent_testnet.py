import asyncio
import time
import logging
import aiohttp
import sys
import os

# Standard Professional Logging Setup
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 🌐 FIXED: HIGH-PERFORMANCE VERIFIED TESTNET JSON-RPC ENDPOINTS ONLY
PRIMARY_RPC_ENDPOINTS = [
    "https://arc-testnet.drpc.org",          # Node 1: Official Free Public Testnet Gateway
    "https://drpc.org" # Node 2: Load-Balanced Network Testnet Channel Route
]

# 🔄 DYNAMIC STATE FAILOVER ROUTE
FALLBACK_RPC_ENDPOINTS = [
    "https://testnet.arc.network"
]

LOG_STORAGE_FILE = "agent_history_logs.txt"
MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB Auto-Rotation Limit for Local Storage

ACTIVE_RPC_POOL = list(PRIMARY_RPC_ENDPOINTS)
rpc_status = {url: {"failures": 0, "circuit_broken_until": 0} for url in (PRIMARY_RPC_ENDPOINTS + FALLBACK_RPC_ENDPOINTS)}

FAILURE_THRESHOLD = 4
COOLDOWN_SECONDS = 20
MAX_DRIFT_THRESHOLD = 8
SUPER_PATIENT_TIMEOUT = 12
GAS_ALERT_THRESHOLD_GWEI = 150

TOTAL_RUN_TIME_LIMIT = 900  
START_TIMESTAMP = time.time()

def write_persistent_log(message):
    try:
        if os.path.exists(LOG_STORAGE_FILE) and os.path.getsize(LOG_STORAGE_FILE) > MAX_LOG_SIZE_BYTES:
            with open(LOG_STORAGE_FILE, mode="w", encoding="utf-8") as file:
                file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- Log rotated to save local storage ---\n")
        clean_line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n"
        with open(LOG_STORAGE_FILE, mode="a", encoding="utf-8") as file:
            file.write(clean_line)
    except Exception:
        pass  

def print_embedded_deployment_guides():
    print("=" * 85)
    print("📱 TERMUX RUNNER BACKGROUND STATE SEQUENCE:")
    print(f"  --> termux-wake-lock && nohup python agent.py >> {LOG_STORAGE_FILE} 2>&1 &")
    print("=" * 85 + "\n")

async def send_discord_alert(session, alert_title, details):
    DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"
    if DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE": return
    payload = {
        "username": "Arc Testnet Auto-Agent",
        "content": f"🚨 **[{alert_title}]**\n{details}\n⏰ **Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}"
    }
    try:
        await session.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception:
        pass

async def check_rpc_with_circuit_breaker(session, url):
    current_time = time.time()
    if current_time < rpc_status[url]["circuit_broken_until"]: 
        return None
    try:
        b_payload = {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": ["latest", False], "id": 1}
        g_payload = {"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 2}
        async with session.post(url, json=b_payload, timeout=SUPER_PATIENT_TIMEOUT) as rb, session.post(url, json=g_payload, timeout=SUPER_PATIENT_TIMEOUT) as rg:
            if rb.status == 200 and rg.status == 200:
                res_b, res_g = await rb.json(), await rg.json()
                block_data = res_b.get("result")
                gas_hex = res_g.get("result")
                if block_data and "number" in block_data and gas_hex:
                    rpc_status[url]["failures"] = 0  
                    return {"url": url, "height": int(block_data["number"], 16), "hash": block_data["hash"], "gas_testnet": round(int(gas_hex, 16) / 10**9, 2)}
    except Exception: 
        pass
    rpc_status[url]["failures"] += 1
    if rpc_status[url]["failures"] >= FAILURE_THRESHOLD:
        rpc_status[url]["circuit_broken_until"] = current_time + COOLDOWN_SECONDS
        await send_discord_alert(session, "NODE_CRASH_ALERT", f"🔴 Node Down: {url}")
    return None

async def monitor_network():
    global ACTIVE_RPC_POOL
    print_embedded_deployment_guides()
    connector = aiohttp.TCPConnector(limit_per_host=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            elapsed_time = time.time() - START_TIMESTAMP
            if elapsed_time >= TOTAL_RUN_TIME_LIMIT:
                logging.info("⏱️ Time limit reached. Shutting down event loop context safely.")
                break # Replaced fatal sys.exit(0) call with clean context break logic
            try:
                tasks = [check_rpc_with_circuit_breaker(session, url) for url in ACTIVE_RPC_POOL]
                results = await asyncio.gather(*tasks)
                latest_data = {res["url"]: res for res in results if res is not None}
                
                if not latest_data:
                    ACTIVE_RPC_POOL = list(PRIMARY_RPC_ENDPOINTS + FALLBACK_RPC_ENDPOINTS)
                    await asyncio.sleep(10)
                    continue
                
                for url, data in latest_data.items():
                    log_line = f"✅ {url} | Block: {data['height']} | Gas: {data['gas_testnet']} Gwei"
                    logging.info(log_line)
                    write_persistent_log(log_line)
                
                if len(latest_data) >= 2:
                    heights = [info["height"] for info in latest_data.values()]
                    max_height = max(heights)
                    
                    for url, info in latest_data.items():
                        node_drift = max_height - info["height"]
                        if node_drift >= MAX_DRIFT_THRESHOLD:
                            logging.warning(f"⚠️ Drift on {url}: Behind by {node_drift} blocks")
                            await send_discord_alert(session, "NODE_DRIFT_ALERT", f"Lagging: {url}")

                    seen_hashes = {}
                    for url, info in latest_data.items():
                        h = info["height"]
                        if h not in seen_hashes: seen_hashes[h] = []
                        seen_hashes[h].append((url, info["hash"]))
                    
                    for h, nodes in seen_hashes.items():
                        if len(nodes) >= 2 and len({b_hash for url, b_hash in nodes}) > 1:
                            await send_discord_alert(session, "CHAIN_FORK_ALERT", f"Fork at Block {h}!")

                print(f"🔄 Active | Time Remaining: {int((TOTAL_RUN_TIME_LIMIT - elapsed_time) / 60)} Mins")
                await asyncio.sleep(10) 
            except Exception:
                await asyncio.sleep(5)

if __name__ == "__main__":
    try: 
        asyncio.run(monitor_network())
    except KeyboardInterrupt: 
        print("\nStopped.")
