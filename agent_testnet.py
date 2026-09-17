import asyncio
import time
import logging
import aiohttp
import os

# Ultra-Clean Enterprise Logging Setup (Strict International Output Only)
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s | %(levelname)s | %(message)s'
)

# 🌐 VERIFIED FUNCTIONAL PRODUCTION JSON-RPC PATHS FOR ARC TESTNET
PRIMARY_RPC_ENDPOINTS = [
    "https://arc-testnet.drpc.org",          # Official dRPC Public Testnet Route
    "https://rpc.testnet.arc.network"        # Core Foundation Testnet Node Gateway
]

# 🔄 DYNAMIC STATE FAILOVER BACKUP ROUTE (TESTNET OVERVIEW)
FALLBACK_RPC_ENDPOINTS = [
    "https://testnet.arc.network"
]

LOG_STORAGE_FILE = "agent_history_logs.txt"
MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB Auto-Rotation Constraint

ACTIVE_RPC_POOL = list(PRIMARY_RPC_ENDPOINTS)
rpc_status = {url: {"failures": 0, "circuit_broken_until": 0} for url in (PRIMARY_RPC_ENDPOINTS + FALLBACK_RPC_ENDPOINTS)}

# Global Operational SLA Parameters
FAILURE_THRESHOLD = 3
COOLDOWN_SECONDS = 20
MAX_DRIFT_THRESHOLD = 8
SUPER_PATIENT_TIMEOUT = 6   # Optimized to prevent mobile background loops from hanging
GAS_ALERT_THRESHOLD_GWEI = 150

TOTAL_RUN_TIME_LIMIT = 900  # Safe execution bounds (15 Minutes runtime limits)
START_TIMESTAMP = time.time()

def write_persistent_log(message):
    try:
        if os.path.exists(LOG_STORAGE_FILE) and os.path.getsize(LOG_STORAGE_FILE) > MAX_LOG_SIZE_BYTES:
            with open(LOG_STORAGE_FILE, mode="w", encoding="utf-8") as file:
                file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- Log rotated systematically ---\n")
        with open(LOG_STORAGE_FILE, mode="a", encoding="utf-8") as file:
            file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except Exception:
        pass  

def print_clean_header():
    print("=" * 90)
    print("⚡ ARC TESTNET GLOBAL NETWORK MONITORING AGENT v2.0")
    print("🔒 STATUS: ENTERPRISE LIVE MONITORING ENGAGED (WORLDWIDE CLEAN INTERFACE)")
    print("=" * 90 + "\n")

async def send_discord_alert(session, alert_title, details):
    DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"
    if DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE": 
        return
    payload = {
        "username": "Arc Testnet Auto-Agent",
        "content": f"🚨 **[{alert_title}]**\n{details}\n⏰ **Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}"
    }
    try:
        await session.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception:
        pass

async def fetch_json(session, url, payload):
    try:
        async with session.post(url, json=payload, timeout=SUPER_PATIENT_TIMEOUT) as response:
            if response.status == 200:
                return await response.json()
    except Exception:
        pass
    return None

async def check_rpc_with_circuit_breaker(session, url):
    current_time = time.time()
    if current_time < rpc_status[url]["circuit_broken_until"]: 
        return None

    block_payload = {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": ["latest", False], "id": 1}
    gas_payload = {"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 2}
    
    # ⚡ Parallel Socket Non-Blocking Core Engine
    res_block, res_gas = await asyncio.gather(
        fetch_json(session, url, block_payload),
        fetch_json(session, url, gas_payload),
        return_exceptions=True
    )
    
    if res_block and res_gas and not isinstance(res_block, Exception) and not isinstance(res_gas, Exception):
        block_data = res_block.get("result")
        gas_hex = res_gas.get("result")
        
        if block_data and "number" in block_data and "hash" in block_data and gas_hex:
            rpc_status[url]["failures"] = 0  
            gas_gwei = round(int(gas_hex, 16) / 10**9, 2)
            return {"url": url, "height": int(block_data["number"], 16), "hash": block_data["hash"], "gas_testnet": gas_gwei}

    # Silent Failover Circuit Routing (Zero Terminal Print Trash)
    rpc_status[url]["failures"] += 1
    if rpc_status[url]["failures"] >= FAILURE_THRESHOLD:
        rpc_status[url]["circuit_broken_until"] = current_time + COOLDOWN_SECONDS
        write_persistent_log(f"Testnet Node isolated silently: {url}")
        await send_discord_alert(session, "NODE_CRASH_ALERT", f"🔴 Testnet Node Down: {url}")
    return None

async def monitor_network():
    global ACTIVE_RPC_POOL
    print_clean_header()
    write_persistent_log("Testnet monitoring engine successfully initialized.")
    
    connector = aiohttp.TCPConnector(limit_per_host=10, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            elapsed_time = time.time() - START_TIMESTAMP
            if elapsed_time >= TOTAL_RUN_TIME_LIMIT:
                logging.info("⏱️ Time limit reached. Shutting down event loop context safely.")
                break 

            try:
                tasks = [check_rpc_with_circuit_breaker(session, url) for url in ACTIVE_RPC_POOL]
                results = await asyncio.gather(*tasks)
                latest_data = {res["url"]: res for res in results if res is not None}
                
                if not latest_data:
                    write_persistent_log("All Testnet nodes offline. Failing over to disaster recovery array.")
                    ACTIVE_RPC_POOL = list(PRIMARY_RPC_ENDPOINTS + FALLBACK_RPC_ENDPOINTS)
                    await asyncio.sleep(10)
                    continue
                
                if len(latest_data) >= 2:
                    max_height = max([info["height"] for info in latest_data.values()])
                    
                    for url, info in latest_data.items():
                        node_drift = max_height - info["height"]
                        if node_drift >= MAX_DRIFT_THRESHOLD:
                            write_persistent_log(f"Testnet drift detected on {url}: Behind by {node_drift} blocks")
                            await send_discord_alert(session, "NODE_DRIFT_ALERT", f"Lagging: {url}")

                    seen_hashes = {}
                    for url, info in latest_data.items():
                        seen_hashes.setdefault(info["height"], []).append(info["hash"])
                    
                    for h, hashes in seen_hashes.items():
                        if len(hashes) >= 2 and len(set(hashes)) > 1:
                            await send_discord_alert(session, "CHAIN_FORK_ALERT", f"Testnet Fork at Block {h}!")

                # Strict Dashboard Outputs: Clean verified online state telemetry only
                for url, data in latest_data.items():
                    logging.info(f"🟩 [ONLINE] {url} | Block: {data['height']} | Gas: {data['gas_testnet']} Gwei")
                    if data['gas_testnet'] > GAS_ALERT_THRESHOLD_GWEI:
                        logging.warning(f"💵 [GAS SPIKE] Anomaly detected on Testnet: {data['gas_testnet']} Gwei")

                time_left_mins = int((TOTAL_RUN_TIME_LIMIT - elapsed_time) / 60)
                print(f"🔄 Execution State Active | Context Remaining: {time_left_mins} Mins")
                print("-" * 90) # Standard Clean Separation Line
                await asyncio.sleep(10) 
                
            except Exception as loop_error:
                write_persistent_log(f"Testnet monitoring kernel loop failure: {str(loop_error)}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    try: 
        asyncio.run(monitor_network())
    except KeyboardInterrupt: 
        print("\n🛑 Testnet tracking context detached cleanly by user command.")
