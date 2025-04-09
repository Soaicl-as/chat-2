from flask import Flask, render_template, request, redirect, session
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, TwoFactorRequired
import time
import threading
import os
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Global state dictionary to hold login sessions safely outside Flask's `session`
login_state = {}

def try_login(session_id):
    cl = Client()
    cl.delay_range = [1, 3]
    login_state[session_id]["status"] = "🔄 Attempting login..."

    try:
        cl.login(
            login_state[session_id]["username"],
            login_state[session_id]["password"]
        )
        login_state[session_id]["status"] = "✅ Logged in successfully."
        login_state[session_id]["client"] = cl
        login_state[session_id]["challenge_required"] = False

    except ChallengeRequired:
        login_state[session_id]["status"] = (
            "⚠️ Challenge required. Approve this login attempt in your Instagram app or browser."
        )
        login_state[session_id]["challenge_required"] = True

    except TwoFactorRequired:
        login_state[session_id]["status"] = (
            "❌ 2FA not handled here. Try a different account."
        )
        login_state[session_id]["challenge_required"] = False

    except Exception as e:
        if "429" in str(e):
            login_state[session_id]["status"] = "⏳ 429 Too Many Requests. Retrying in 10s..."
            time.sleep(10)
            try_login(session_id)
        else:
            login_state[session_id]["status"] = f"❌ Login failed: {str(e)}"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id

        login_state[session_id] = {
            "username": request.form["username"],
            "password": request.form["password"],
            "target_user": request.form["target_user"],
            "target_type": request.form["target_type"],
            "message": request.form["message"],
            "max_users": int(request.form["max_users"]),
            "delay": float(request.form["delay"]),
            "status": "🔄 Logging in...",
            "client": None,
            "challenge_required": False
        }

        threading.Thread(target=try_login, args=(session_id,)).start()
        return redirect("/status")

    return render_template("index.html")


@app.route("/status")
def status():
    session_id = session.get("session_id")
    if not session_id or session_id not in login_state:
        return "No login in progress."
    return render_template("status.html", status=login_state[session_id]["status"])


@app.route("/check_secure_account")
def check_secure_account():
    session_id = session.get("session_id")
    if not session_id or session_id not in login_state:
        return "Invalid session."

    if login_state[session_id]["challenge_required"]:
        login_state[session_id]["status"] = "🔁 Retrying login after browser confirmation..."
        threading.Thread(target=try_login, args=(session_id,)).start()
        return "Retrying..."

    return "No challenge or already in progress."


@app.route("/send_dms")
def send_dms():
    session_id = session.get("session_id")
    if not session_id or session_id not in login_state:
        return "Session not found."

    data = login_state[session_id]
    cl: Client = data.get("client")
    if not cl:
        return "❌ Not logged in yet."

    try:
        user_id = cl.user_id_from_username(data["target_user"])
        if data["target_type"] == "followers":
            users = cl.user_followers(user_id)
        else:
            users = cl.user_following(user_id)

        count = 0
        for uid, _ in users.items():
            if count >= data["max_users"]:
                break
            cl.direct_send(data["message"], [uid])
            count += 1
            time.sleep(data["delay"])

        return f"✅ DMs sent to {count} users."

    except Exception as e:
        return f"❌ Failed to send DMs: {str(e)}"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
