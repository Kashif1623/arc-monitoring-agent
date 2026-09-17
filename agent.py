import asyncio
import time
import logging
import aiohttp
import os
import sys

# Standard Professional Logging Setup
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 🌐 PRIMARY HIGH-PERFORMANCE MAINNET ENDPOINTS
PRIMARY_RPC_ENDPOINTS = [
    "https://arc.io",
    "https://drpc.org"  
]

# 🔄 DYNAMIC FALLBACK BACKUP POOL
FALLBACK_RPC_ENDPOINTS = [
    "https://archiechain.io",
    "https://arc.network"
]

# Local persistent log storage path configuration
LOG_STORAGE_FILE = "mainnet_agent_history_logs.txt"
MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB Auto-Rotation limit

# Master State Pool for tracking active URLs dynamically
ACTIVE_RPC_POOL = list(PRIMARY_RPC_ENDPOINTS)

# Stateful network tracking matrix for Circuit Breaker
rpc_status = {url: {"failures": 0, "circuit_broken_until": 0} for url in (PRIMARY_RPC_ENDPOINTS + FALLBACK_RPC_ENDPOINTS)}

# Global Operational Rules for 24/7 Non-Stop Automation
FAILURE_THRESHOLD = 3       
COOLDOWN_SECONDS = 30       
MAX_DRIFT_THRESHOLD = 5     
SUPER_PATIENT_TIMEOUT = 10  
GAS_ALERT_THRESHOLD_GWEI = 50  
def write_persistent_log(message):
    """Safely appends runtime console metrics to local text log. Rotates if file exceeds 5MB."""
    try:
        if os.path.exists(LOG_STORAGE_FILE) and os.path.getsize(LOG_STORAGE_FILE) > MAX_LOG_SIZE_BYTES:
            with open(LOG_STORAGE_FILE, mode="w", encoding="utf-8") as file:
                file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- Log file rotated to save mobile space ---\n")
                
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        clean_line = f"[{timestamp}] {message}\n"
        with open(LOG_STORAGE_FILE, mode="a", encoding="utf-8") as file:
            file.write(clean_line)
    except Exception:
        pass  

def print_embedded_deployment_guides():
    """Prints production-grade deployment scripts directly inside the interface."""
    print("=" * 85)
    print("📱 [24/7 RUNNER ACTIVATED] TERMUX BACKGROUND RUNNER:")
    print("  Run this exact command to maintain execution state indefinitely:")
    print(f"  --> termux-wake-lock && nohup python agent.py >> {LOG_STORAGE_FILE} 2>&1 &")
    print(f"\n  * Note: To view accumulative logs history later, execute: cat {LOG_STORAGE_FILE}")
    print("=" * 85)
    print("💻 [DEPLOYMENT GUIDE] TO RUN SILENTLY ON WINDOWS BACKGROUND:")
    print("  Rename this file to 'agent.pyw' and run via Windows Task Scheduler utilizing: pythonw agent.pyw")
    print("=" * 85 + "\n")
async def send_discord_alert(session, alert_title, details):
    """Sends asynchronous emergency notifications straight to Discord mobile."""
    DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"
    if DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        return

    payload = {
        "username": "Arc Mainnet Auto-Agent",
        "avatar_url": "https://imgur.com",
        "content": f"🚨 **[{alert_title}]**\n{details}\n⏰ **Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}"
    }
    try:
        async with session.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5) as resp:
            if resp.status != 200:  
                logging.error(f"Discord API error: {resp.status}")
    except Exception as e:
        logging.error(f"Discord push failed: {str(e)}")

async def check_rpc_with_circuit_breaker(session, url):
    current_time = time.time()
    if current_time < rpc_status[url]["circuit_broken_until"]:
        return None

    try:
        block_payload = {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": ["latest", False], "id": 1}
        gas_payload = {"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 2}
        
        async with session.post(url, json=block_payload, timeout=SUPER_PATIENT_TIMEOUT) as rb, session.post(url, json=gas_payload, timeout=SUPER_PATIENT_TIMEOUT) as rg:
            if rb.status == 200 and rg.status == 200:
                res_block, res_gas = await rb.json(), await rg.json()
                block_data = res_block.get("result")
                gas_hex = res_gas.get("result")
                
                if block_data and "number" in block_data and "hash" in block_data and gas_hex:
                    rpc_status[url]["failures"] = 0  
                    try:
                        gas_price_gwei = int(gas_hex, 16) / 10**9
                        block_height = int(block_data["number"], 16)
                    except (ValueError, TypeError):
                        return None
                    return {"url": url, "height": block_height, "hash": block_data["hash"], "gas_usdc": round(gas_price_gwei, 2)}
    except asyncio.TimeoutError:
        logging.warning(f"⚠️ Latency Timeout: Node {url} responded slower than {SUPER_PATIENT_TIMEOUT}s.")
    except Exception: pass

    rpc_status[url]["failures"] += 1
    if rpc_status[url]["failures"] >= FAILURE_THRESHOLD:
        rpc_status[url]["circuit_broken_until"] = current_time + COOLDOWN_SECONDS
        await send_discord_alert(session, "NODE_CRASH_ALERT", f"🔴 **Node Down:** {url}\nFailed {FAILURE_THRESHOLD} times.")
    return None
async def monitor_network():
    global ACTIVE_RPC_POOL
    print_embedded_deployment_guides()
    logging.info("🚀 Autonomous Arc Mainnet Monitor Agent successfully deployed (24/7 Engine Active).\n")
    
   connector = aiohttp.TCPConnector(limit_per_host=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            try:
                tasks = [check_rpc_with_circuit_breaker(session, url) for url in ACTIVE_RPC_POOL]
                results = await asyncio.gather(*tasks)
                latest_data = {res["url"]: res for res in results if res is not None}
                
                if not latest_data:
                    logging.warning("⚠️ Primary Nodes Failed! Activating Fallback Router Subsystem...")
                    ACTIVE_RPC_POOL = list(PRIMARY_RPC_ENDPOINTS + FALLBACK_RPC_ENDPOINTS)
                    await asyncio.sleep(10)
                    continue
                
                for url, data in latest_data.items():
                    logging.info(f"  ✅ [Healthy] {url} | Block: {data['height']} | USDC Gas: {data['gas_usdc']} Gwei")
                    if data['gas_usdc'] > GAS_ALERT_THRESHOLD_GWEI:
                        await send_discord_alert(session, "HIGH_GAS_ALERT", f"💵 **Gas Spike:** {data['gas_usdc']} Gwei on {url}")
                
                if len(latest_data) >= 2:
                    heights = [info["height"] for info in latest_data.values()]
                    max_height = max(heights)
                    
                    for url, info in latest_data.items():
                        node_drift = max_height - info["height"]
                        if node_drift >= MAX_DRIFT_THRESHOLD:
                            logging.warning(f"  ⚠️ DRIFT WARNING: Node {url} lagging behind by {node_drift} blocks!")
                            await send_discord_alert(session, "NODE_DRIFT_ALERT", f"⚠️ Node Lagging: {url}")

                    seen_hashes = {}
                    for url, info in latest_data.items():
                        h = info["height"]
                        if h not in seen_hashes: seen_hashes[h] = []
                        seen_hashes[h].append((url, info["hash"]))
                    
                    for h, nodes in seen_hashes.items():
                        if len(nodes) >= 2 and len({b_hash for url, b_hash in nodes}) > 1:
                            logging.critical(f"🚨 CRITICAL FORK DETECTION! Chain split at Block {h}!")
                            await send_discord_alert(session, "CHAIN_FORK_ALERT", f"🔥 Fork at height {h}!")

                print(f"🔄 24/7 Monitor Status: Active | Pool Size: {len(ACTIVE_RPC_POOL)}")
                print("-" * 85)
                await asyncio.sleep(10) 
                
            except Exception as loop_error:
                logging.error(f"🔄 Loop interrupted: {str(loop_error)}. Recovering in 5s...")
                await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_network())
    except KeyboardInterrupt:
        print("\n🛑 Mainnet Monitor Agent safely stopped by user.")









