import asyncio
import time
import logging
import aiohttp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RPC_ENDPOINTS = [
    "https://drpc.live",
    "https://arc.network"
]

rpc_status = {url: {"failures": 0, "circuit_broken_until": 0} for url in RPC_ENDPOINTS}

FAILURE_THRESHOLD = 5       
COOLDOWN_SECONDS = 20       
MAX_DRIFT_THRESHOLD = 5     
SUPER_PATIENT_TIMEOUT = 30  

async def check_rpc_with_circuit_breaker(session, url):
    current_time = time.time()
    if current_time < rpc_status[url]["circuit_broken_until"]:
        return None

    logging.info(f"🔄 Searching Testnet health from {url}...")
    payload = {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": ["latest", False], "id": 1}
    
    try:
        async with session.post(url, json=payload, timeout=SUPER_PATIENT_TIMEOUT) as response:
            if response.status == 200:
                res_json = await response.json()
                block_data = res_json.get("result")
                if block_data:
                    rpc_status[url]["failures"] = 0
                    return {"url": url, "height": int(block_data["number"], 16), "hash": block_data["hash"]}
    except asyncio.TimeoutError:
        logging.warning(f"⚠️ {url} taking too long, but agent is keeping patience...")
    except Exception:
        pass

    rpc_status[url]["failures"] += 1
    if rpc_status[url]["failures"] >= FAILURE_THRESHOLD:
        rpc_status[url]["circuit_broken_until"] = current_time + COOLDOWN_SECONDS
        logging.critical(f"🚨 Circuit Tripped! {url} is down. Paused for {COOLDOWN_SECONDS}s.")
    return None

async def monitor_network():
    logging.info("🚀 Arc Network TESTNET Monitoring Agent Started...")
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = [check_rpc_with_circuit_breaker(session, url) for url in RPC_ENDPOINTS]
            results = await asyncio.gather(*tasks)
            latest_data = {res["url"]: res for res in results if res is not None}
            
            for url, data in latest_data.items():
                logging.info(f"✅ Testnet | Healthy | Block: {data['height']}")
            
            if len(latest_data) >= 2:
                heights = [info["height"] for info in latest_data.values()]
                max_height = max(heights)
                
                for url, info in latest_data.items():
                    node_drift = max_height - info["height"]
                    if node_drift >= MAX_DRIFT_THRESHOLD:
                        logging.warning(f"⚠️ DRIFT ALERT: Node lagging behind by {node_drift} blocks!")

                height_groups = {}
                for url, info in latest_data.items():
                    h = info["height"]
                    if h not in height_groups: height_groups[h] = set()
                    height_groups[h].add(info["hash"])
                
                for h, hashes in height_groups.items():
                    if len(hashes) > 1:
                        logging.critical(f"🚨 CONSENSUS MISMATCH! Possible Fork on height {h}!")

            print("-" * 70)
            await asyncio.sleep(10)

if __name__ == "__main__":
    try: asyncio.run(monitor_network())
    except KeyboardInterrupt: logging.info("👋 Agent stopped.")
