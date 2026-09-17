import asyncio
import time
import logging
import aiohttp

# Standard Professional Logging Setup
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# LIVE PRODUCTION ENDPOINTS (Arc Mainnet High-Performance Paths)
RPC_ENDPOINTS = [
    "https://arc.io",
    "https://drpc.org"
]

# Stateful tracking network matrix
rpc_status = {url: {"failures": 0, "circuit_broken_until": 0} for url in RPC_ENDPOINTS}

# Global Operational Rules
FAILURE_THRESHOLD = 3       
COOLDOWN_SECONDS = 30       
MAX_DRIFT_THRESHOLD = 5     
SUPER_PATIENT_TIMEOUT = 10  # Parallel async calls ke liye 10 seconds kaafi hain

async def send_discord_alert(session, alert_title, details):
    """Sends asynchronous emergency notifications straight to Discord mobile."""
    # 🔴 BROWSER SE COPY KI HUI LINK IS QUOTES KE ANDAR PASTE KAREIN:
    DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"
    
    if DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        return

    payload = {
        "username": "Arc Network Async Monitor Bot",
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
        logging.warning(f"🚫 Circuit is OPEN for {url}. Temporarily skipping connection deployment.")
        return None

    logging.info(f"🔄 Interrogating node path: {url}")
    payload = {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": ["latest", False], "id": 1}
    
    try:
        async with session.post(url, json=payload, timeout=SUPER_PATIENT_TIMEOUT) as response:
            if response.status == 200:
                res_json = await response.json()
                block_data = res_json.get("result")
                if block_data and "number" in block_data and "hash" in block_data:
                    rpc_status[url]["failures"] = 0  # Success reset
                    return {
                        "url": url, 
                        "height": int(block_data["number"], 16), 
                        "hash": block_data["hash"]
                    }
    except asyncio.TimeoutError:
        logging.warning(f"⚠️ Latency Timeout: Node {url} responded slower than {SUPER_PATIENT_TIMEOUT}s.")
    except Exception as e:
        logging.error(f"❌ Connection failure on target {url}: {str(e)}")

    # Failure counting increments
    rpc_status[url]["failures"] += 1
    if rpc_status[url]["failures"] >= FAILURE_THRESHOLD:
        rpc_status[url]["circuit_broken_until"] = current_time + COOLDOWN_SECONDS
        logging.critical(f"🚨 Circuit Tripped! {url} is down. Cooldown for {COOLDOWN_SECONDS}s.")
        await send_discord_alert(session, "NODE_CRASH_ALERT", f"🔴 **Node Down:** {url}\nFailed {FAILURE_THRESHOLD} consecutive times.")
    return None

async def monitor_network():
    logging.info("🚀 Production Arc Network Autonomous Async Agent Activated.\n")
    
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = [check_rpc_with_circuit_breaker(session, url) for url in RPC_ENDPOINTS]
            results = await asyncio.gather(*tasks)
            
            # Map successful node responses
            latest_data = {res["url"]: res for res in results if res is not None}
            
            for url, data in latest_data.items():
                logging.info(f"  ✅ [Healthy] {url} | Block Height: {data['height']}")
            
            if len(latest_data) >= 2:
                heights = [info["height"] for info in latest_data.values()]
                max_height = max(heights)
                
                # 1. Asynchronous Sync Drift Analytics
                for url, info in latest_data.items():
                    node_drift = max_height - info["height"]
                    if node_drift >= MAX_DRIFT_THRESHOLD:
                        logging.warning(f"  ⚠️ DRIFT WARNING: Node {url} lagging behind by {node_drift} blocks!")
                        await send_discord_alert(session, "NODE_DRIFT_ALERT", f"⚠️ **Node Lagging:** {url}\nBehind by {node_drift} blocks.")

                # 2. Complete Fork / Consensus Split Analytics Matrix
                seen_hashes = {}
                for url, info in latest_data.items():
                    h = info["height"]
                    b_hash = info["hash"]
                    if h not in seen_hashes:
                        seen_hashes[h] = []
                    seen_hashes[h].append((url, b_hash))
                
                for h, nodes in seen_hashes.items():
                    if len(nodes) >= 2:
                        unique_hashes = {item[1] for item in nodes}
                        if len(unique_hashes) > 1:
                            logging.critical(f"🚨 CRITICAL MISMATCH! Suspected Chain split/fork at Block {h}!")
                            await send_discord_alert(session, "CHAIN_FORK_ALERT", f"🔥 **CRITICAL:** Mismatched block hashes found at height {h}!")
                            for url, b_hash in nodes:
                                logging.critical(f"   -> Node: {url} | Hash: {b_hash}")

            print("-" * 85)
            await asyncio.sleep(10) # Next request loop cooldown window

if __name__ == "__main__":
    try:
        asyncio.run(monitor_network())
    except KeyboardInterrupt:
        logging.info("🛑 Monitor agent safely stopped via terminal control interface.")
