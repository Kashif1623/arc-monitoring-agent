import time
import logging
import requests

# Setup Logging for Warnings and Alerts
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 1. LIVE ARC TESTNET RPC ENDPOINTS (Rais's suggestion)
# Yahan maine asli public endpoints dal diye hain
RPC_ENDPOINTS = [
    "https://rpc.testnet.arc.network",
    "https://arc-testnet.drpc.org"
]

# Circuit Breaker state track karne ke liye tracking system
rpc_status = {url: {"failures": 0, "circuit_broken_until": 0} for url in RPC_ENDPOINTS}

# Circuit Breaker Configuration
FAILURE_THRESHOLD = 3       # N Failures (Kitni baar fail ho toh block karein)
COOLDOWN_SECONDS = 30       # X Seconds (Kitne seconds ke liye rpc block rahe)
MAX_DRIFT_THRESHOLD = 50    # Agar koi node 50 blocks piche ho toh down mana jaye

def check_rpc_with_circuit_breaker(url):
    """
    Suggestion 2: Unstable RPC Handling with Circuit Breaker and Cheap Probe
    """
    current_time = time.time()
    
    # Check if circuit is broken
    if current_time < rpc_status[url]["circuit_broken_until"]:
        logging.warning(f"⚠️ Circuit Broken for {url}. Skipping to save performance.")
        return None

    try:
        # Cheap probe using eth_chainId instead of heavy retries
        payload_id = {"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}
        response = requests.post(url, json=payload_id, timeout=3)
        
        if response.status_code == 200 and "result" in response.json():
            # If cheap probe passes, get the actual block data
            payload_block = {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": ["latest", False], "id": 2}
            block_resp = requests.post(url, json=payload_block, timeout=5).json()
            
            # Reset failure counter on success
            rpc_status[url]["failures"] = 0
            
            block_data = block_resp.get("result")
            if block_data:
                return {
                    "height": int(block_data["number"], 16),
                    "hash": block_data["hash"]
                }
        
    except Exception as e:
        pass

    # Handle failures and trip the circuit breaker
    rpc_status[url]["failures"] += 1
    logging.error(f"❌ Failed to connect to {url}. Failures: {rpc_status[url]['failures']}")
    
    if rpc_status[url]["failures"] >= FAILURE_THRESHOLD:
        rpc_status[url]["circuit_broken_until"] = current_time + COOLDOWN_SECONDS
        logging.critical(f"🚨 Circuit Tripped! {url} has been disabled for {COOLDOWN_SECONDS} seconds.")
    
    return None

def monitor_network():
    logging.info("🚀 Arc Network Automated Monitoring Agent Started...")
    
    while True:
        latest_data = {}
        
        # Sary endpoints se data fetch karna
        for url in RPC_ENDPOINTS:
            data = check_rpc_with_circuit_breaker(url)
            if data:
                latest_data[url] = data
        
        if len(latest_data) >= 2:
            heights = [info["height"] for info in latest_data.values()]
            max_height = max(heights)
            min_height = min(heights)
            
            # Suggestion 1: Track block height DRIFT between RPC endpoints
            drift = max_height - min_height
            for url, info in latest_data.items():
                node_drift = max_height - info["height"]
                if node_drift >= MAX_DRIFT_THRESHOLD:
                    logging.critical(f"🚨 DRIFT ALERT: Node {url} is lagging by {node_drift} blocks! Max height is {max_height}.")

            # Suggestion 3: Log Finality & Hash Mismatch Verification
            seen_hashes = {}
            for url, info in latest_data.items():
                h = info["height"]
                b_hash = info["hash"]
                
                if h not in seen_hashes:
                    seen_hashes[h] = []
                seen_hashes[h].append((url, b_hash))
                
            for h, nodes in seen_hashes.items():
                if len(nodes) >= 2:
                    first_hash = nodes[0][1]
                    for url, b_hash in nodes:
                        if b_hash != first_hash:
                            logging.critical(f"🔥 CRITICAL ALERT: Block Hash Mismatch at height {h}! Network consensus issue detected.")
                            logging.critical(f"Node 1 ({nodes[0][0]}): {first_hash}")
                            logging.critical(f"Node 2 ({url}): {b_hash}")

        else:
            logging.warning("⚠️ Consensus verification skipped: Not enough active RPC endpoints available.")

        # Interval between monitoring loops
        time.sleep(10)

if __name__ == "__main__":
    monitor_network()
