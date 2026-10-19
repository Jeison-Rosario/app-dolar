"""Start Streamlit using the network settings assigned by the host."""
import os
from pathlib import Path
import re
import sys
from dotenv import load_dotenv

def command(env):
    base = env.get("BASE_PATH", "").strip("/")
    if base and not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", base):
        raise ValueError("BASE_PATH inválido")
    port = int(env.get("PORT", "8501"))
    if not 1 <= port <= 65535:
        raise ValueError("PORT inválido")
    return [sys.executable, "-m", "streamlit", "run", str(Path(__file__).with_name("app.py")),
            "--server.address=" + (env.get("IP") or env.get("HOST") or "127.0.0.1"),
            "--server.port=" + str(port), "--server.baseUrlPath=" + base,
            "--server.headless=true", "--server.fileWatcherType=none", "--browser.gatherUsageStats=false"]

if __name__ == "__main__":
    load_dotenv(Path(__file__).with_name(".env"), override=False)
    args = command(os.environ)
    os.execv(args[0], args)
