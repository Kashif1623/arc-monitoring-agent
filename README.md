# ⚡ Arc Network Multi-Node Infrastructure Sentinel

A production-grade, asynchronous infrastructure daemon engineered for continuous health validation, real-time metrics harvesting, and cryptographic state tracking across **Arc Mainnet** and **Arc Testnet** environments.

---

## 📦 Step 1: Pre-requisites & Dependency Installation

Before running the monitoring agents, you must install the required asynchronous HTTP networking libraries. This setup is mandatory for both new and experienced developers.

### For Mobile Platforms (Pydroid 3 App)
1. Open **Pydroid 3**.
2. Tap the **Menu icon** (three horizontal lines on the top left grid).
3. Select **Pip**.
4. Inside the library lookup bar, type exactly: `aiohttp`
5. Tap **Install**. Wait until the terminal status window prints `Complete`.

### For Server Platforms (Termux / Linux Terminal)
Open your terminal window interface and execute the following sequential toolchain command to provision core packages and dependencies:
```bash
pkg update && pkg install python libffi clang openssl -y && pip install aiohttp
```

---

## 📱 Step 2: Deployment Layout Options

### Option A: Foreground Development Deployment (via Pydroid 3 IDE)

This layout is perfect for quick testing, code modifications, or developer sandbox reviews directly on your mobile device screen interface.

1. Create a **New File** inside your Pydroid 3 editor workspace canvas.
2. Copy your raw python configuration script (`mainnet_agent.py` or `testnet_agent.py`).
3. Paste the contents using the upper **Clipboard Icon** menu shortcut option.
4. Tap the **Folder Icon** on the upper action bar and select **Save** to commit the asset onto local memory disk space.
5. Tap the circular **Yellow Play/Button Icon** located at the bottom right corner of the canvas frame to engage telemetry updates.

### Option B: 24/7 Production Background Deployment (via Termux Server)

This layout is intended for enterprise-level deployments. It utilizes automated shell processes to ensure tracking persists even when the device goes into deep sleep mode or the foreground UI terminates.

1. Secure your active shell framework workspace from being paused by the operating system layer:
```bash
termux-wake-lock
```
2. Spin up the background thread sequence using `nohup` to pipe your operational tracking telemetry into silent storage buffers indefinitely:
```bash
nohup python agent.py >> mainnet_agent_history_logs.txt 2>&1 &
```

---

## 🛠️ Infrastructure Core Configurations & Parameters

The control loop layer is bound by the following optimized operational safety parameters:

- **`FAILURE_THRESHOLD = 3`**: Safe isolation bounds before the automated circuit breaker trips a faulty gateway.
- **`COOLDOWN_SECONDS = 20 / 30`**: The mandatory circuit quarantine interval before re-probing decentralized endpoints.
- **`TOTAL_RUN_TIME_LIMIT = 900`**: Maximum lifespan constraints configured for advanced debugging runs (safely terminates active loop context after 15 minutes).
- **`GAS_ALERT_THRESHOLD_GWEI`**: Triggers real-time alerts whenever underlying gas fees spike past anomalous network thresholds.

---

## 🩹 Troubleshooting & Node Fault Isolation

### Why am I seeing a hidden background log event regarding isolated nodes?
The agent runs an embedded **Circuit Breaker Pattern**. If a primary RPC connection fails to deliver block metrics or gas rates 3 times sequentially, the agent safely quarantines the path for a cooldown window. This protects your mobile battery and keeps network socket operations flowing cleanly.

### How do I stop a background running task inside Termux?
If you want to clear your active background worker nodes, run this terminal kill switch string:
```bash
pkill -f python
```
