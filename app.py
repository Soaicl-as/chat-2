from flask import Flask, render_template, request, redirect, session
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, TwoFactorRequired
import time
import threading
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)


def try_login():
    session["client"] = Client()
    session["client"].delay_range = [1, 3]
    session["login_attempt_in_progress"] = True

    try:
        session["client"].login(session["username"], session["password"])
        session["login_status"] = "✅ Logged in successfully."
        session["challenge_required"] = False
    except ChallengeRequired:
        session["login_status"] = (
            "⚠️ Login challenge required. Please approve in your Instagram app or browser."
        )
        session["challenge_required"] = True
    except TwoFactorRequired:
        session["login_status"] = (
            "❌ 2FA code required but not supported in this flow."
        )
        session["challenge_required"] = False
    except Exception as e:
        if "429" in str(e):
            session["login_status"] = "⏳ Too many requests. Waiting 10 seconds before retry..."
            time.sleep(10)
            try_login()
        else:
            session["login_status"] = f"❌ Login failed: {str(e)}"
    finally:
        session["login_attempt_in_progress"] = False


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        session["username"] = request.form["username"]
        session["password"] = request.form["password"]
        session["target_user"] = request.form["target_user"]
        session["target_type"] = request.form["target_type"]
        session["message"] = request.form["message"]
        session["max_users"] = int(request.form["max_users"])
        session["delay"] = float(request.form["delay"])

        session["login_status"] = "🔄 Logging in..."
        threading.Thread(target=try_login).start()

        return redirect("/status")

    return render_template("index.html")


@app.route("/status")
def status():
    return render_template("status.html", status=session.get("login_status", "No login attempt yet."))


@app.route("/check_secure_account")
def check_secure_account():
    if session.get("challenge_required") and not session.get("login_attempt_in_progress"):
        session["login_status"] = "🔄 Retrying login after browser approval..."
        threading.Thread(target=try_login).start()
        return "Triggered retry..."
    return "Waiting for challenge approval or login in progress."


@app.route("/send_dms")
def send_dms():
    if "client" not in session:
        return "❌ Not logged in."

    cl: Client = session["client"]
    target_user = session["target_user"]
    message = session["message"]
    max_users = session["max_users"]
    delay = session["delay"]

    try:
        user_id = cl.user_id_from_username(target_user)

        if session["target_type"] == "followers":
            users = cl.user_followers(user_id)
        else:
            users = cl.user_following(user_id)

        count = 0
        for uid, user in users.items():
            if count >= max_users:
                break
            cl.direct_send(message, [uid])
            count += 1
            time.sleep(delay)

        return f"✅ Sent messages to {count} users."

    except Exception as e:
        return f"❌ Failed to send messages: {str(e)}"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
