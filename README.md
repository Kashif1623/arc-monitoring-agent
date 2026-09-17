# ⚡ Arc Network Multi-Node Monitoring Agent

Welcome to the **Arc Network Monitoring Agent**! This repository contains high-performance, asynchronous Python scripts designed to monitor both **Arc Mainnet** and **Arc Testnet** core infrastructure directly from mobile environments.

Built specifically for low-resource environments like **Termux (Android Linux Terminal)** and **Pydroid 3 (Android IDE)**, this agent tracks live block generation, monitors block synchronization lag (drift), detects potential network forks, and watches dollar-denominated gas configurations in real-time.

---

## 🛠️ Global Network Parameters Inside Agent

| Parameter / Metric | 🌐 Arc Mainnet (`mainnet_agent.py`) | 🧪 Arc Testnet (`testnet_agent.py`) |
| :--- | :--- | :--- |
| **Chain ID** | `5042` (`0x13b2`) | Sandbox Testing standard |
| **Gas Fee Asset** | Native Stablecoin (`USDC`) | Testnet Gwei / Asset Standard |
| **Block Time Speed** | ~0.5 Seconds Deterministic Finality | Fast Consensus Iterations |
| **Primary Node** | `https://drpc.org` | `https://drpc.org` |
| **Load-Balanced Node**| `https://drpc.org` | `https://drpc.org-testnet` |

---

## 📱 Option 1: Running inside Termux (Indefinite Background Runner)

Termux is the best option if you want to keep the script running 24/7 non-stop in the background of your phone, even when your screen is turned off.

### Step 1: Open Termux and Install Prerequisites
Copy and paste this command sequences to set up your environment safely:
```bash
# Update local packages and install system essentials
pkg update -y && pkg upgrade -y
pkg install python git -y

# Install high-performance asynchronous HTTP networking modules
pip install aiohttp
```

### Step 2: Download Your GitHub Repo
Replace `your-username` and `your-repo-name` with your actual GitHub details:
```bash
git clone https://github.com
cd your-repo-name
```

### Step 3: Run the Script Securely in Background
To ensure Android doesn't kill the terminal when you close the app or lock your screen, execute the script with a system wake-lock:
```bash
# Prevent Android system processor from sleeping
termux-wake-lock

# Launch Mainnet Agent in background (Saves outputs directly to text log file)
nohup python mainnet_agent.py >> mainnet_agent_history_logs.txt 2>&1 &

# OR Launch Testnet Agent instead
nohup python testnet_agent.py >> agent_history_logs.txt 2>&1 &
```

### Step 4: Check Live Operational Logs
To see what your agent is printing right now in the background, use the `tail` tracking feature:
```bash
# Watch real-time mainnet processing block metrics
tail -f mainnet_agent_history_logs.txt
```
*(Press `Ctrl + C` anytime to exit the log view screen. The script will keep running silently).*

---

## 💻 Option 2: Running inside Pydroid 3 (Visual Mobile IDE)

If you prefer a visual interface where you can hit a "Play" button and watch the logs print line-by-line, Pydroid 3 is perfect.

### Step 1: Install Pydroid 3 App
* Go to the **Google Play Store**.
* Search and install **Pydroid 3 - IDE for Python 3**.

### Step 2: Install Network Dependencies
* Open **Pydroid 3**.
* Tap the **Menu icon** (three lines on the top left grid).
* Go to **Pip**.
* Tap the **QUICK INSTALL** tab, look for `aiohttp` (or go to the **LIBRARY** tab, type `aiohttp`, and tap **Install**).
* Wait for the terminal to display `Complete`.

### Step 3: Paste and Execute Your Code
* Copy your raw code directly from GitHub (`mainnet_agent.py` or `testnet_agent.py`).
* Paste it inside the main empty text editor canvas of **Pydroid 3**.
* Tap the **Folder icon** on the top right bar and choose **Save** to store it locally as `agent.py`.
* Tap the yellow **Play/Button icon** on the bottom right corner.
* The script will open a graphical terminal window and start printing live network telemetry logs every 10 seconds!

---

## 🚨 Troubleshooting & Node Isolation (Circuit Breaker)

* **Why am I seeing "CRITICAL FAULT: Node isolated"?**  
  The agent contains a safety feature called a **Circuit Breaker**. If a primary RPC server stops responding or gives corrupt block data 3 times in a row, the script isolates that node for **30 seconds** to save battery and drops directly into the backup failover nodes pool (`https://arc.network`). It will automatically re-test the primary link after the cooldown ends.
* **Why did the Testnet Agent stop after 15 minutes?**  
  The testnet configuration has a pre-allocated runtime barrier of **900 seconds (`TOTAL_RUN_TIME_LIMIT`)**. This is built intentionally to prevent background battery drainage during sandbox code tests. It detaches and terminates the loop safely without leaking operating system sockets.

---
💡 *Tip: If running on Termux, remember to type `termux-wake-unlock` when you want to fully stop your tests and allow your device to go into deep battery saving sleep state.*
