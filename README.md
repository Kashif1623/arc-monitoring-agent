# ⚡ Arc Network Multi-Node Infrastructure Sentinel

A production-grade asynchronous infrastructure daemon for continuous health validation, real-time metrics harvesting, and cryptographic state tracking across **Arc Mainnet** and **Arc Testnet** environments.

---

## 📦 Step 1: Pre-requisites & Dependency Installation

Install the required asynchronous HTTP networking libraries (`aiohttp`) before running the monitoring agents.

### For Mobile Platforms (Pydroid 3 App)
1. Open **Pydroid 3** -> Tap the **Menu icon** -> Select **Pip**.
2. Type `aiohttp` in the lookup bar and tap **Install** until it prints `Complete`.

### For Server Platforms (Termux / Linux Terminal)
Execute the following command to provision core packages and dependencies:
```bash
pkg update && pkg install python libffi clang openssl curl -y && pip install aiohttp
```

---

## 📱 Step 2: Deployment Layout Options

### Option A: Foreground Development Deployment (Pydroid 3)
1. Create a **New File** in Pydroid 3.
2. Copy your Python configuration script (`agent.py` or `agent_testnet.py`) from GitHub and paste it using the clipboard icon.
3. Save the file and tap the yellow **Play/Button Icon** to run.

#### 🟩 Box 1: Run Arc Mainnet Monitoring Agent (Pydroid 3)
```bash
curl -sSL https://raw.githubusercontent.com/Kashif1623/arc-monitoring-agent/main/agent.py -o agent.py
```

#### 🔵 Box 2: Run Arc Testnet Monitoring Agent (Pydroid 3)
```bash
curl -sSL https://raw.githubusercontent.com/Kashif1623/arc-monitoring-agent/main/agent_testnet.py -o agent_testnet.py
```

### Option B: 24/7 Production Background Deployment (Termux Server)
1. Secure your active shell workspace:
```bash
termux-wake-lock
```
2. Run the monitoring agents in the background:

#### 🟢 Box 1: Run Arc Mainnet Monitoring Agent
```bash
curl -sSL https://raw.githubusercontent.com/Kashif1623/arc-monitoring-agent/main/agent.py -o agent.py && nohup python agent.py >> mainnet_agent_history_logs.txt 2>&1 &

```

#### 🔵 Box 2: Run Arc Testnet Monitoring Agent
```bash
curl -sSL https://raw.githubusercontent.com/Kashif1623/arc-monitoring-agent/main/agent_testnet.py -o agent_testnet.py && nohup python agent_testnet.py >> agent_history_logs.txt 2>&1 &
```

---

## 🛠️ Infrastructure Core Configurations & Parameters

- **`FAILURE_THRESHOLD`**: Mainnet `2`, Testnet `3`.
- **`COOLDOWN_SECONDS`**: Mainnet `30`s, Testnet `20`s.
- **`TOTAL_RUN_TIME_LIMIT`**: `900` seconds (Testnet max lifespan).
- **`GAS_ALERT_THRESHOLD_GWEI`**: Mainnet `35.0 Gwei`, Testnet `150 Gwei`.

---

## 🩹 Troubleshooting & Node Fault Isolation

- **View Live Logs:** Use `tail -f mainnet_agent_history_logs.txt` or `tail -f agent_history_logs.txt`.
- **Stop Background Tasks:** Run `pkill -f python`.
