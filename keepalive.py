import os
from flask import Flask
from threading import Thread


app = Flask('')

@app.route('/')
def home():
    return "sentinelone is online!"

def run():
    # Render tells a web service which port to listen on through $PORT
    # (10000 by default). If no port is detected the deploy times out.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # daemon=True: if the bot crashes, the process exits and Render restarts it,
    # instead of this web server keeping a dead bot looking healthy.
    t = Thread(target=run, daemon=True)
    t.start()
    print("[DEBUG] Keep-alive server started.")
