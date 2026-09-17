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

# 🌐 GLOBAL DECENTRALIZED ARC MAINNET MULTI-NODE INFRASTRUCTURE
PRIMARY_RPC_ENDPOINTS = [
    "https://drpc.live", # Your Premium Private Endpoint
    "https://arc-rpc.publicnode.com",                                       # Global PublicNode Infrastructure Route
    "https://rpc.blockdaemon.mainnet.arc.io",                               # Dedicated Blockdaemon Enterprise Node
    "https://rpc.mainnet.arc.io"                                            # Core Arc Mainnet Infrastructure Gateway
]

# 🔄 AUTOMATED DISASTER RECOVERY CHANNELS (WORLDWIDE FAILOVER)
FALLBACK_RPC_ENDPOINTS = [
    "https://rpc.drpc.mainnet.arc.io"
]

LOG_STORAGE_FILE = "mainnet_agent_history_logs.txt"
MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024  # 5MB Dynamic rotation constraint

ACTIVE_RPC_POOL = list(PRIMARY_RPC_ENDPOINTS)
rpc_status = {url: {"failures": 0, "circuit_broken_until": 0} for url in (PRIMARY_RPC_ENDPOINTS + FALLBACK_RPC_ENDPOINTS)}

# Global Operational SLA Parameters
FAILURE_THRESHOLD = 2       
COOLDOWN_SECONDS = 30       
MAX_DRIFT_THRESHOLD = 3     
SUPER_PATIENT_TIMEOUT = 5   # Tight timeout bounds to prevent loop blocking
GAS_ALERT_THRESHOLD_GWEI = 35.0  

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
    print("⚡ ARC MAINNET GLOBAL NETWORK MONITORING AGENT v2.0")
    print("🔒 STATUS: ENTERPRISE LIVE MONITORING ENGAGED (WORLDWIDE CLEAN INTERFACE)")
    print("=" * 90 + "\n")

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
            gas_gwei = round(int(gas_hex, 16) / 10**9, 6) 
            return {"url": url, "height": int(block_data["number"], 16), "hash": block_data["hash"], "gas": gas_gwei}

    # Internal failover tracker (Silent - No print statements to ensure clean interface)
    rpc_status[url]["failures"] += 1
    if rpc_status[url]["failures"] >= FAILURE_THRESHOLD:
        rpc_status[url]["circuit_broken_until"] = current_time + COOLDOWN_SECONDS
        write_persistent_log(f"Node isolated silently: {url}")
    return None

async def monitor_network():
    global ACTIVE_RPC_POOL
    print_clean_header()
    write_persistent_log("System core initialization sequence completed successfully.")
    
    connector = aiohttp.TCPConnector(limit_per_host=10, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            try:
                tasks = [check_rpc_with_circuit_breaker(session, url) for url in ACTIVE_RPC_POOL]
                results = await asyncio.gather(*tasks)
                latest_data = {res["url"]: res for res in results if res is not None}
                
                if not latest_data:
                    write_persistent_log("Disaster recovery protocol triggered: All nodes offline.")
                    ACTIVE_RPC_POOL = list(PRIMARY_RPC_ENDPOINTS + FALLBACK_RPC_ENDPOINTS)
                    await asyncio.sleep(4)
                    continue
                
                if len(latest_data) >= 2:
                    max_height = max([info["height"] for info in latest_data.values()])
                    
                    for url, info in latest_data.items():
                        node_drift = max_height - info["height"]
                        if node_drift >= MAX_DRIFT_THRESHOLD:
                            write_persistent_log(f"Desync on {url}: Lagging {node_drift} blocks.")

                    seen_hashes = {}
                    for url, info in latest_data.items():
                        seen_hashes.setdefault(info["height"], []).append(info["hash"])
                    
                    for h, hashes in seen_hashes.items():
                        if len(hashes) >= 2 and len(set(hashes)) > 1:
                            logging.critical(f"🔥 [CHAIN SPLIT] State divergence detected at Block {h}!")

                # Strict filtering: Displays ONLY operational verified online nodes
                for url, data in latest_data.items():
                    logging.info(f"🟩 [ONLINE] {url} | Block: {data['height']} | Gas: {data['gas']} Gwei")
                    if data['gas'] > GAS_ALERT_THRESHOLD_GWEI:
                        logging.warning(f"💵 [GAS SPIKE] Rate anomaly detected: {data['gas']} Gwei")

                print("-" * 90) # Standard Clean Separation Line
                await asyncio.sleep(10) 
                
            except Exception as loop_error:
                write_persistent_log(f"Core runtime kernel exception: {str(loop_error)}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_network())
    except KeyboardInterrupt:
        print("\n🛑 System termination signal intercepted. Detaching cleanly.")
