import anvil.server
import os
from dotenv import load_dotenv

workers = 1
worker_class = "gthread"
threads = 4
timeout = 120
bind = "0.0.0.0:" + os.environ.get("PORT", "10000")

def post_fork(server, worker):
    load_dotenv()
    key = os.getenv("ANVIL_UPLINK_KEY")
    if key:
        try:
            anvil.server.disconnect()
        except Exception:
            pass
        anvil.server.connect(key)