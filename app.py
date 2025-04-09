from flask import Flask, render_template, request, redirect, session
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, TwoFactorRequired
import time
import threading
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "very_secret")

client = Client()
login_in_progress = False


@app.route("/", methods=["GET", "POST"])
def index():
    global login_in_progress

    if request.method == "POST":
        # Save form input to session
        session['username'] = request.form["username"]
        session['password'] = request.form["password"]
        session['target_username'] = request.form["target_username"]
        session['message'] = request.form["message"]
        session['amount'] = int(request.form["amount"])
        session['delay'] = float(request.form["delay"])
        session['relationship'] = request.form["relationship"]

        try:
            login_in_progress = True
            client.login(session['username'], session['password'])
            login_in_progress = False
            return redirect("/start")

        except ChallengeRequired as e:
            session['challenge_url'] = e.challenge_url
            return render_template("verify.html", error=None)

        except TwoFactorRequired:
            session['2fa_pending'] = True
            return render_template("waiting_for_approval.html")

        except Exception as e:
            login_in_progress = False
            return render_template("error.html", error=f"Login failed: {str(e)}")

    return render_template("index.html")


@app.route("/auto_retry_login")
def auto_retry_login():
    global login_in_progress
    if login_in_progress:
        return "Login is already in progress, please wait."

    try:
        login_in_progress = True
        client.login(session['username'], session['password'])
        login_in_progress = False
        return redirect("/start")
    except TwoFactorRequired:
        login_in_progress = False
        return render_template("waiting_for_approval.html")
    except Exception as e:
        login_in_progress = False
        return render_template("error.html", error=f"Retry failed: {str(e)}")


@app.route("/start")
def start():
    target_username = session["target_username"]
    message = session["message"]
    amount = session["amount"]
    delay = session["delay"]
    relationship = session["relationship"]

    try:
        if relationship == "followers":
            users = client.user_followers(client.user_id_from_username(target_username), amount)
        else:
            users = client.user_following(client.user_id_from_username(target_username), amount)

        usernames = list(users.values())[:amount]

        def send_messages():
            for user in usernames:
                try:
                    client.direct_send(message, [user.pk])
                    print(f"Sent to {user.username}")
                    time.sleep(delay)
                except Exception as e:
                    print(f"Failed to send to {user.username}: {e}")

        threading.Thread(target=send_messages).start()

        return render_template("success.html", usernames=[u.username for u in usernames])

    except Exception as e:
        return render_template("error.html", error=f"Failed to fetch users or send messages: {str(e)}")


@app.route("/verify", methods=["POST"])
def verify():
    code = request.form["code"]
    try:
        client.challenge_resolve(session['challenge_url'])
        client.challenge_send_code(session['challenge_url'])
        client.challenge_code_submit(session['challenge_url'], code)
        return redirect("/start")
    except Exception as e:
        return render_template("verify.html", error=f"Challenge failed: {str(e)}")
