# 🚀 Deploying Lumina 20 to PythonAnywhere

This guide outlines the steps to deploy your **Lumina 20 Live Bot** (`live_bot.py`) to PythonAnywhere.

> [!NOTE]
> Since `live_bot.py` uses a continuous `while True` loop, it is best suited for an **"Always-on Task"**, which requires a **paid** PythonAnywhere account ($5/month).

## step 1: Set Up Account

1.  Log in to your PythonAnywhere dashboard.
2.  Open a **Bash Console**.

## Step 2: Clone the Repository

In the Bash console, run:

```bash
git clone https://github.com/ronadasakalesha/Lumina-20.git
cd Lumina-20
```

## Step 3: Set Up Environment

Create a virtual environment and install dependencies:

```bash
mkvirtualenv --python=/usr/bin/python3.10 lumina-env
pip install -r requirements.txt
```

*(Note: If `mkvirtualenv` is not available, use `python3 -m venv venv` and `source venv/bin/activate` instead.)*

## Step 4: Configure Credentials

1.  Navigate to the `src` directory:
    ```bash
    cd src
    nano config.py
    ```
2.  Ensure your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are correctly set.
3.  Press `Ctrl+X`, then `Y`, then `Enter` to save and exit.

## Step 5: Test Execution (Optional)

Run the bot manually to ensure it works map:

```bash
python live_bot.py
```

*(You should see "✨ Starting Lumina 20..." and "Waiting...". Press `Ctrl+C` to stop.)*

## Step 6: Set Up Continuous Execution

### Option A: Paid Account (Recommended)
1.  Go to the **Tasks** tab on your dashboard.
2.  Scroll to **"Always-on tasks"**.
3.  Add a new task with the command:
    ```bash
    /home/yourusername/.virtualenvs/lumina-env/bin/python /home/yourusername/Lumina-20/live_bot.py
    ```
    *(Replace `yourusername` with your actual PythonAnywhere username)*.

### Option B: Free Account (Limitations)
Free accounts cannot run continuous scripts reliably. You can:
-   Keep a browser tab open with the Bash console running the script (it may time out).
-   Or, modify the script to run ONCE and exit, then use **Scheduled Tasks** (Daily) - *Not ideal for a 15m strategy*.

**Recommendation**: Use the $5/month "Hacker" plan for reliable 24/7 trading.

## Troubleshooting

### Disk Quota Exceeded
If you see `OSError: [Errno 122] Disk quota exceeded`, your PythonAnywhere account is full.
**Solution:**
1.  Delete the broken virtual environment:
    ```bash
    deactivate
    rmvirtualenv lumina-env
    ```
2.  Clear pip cache:
    ```bash
    rm -rf ~/.cache/pip
    ```
3.  Create a new virtual environment that **reuses system packages** (saves HUGE space):
    ```bash
    mkvirtualenv --system-site-packages --python=/usr/bin/python3.10 lumina-env
    ```
4.  Install only missing packages without caching:
    ```bash
    pip install --no-cache-dir -r requirements.txt
    ```
