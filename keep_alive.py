from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def keep_alive():
    from threading import Thread
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
