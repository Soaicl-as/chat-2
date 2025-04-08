from flask import Flask, render_template, request, redirect, url_for, session
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired, ChallengeRequired
import time
import threading

app = Flask(__name__)
app.secret_key = 'your_secret_key'
client = Client()
login_in_progress = False

def send_dms(client, users, message, delay):
    for user in users:
        try:
            client.direct_send(message, [user.pk])
            print(f"DM sent to {user.username}")
        except Exception as e:
            print(f"Failed to DM {user.username}: {e}")
        time.sleep(delay)

@app.route("/", methods=["GET", "POST"])
def index():
    global login_in_progress

    if request.method == "POST":
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
        except ChallengeRequired as e:
            session['challenge_url'] = e.challenge_url
            return render_template("verify.html", error=None)
        except TwoFactorRequired:
            return render_template("error.html", error="2FA code required but not provided.")
        except Exception as e:
            login_in_progress = False
            return render_template("error.html", error=f"Login failed: {str(e)}")

        return redirect("/start")

    return render_template("index.html")

@app.route("/start")
def start():
    target_username = session.get("target_username")
    amount = session.get("amount")
    relationship = session.get("relationship")

    try:
        user_id = client.user_id_from_username(target_username)
        if relationship == "followers":
            users = client.user_followers(user_id, amount=amount)
        else:
            users = client.user_following(user_id, amount=amount)

        users = list(users.values())
        message = session.get("message")
        delay = session.get("delay")

        threading.Thread(target=send_dms, args=(client, users, message, delay)).start()
        return "DMs are being sent in the background."

    except Exception as e:
        return render_template("error.html", error=f"Failed to fetch users or send DMs: {e}")

@app.route("/verify", methods=["POST"])
def verify():
    try:
        client.challenge_resolve()
        print("Account unlocked")
        return redirect("/auto_retry_login")
    except Exception as e:
        return render_template("error.html", error=f"Challenge resolution failed: {str(e)}")

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
    except Exception as e:
        login_in_progress = False
        return render_template("error.html", error=f"Auto-login retry failed: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
