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

# 🌐 REAL & ACTIVE ARC TESTNET ENDPOINTS (Auto-Configured)
RPC_ENDPOINTS = [
    "https://arc.io",
    "https://drpc.org"
]

# Local persistent log storage path config
LOG_STORAGE_FILE = "agent_history_logs.txt"

# Stateful tracking network matrix
rpc_status = {url: {"failures": 0, "circuit_broken_until": 0} for url in RPC_ENDPOINTS}

# Global Operational Rules for 24/7 Automation
FAILURE_THRESHOLD = 3       
COOLDOWN_SECONDS = 30       
MAX_DRIFT_THRESHOLD = 5     
SUPER_PATIENT_TIMEOUT = 10  

# 🔋 BATTERY SAVER CONFIGURATION (15 Minutes = 900 Seconds)
TOTAL_RUN_TIME_LIMIT = 900  
START_TIMESTAMP = time.time()

def write_persistent_log(message):
    """Safely appends runtime console metrics to local text log without overwriting history."""
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        clean_line = f"[{timestamp}] {message}\n"
        with open(LOG_STORAGE_FILE, mode="a", encoding="utf-8") as file:
            file.write(clean_line)
    except Exception:
        pass  # Enforces silent fault tolerance if system path locks temporarily

def print_embedded_deployment_guides():
    """Prints production-grade deployment scripts directly inside the interface."""
    print("=" * 85)
    print("📱 [BATTERY SAVER ACTIVATED] TERMUX 15-MINUTE BACKGROUND RUNNER:")
    print("  Run this exact command so it keeps running even if your phone is locked.")
    print("  It will AUTOMATICALLY KILL ITSELF after exactly 15 minutes to save battery!")
    print(f"  --> termux-wake-lock && nohup python agent.py >> {LOG_STORAGE_FILE} 2>&1 &")
    print(f"\n  * Note: To view accumulative logs history later, type: cat {LOG_STORAGE_FILE}")
    print("=" * 85 + "\n")

async def send_discord_alert(session, alert_title, details):
    """Sends asynchronous emergency notifications straight to Discord mobile."""
    # 🔴 Optional: Agar mobile par notification chahiye toh link yahan paste karein
    DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"
    
    if DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        return

    payload = {
        "username": "Arc Testnet Auto-Agent",
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
        payload = {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": ["latest", False], "id": 1}
        async with session.post(url, json=payload, timeout=SUPER_PATIENT_TIMEOUT) as response:
            if response.status == 200:
                res_json = await response.json()
                block_data = res_json.get("result")
                if block_data and "number" in block_data and "hash" in block_data:
                    rpc_status[url]["failures"] = 0  
                    return {
                        "url": url, 
                        "height": int(block_data["number"], 16), 
                        "hash": block_data["hash"]
                    }
    except asyncio.TimeoutError:
        msg = f"⚠️ Latency Timeout: Node {url} responded slower than {SUPER_PATIENT_TIMEOUT}s."
        logging.warning(msg)
        write_persistent_log(msg)
    except Exception:
        pass

    rpc_status[url]["failures"] += 1
    if rpc_status[url]["failures"] >= FAILURE_THRESHOLD:
        rpc_status[url]["circuit_broken_until"] = current_time + COOLDOWN_SECONDS
        err_msg = f"🚨 Circuit Tripped! {url} is down. Cooldown for {COOLDOWN_SECONDS}s."
        logging.critical(err_msg)
        write_persistent_log(err_msg)
        await send_discord_alert(session, "NODE_CRASH_ALERT", f"🔴 **Node Down:** {url}\nFailed {FAILURE_THRESHOLD} consecutive times.")
    return None

async def monitor_network():
    print_embedded_deployment_guides()
    init_msg = "🚀 Autonomous Arc Testnet Monitor Agent successfully deployed (15-Min Timer Active)."
    logging.info(init_msg + "\n")
    write_persistent_log(init_msg)
    
    async with aiohttp.ClientSession() as session:
        while True:
            # 🕒 Check dynamic execution budget constraints
            elapsed_time = time.time() - START_TIMESTAMP
            if elapsed_time >= TOTAL_RUN_TIME_LIMIT:
                kill_msg = "🔋 [BATTERY SAVER] 15 minutes limit reached! Automatically shutting down agent process now."
                logging.critical(kill_msg)
                write_persistent_log(kill_msg)
                await send_discord_alert(session, "AGENT_AUTO_SHUTDOWN", "🔋 **Battery Saver:** Agent completed its 15-minute runtime budget and shut down safely.")
                sys.exit(0) # Strictly kills the python script automatically from background

            try:
                tasks = [check_rpc_with_circuit_breaker(session, url) for url in RPC_ENDPOINTS]
                results = await asyncio.gather(*tasks)
                
                latest_data = {res["url"]: res for res in results if res is not None}
                
                if not latest_data:
                    msg = "⚠️ Searching for active network health metrics... Retrying in 10s."
                    logging.warning(msg)
                    write_persistent_log(msg)
                
                for url, data in latest_data.items():
                    success_msg = f"✅ [Healthy Connection] {url} | Current Testnet Block: {data['height']}"
                    logging.info(f"  {success_msg}")
                    write_persistent_log(success_msg)
                
                if len(latest_data) >= 2:
                    heights = [info["height"] for info in latest_data.values()]
                    max_height = max(heights)
                    
                    # 1. Automatic Drift Performance Analytics
                    for url, info in latest_data.items():
                        node_drift = max_height - info["height"]
                        if node_drift >= MAX_DRIFT_THRESHOLD:
                            drift_msg = f"⚠️ DRIFT WARNING: Node {url} lagging behind by {node_drift} blocks!"
                            logging.warning(f"  {drift_msg}")
                            write_persistent_log(drift_msg)
                            await send_discord_alert(session, "NODE_DRIFT_ALERT", f"⚠️ **Node Lagging:** {url}\nBehind by {node_drift} blocks.")

                    # 2. Consensus Fork Management Analytics
                    seen_hashes = {}
                    for url, info in latest_data.items():
                        h = info["height"]
                        b_hash = info["hash"]
                        if h not in seen_hashes:
                            seen_hashes[h] = []
                        seen_hashes[h].append((url, b_hash))
                    
                    for h, nodes in seen_hashes.items():
                        if len(nodes) >= 2:
                            unique_hashes = {b_hash for url, b_hash in nodes}
                            if len(unique_hashes) > 1:
                                fork_msg = f"🚨 CRITICAL MISMATCH! Suspected Chain split/fork at Block {h}!"
                                logging.critical(fork_msg)
                                write_persistent_log(fork_msg)
                                await send_discord_alert(session, "CHAIN_FORK_ALERT", f"🔥 **CRITICAL:** Mismatched block hashes found at height {h}!")
                                for url, b_hash in nodes:
                                    logging.critical(f"   -> Node: {url} | Hash: {b_hash}")

                remaining_minutes = int((TOTAL_RUN_TIME_LIMIT - elapsed_time) / 60)
                print(f"⏳ Time Remaining until Auto-Kill: {remaining_minutes} Minutes")
                print("-" * 85)
                await asyncio.sleep(10) 
                
            except Exception as loop_error:
                logging.error(f"🔄 Session interrupted: {str(loop_error)}. Recovering in 5s...")
                await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_network())
    except KeyboardInterrupt:
        logging.info("🛑 Monitor agent safely stopped via terminal control.")
