import time
import threading
import os
from flask import Flask, render_template, request, redirect, url_for, session
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired
from werkzeug.local import LocalProxy

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Session to store Instagram client
client = LocalProxy(lambda: session.get('client'))

# Home route, displays login form
@app.route('/')
def home():
    return render_template('index.html')

# Handle login form submission
@app.route('/', methods=["POST"])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return "Please provide both username and password.", 400

    # Initialize the client and attempt login
    try:
        session["client"] = Client()
        client.login(username, password)
        return redirect(url_for('status'))
    except TwoFactorRequired as e:
        session['two_factor_identifier'] = e.two_factor_identifier
        return redirect(url_for('verify'))
    except Exception as e:
        return f"An error occurred: {e}", 500

# Status route to show the current login status
@app.route('/status')
def status():
    if client:
        return render_template('status.html', logged_in=True)
    return render_template('status.html', logged_in=False)

# Handle 2FA verification page
@app.route('/verify', methods=["POST", "GET"])
def verify():
    if request.method == 'POST':
        code = request.form.get('code')

        if not code:
            return "Please provide a 2FA code.", 400

        try:
            # Attempt to complete 2FA using the code
            client.complete_two_factor_login(code, session['two_factor_identifier'])
            return redirect(url_for('status'))
        except Exception as e:
            return f"Failed to verify 2FA: {e}", 500

    return render_template('verify.html')

# Send DMs route
@app.route('/send_dms', methods=["GET"])
def send_dms():
    if not client:
        return redirect(url_for('home'))

    # Send DMs logic
    target_account = request.args.get('target_account')
    if not target_account:
        return "Please provide a target account.", 400

    # Send DMs to followers or following
    try:
        users = client.user_following(target_account)
        for user in users:
            client.direct_send("Hello!", [user.pk])  # Example message
        return "DMs sent successfully."
    except Exception as e:
        return f"An error occurred while sending DMs: {e}", 500

# Threaded function to continuously check login and handle retries
def try_login():
    while True:
        try:
            if client and client.is_logged_in:
                break  # Stop the loop if logged in
            time.sleep(5)  # Retry after 5 seconds
        except Exception as e:
            print(f"Error in try_login: {e}")
            time.sleep(5)

# Run the Flask app
if __name__ == '__main__':
    threading.Thread(target=try_login, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
