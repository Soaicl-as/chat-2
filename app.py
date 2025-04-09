import os
from flask import Flask, render_template, request, session, redirect, url_for
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired
from instagrapi.types import User
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Flask session secret key

# Instagram client setup
client = Client()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Attempt to login
        try:
            client.login(username, password)

            # If login is successful, proceed to dashboard
            return redirect(url_for("dashboard"))
        except TwoFactorRequired as e:
            # Store the two-factor identifier so we can complete it later
            session["two_factor_identifier"] = e.two_factor_identifier
            return redirect(url_for("verify_2fa"))
        except Exception as e:
            return f"Login failed: {str(e)}"
    
    return render_template("login.html")

@app.route("/verify_2fa", methods=["GET", "POST"])
def verify_2fa():
    if request.method == "POST":
        verification_code = request.form.get("verification_code")
        two_factor_identifier = session.get("two_factor_identifier")

        if two_factor_identifier:
            try:
                # Try completing the 2FA with the verification code
                client.complete_two_factor_login(two_factor_identifier, verification_code)

                # After completing 2FA, you will be logged in and can proceed to the dashboard
                return redirect(url_for("dashboard"))
            except Exception as e:
                return f"Error completing 2FA: {str(e)}"
    
    return render_template("verify_2fa.html")

@app.route("/dashboard")
def dashboard():
    try:
        # Example: Fetch and display the user's followers or any info
        user_info = client.user_info(client.user_id)
        followers = client.user_followers(client.user_id)
        return render_template("dashboard.html", user_info=user_info, followers=followers)
    except Exception as e:
        return f"Error fetching data: {str(e)}"

@app.route("/send_dm", methods=["POST"])
def send_dm():
    message = request.form.get("message")
    target_account = request.form.get("target_account")

    try:
        # Fetch the user by username
        target_user = client.user_info_by_username(target_account)
        client.direct_send(message, [target_user.pk])
        return redirect(url_for("dashboard"))
    except Exception as e:
        return f"Error sending DM: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
