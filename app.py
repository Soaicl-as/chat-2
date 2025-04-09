from flask import Flask, request, render_template, redirect, url_for
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, TwoFactorRequired, ChallengeRequired
import threading
import time
import os

app = Flask(__name__)
session = {
    "client": None,
    "username": "",
    "password": "",
    "target": "",
    "message": "",
    "mode": "followers",
    "limit": 10,
    "delay": 5,
    "login_status": "",
    "challenge_required": False,
    "login_attempt_in_progress": False
}


def try_login():
    session["client"] = Client()
    session["client"].delay_range = [1, 3]

    try:
        session["client"].login(session["username"], session["password"])
        session["login_status"] = "Logged in"
        session["challenge_required"] = False
        session["login_attempt_in_progress"] = False
    except ChallengeRequired:
        session["login_status"] = "Login challenge required. Please approve the login in your Instagram app or browser."
        session["challenge_required"] = True
        session["login_attempt_in_progress"] = True
    except TwoFactorRequired:
        session["login_status"] = "2FA code required but not provided."
        session["challenge_required"] = False
        session["login_attempt_in_progress"] = False
    except Exception as e:
        session["login_status"] = f"Login failed: {str(e)}"
        session["login_attempt_in_progress"] = False


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        session["username"] = request.form["username"]
        session["password"] = request.form["password"]
        session["target"] = request.form["target"]
        session["message"] = request.form["message"]
        session["mode"] = request.form["mode"]
        session["limit"] = int(request.form["limit"])
        session["delay"] = int(request.form["delay"])

        threading.Thread(target=try_login).start()
        return redirect(url_for("status"))

    return render_template("index.html")


@app.route("/status")
def status():
    return render_template("status.html", status=session["login_status"])


@app.route("/check_secure_account")
def check_secure_account():
    if session["challenge_required"] and session["login_attempt_in_progress"]:
        threading.Thread(target=try_login).start()
        return "Retrying login after approval..."
    return "No pending login challenge."


@app.route("/send_dms")
def send_dms():
    cl = session.get("client")
    if not cl or not cl.user_id:
        return "Error: Not logged in."

    try:
        user_id = cl.user_id_from_username(session["target"])
        if session["mode"] == "followers":
            users = cl.user_followers(user_id, amount=session["limit"])
        else:
            users = cl.user_following(user_id, amount=session["limit"])

        for i, user in enumerate(users.values()):
            cl.direct_send(session["message"], [user.pk])
            time.sleep(session["delay"])
        return f"DMs sent to {len(users)} users."

    except LoginRequired:
        return "Error: Instagram session expired. Please log in again."
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
