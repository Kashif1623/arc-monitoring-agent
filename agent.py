import asyncio
import time
import logging
import aiohttp
import os

# Standard Professional Logging Setup
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 🌐 PRIMARY HIGH-PERFORMANCE ENDPOINTS
PRIMARY_RPC_ENDPOINTS = [
    "https://arc.io",
    "https://drpc.org"  
]

# 🔄 DYNAMIC FALLBACK BACKUP POOL (Activated if primary crashes)
FALLBACK_RPC_ENDPOINTS = [
    "https://rpc.main-1.archiechain.io",  # Fallback Router 1
    "https://rpc.testnet.arc.network"      # Fallback Router 2 (Backup node reference)
]

# Local persistent log storage path configuration
LOG_STORAGE_FILE = "mainnet_agent_history_logs.txt"
MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB Auto-Rotation limit for mobile safety

# Master State Pool for tracking active URLs dynamically
ACTIVE_RPC_POOL = list(PRIMARY_RPC_ENDPOINTS)

# Stateful network tracking matrix for Circuit Breaker
rpc_status = {url: {"failures": 0, "circuit_broken_until": 0} for url in (PRIMARY_RPC_ENDPOINTS + FALLBACK_RPC_ENDPOINTS)}

# Global Operational Rules for 24/7 Non-Stop Automation
FAILURE_THRESHOLD = 3       
COOLDOWN_SECONDS = 30       
MAX_DRIFT_THRESHOLD = 5     
SUPER_PATIENT_TIMEOUT = 10  
GAS_ALERT_THRESHOLD_GWEI = 50  # 🚨 Alert triggers if gas fee exceeds this limit
def write_persistent_log(message):
    """Safely appends runtime console metrics to local text log. Rotates if file exceeds 5MB."""
    try:
        if os.path.exists(LOG_STORAGE_FILE) and os.path.getsize(LOG_STORAGE_FILE) > MAX_LOG_SIZE_BYTES:
            with open(LOG_STORAGE_FILE, mode="w", encoding="utf-8") as file:
                file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- Log file rotated/cleared to save mobile space ---\n")
                
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
    print("  Run this exact command to maintain execution state indefinitely when device locks:")
    print(f"  --> termux-wake-lock && nohup python agent.py >> {LOG_STORAGE_FILE} 2>&1 &")
    print(f"\n  * Note: To view accumulative logs history later, execute: cat {LOG_STORAGE_FILE}")
    print("=" * 85)
    print("💻 [DEPLOYMENT GUIDE] TO RUN SILENTLY ON WINDOWS BACKGROUND:")
    print("  To execute without displaying the command console, rename this file to 'agent.pyw'")
    print("  and invoke it via Windows Task Scheduler utilizing: pythonw agent.pyw")
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
                logging.error(f"Discord API returned error status: {resp.status}")
    except Exception as e:
        logging.error(f"Failed to push discord message stream: {str(e)}")

async def check_rpc_with_circuit_breaker(session, url):
    current_time = time.time()
    if current_time < rpc_status[url]["circuit_broken_until"]:
        return None

    try:
        block_payload = {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": ["latest", False], "id": 1}
        gas_payload = {"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 2}
        
        async with session.post(url, json=block_payload, timeout=SUPER_PATIENT_TIMEOUT) as response_block:
            async with session.post(url, json=gas_payload, timeout=SUPER_PATIENT_TIMEOUT) as response_gas:
                if response_block.status == 200 and response_gas.status == 200:
                    res_block = await response_block.json()
                    res_gas = await response_gas.json()
                    block_data = res_block.get("result") if isinstance(res_block, dict) else None
                    gas_hex = res_gas.get("result") if isinstance(res_gas, dict) else None
                    
                    if block_data and "number" in block_data and "hash" in block_data and gas_hex:
                        rpc_status[url]["failures"] = 0  
                        try:
                            gas_price_gwei = int(gas_hex, 16) / 10**9
                            block_height = int(block_data["number"], 16)
                        except (ValueError, TypeError):
                            return None
                        return {"url": url, "height": block_height, "hash": block_data["hash"], "gas_usdc": round(gas_price_gwei, 2)}
    except asyncio.TimeoutError:
        msg = f"⚠️ Latency Timeout: Node {url} responded slower than {SUPER_PATIENT_TIMEOUT}s."
        logging.warning(msg)
        write_persistent_log(msg)
    except Exception: pass

    rpc_status[url]["failures"] += 1
    if rpc_status[url]["failures"] >= FAILURE_THRESHOLD:
        rpc_status[url]["circuit_broken_until"] = current_time + COOLDOWN_SECONDS
        err_msg = f"🚨 Circuit Tripped! Node {url} is down. Cooldown for {COOLDOWN_SECONDS}s."
        logging.critical(err_msg)
        write_persistent_log(err_msg)
        await send_discord_alert(session, "NODE_CRASH_ALERT", f"🔴 **Node Down:** {url}\nFailed {FAILURE_THRESHOLD} consecutive times.")
    return None
    async def monitor_network():
    global ACTIVE_RPC_POOL
    print_embedded_deployment_guides()
    init_msg = "🚀 Autonomous Arc Mainnet Monitor Agent successfully deployed with Fallback Matrix (24/7 Engine)."
    logging.info(init_msg + "\n")
    write_persistent_log(init_msg)
    
    connector = aiohttp.TCPConnector(limit_per_host=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            try:
                tasks = [check_rpc_with_circuit_breaker(session, url) for url in ACTIVE_RPC_POOL]
                results = await asyncio.gather(*tasks)
                latest_data = {res["url"]: res for res in results if res is not None}
                
                if not latest_data:
                    fallback_warning = "⚠️ Primary Nodes Failed! Activating Fallback Router Subsystem..."
                    logging.warning(fallback_warning)
                    write_persistent_log(fallback_warning)
                    ACTIVE_RPC_POOL = list(PRIMARY_RPC_ENDPOINTS + FALLBACK_RPC_ENDPOINTS)
                    await asyncio.sleep(10)
                    continue
                
                for url, data in latest_data.items():
                    success_msg = f"✅ [Healthy] {url} | Block: {data['height']} | USDC Gas: {data['gas_usdc']} Gwei"
                    logging.info(f"  {success_msg}")
                    write_persistent_log(success_msg)
                    
                    if data['gas_usdc'] > GAS_ALERT_THRESHOLD_GWEI:
                        gas_alert_msg = f"🔥 HIGH GAS FEES ALERT: Network USDC Gas is at {data['gas_usdc']} Gwei!"
                        logging.warning(f"  {gas_alert_msg}")
                        write_persistent_log(gas_alert_msg)
                        await send_discord_alert(session, "HIGH_GAS_ALERT", f"💵 **Arc USDC Gas Spike:** {data['gas_usdc']} Gwei\nNode: {url}")
                
                if len(latest_data) >= 2:
                    heights = [info["height"] for info in latest_data.values()]
                    max_height = max(heights)
                    
                    for url, info in latest_data.items():
                        node_drift = max_height - info["height"]
                        if node_drift >= MAX_DRIFT_THRESHOLD:
                            drift_msg = f"⚠️ DRIFT WARNING: Node {url} lagging behind by {node_drift} blocks!"
                            logging.warning(f"  {drift_msg}")
                            write_persistent_log(drift_msg)
                            await send_discord_alert(session, "NODE_DRIFT_ALERT", f"⚠️ **Node Lagging:** {url}\nBehind by {node_drift} blocks.")

                    seen_hashes = {}
                    for url, info in latest_data.items():
                        h = info["height"]
                        b_hash = info["hash"]
                        if h not in seen_hashes: seen_hashes[h] = []
                        seen_hashes[h].append((url, b_hash))
                    
                    for h, nodes in seen_hashes.items():
                        if len(nodes) >= 2 and len({b_hash for url, b_hash in nodes}) > 1:
                            fork_msg = f"🚨 CRITICAL FORK DETECTION! Chain split at Block {h}!"
                            logging.critical(fork_msg)
                            write_persistent_log(fork_msg)
                            await send_discord_alert(session, "CHAIN_FORK_ALERT", f"🔥 Mismatched hashes at block {h}!")

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

