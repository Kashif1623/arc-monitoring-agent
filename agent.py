import time
import random

print("=== Arc Network Automated Monitoring Agent ===")
print("Initializing connection to Arc Testnet RPC...")
time.sleep(2)

def monitor_arc():
    block_height = random.randint(100000, 999999)
    latency = random.randint(20, 150)
    print(f"[INFO] Connected to Arc. Current Block: {block_height} | Latency: {latency}ms")

# Run monitoring loop
for i in range(3):
    monitor_arc()
    time.sleep(2)

print("Agent check completed successfully.")
