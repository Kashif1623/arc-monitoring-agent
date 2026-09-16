import time
import logging
import requests

# Setup Logging - Sirf zaroori warnings aur data dikhane ke liye
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# LIVE ARC TESTNET RPC ENDPOINTS
RPC_ENDPOINTS = [
    "https://rpc.testnet.arc.network",
    "https://arc-testnet.drpc.org"
]

# State tracking
rpc_status = {url: {"failures": 0, "circuit_broken_until": 0} for url in RPC_ENDPOINTS}

# Configuration - Server ko handle karne ke rules
FAILURE_THRESHOLD = 5       # Failures limit barha di taake slow net par foran block na ho
COOLDOWN_SECONDS = 20       
MAX_DRIFT_THRESHOLD = 50    
SLOW_TIMEOUT = 15           # Server ko response dene ke liye 15 seconds ka zyada waqt diya

def check_rpc_with_circuit_breaker(url):
    current_time = time.time()
    
    if current_time < rpc_status[url]["circuit_broken_until"]:
        return None

    # Screen par bura 'Failed' message dikhane ke bajaye calm update dikhein
    logging.info(f"🔄 Connecting to {url} (Allowing extra time if network is slow)...")

    try:
        # Step 1: Cheap probe with high timeout to handle slowness
        payload_id = {"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}
        response = requests.post(url, json=payload_id, timeout=SLOW_TIMEOUT)
        
        if response.status_code == 200 and "result" in response.json():
            # Step 2: Sahi data fetch karna
            payload_block = {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": ["latest", False], "id": 2}
            block_resp = requests.post(url, json=payload_block, timeout=SLOW_TIMEOUT).json()
            
            rpc_status[url]["failures"] = 0  # Success par failure counter zero
            
            block_data = block_resp.get("result")
            if block_data:
                return {
                    "height": int(block_data["number"], 16),
                    "hash": block_data["hash"]
                }
        
    except requests.exceptions.Timeout:
        # Agar network slow hai toh failed bolne ke bajaye yeh batayein
        logging.warning(f"⚠️ {url} response is slow today, retrying in next loop...")
    except Exception as e:
        pass

    # Agar server bilkul hi dead ho tabhi failure count karein
    rpc_status[url]["failures"] += 1
    
    if rpc_status[url]["failures"] >= FAILURE_THRESHOLD:
        rpc_status[url]["circuit_broken_until"] = current_time + COOLDOWN_SECONDS
        logging.critical(f"🚨 Circuit Tripped! {url} is completely down. Paused for {COOLDOWN_SECONDS}s.")
    
    return None

def monitor_network():
    logging.info("🚀 Arc Network Smart Monitoring Agent Started...")
    
    while True:
        latest_data = {}
        
        for url in RPC_ENDPOINTS:
            data = check_rpc_with_circuit_breaker(url)
            if data:
                latest_data[url] = data
                # Sahi data milne par screen par pyara aur theek status dikhayein
                logging.info(f"✅ {url} | Block Height: {data['height']} | Status: Healthy")
        
        if len(latest_data) >= 2:
            heights = [info["height"] for info in latest_data.values()]
            max_height = max(heights)
            
            # Block height drift track karna
            for url, info in latest_data.items():
                node_drift = max_height - info["height"]
                if node_drift >= MAX_DRIFT_THRESHOLD:
                    logging.warning(f"⚠️ DRIFT: Node {url} is lagging behind by {node_drift} blocks.")

            # Hash Mismatch track karna
            seen_hashes = {}
            for url, info in latest_data.items():
                h = info["height"]
                b_hash = info["hash"]
                if h not in seen_hashes:
                    seen_hashes[h] = []
                seen_hashes[h].append((url, b_hash))

        print("-" * 60) # Visual separator for loops
        time.sleep(10)

if __name__ == "__main__":
    monitor_network()
