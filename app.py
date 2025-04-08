from flask import Flask, render_template_string, request, redirect, url_for, session
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired
import time
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

HTML_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Instagram DM Sender</title>
</head>
<body>
    <h1>Instagram DM Sender</h1>
    <form method="POST">
        <label>Instagram Username:</label><br>
        <input type="text" name="username" required><br><br>

        <label>Instagram Password:</label><br>
        <input type="password" name="password" required><br><br>

        <label>Account to Pull Followers/Following from:</label><br>
        <input type="text" name="account" required><br><br>

        <label>Message to Send:</label><br>
        <textarea name="message" required></textarea><br><br>

        <label>Message Followers or Following:</label><br>
        <select name="followers_or_following" required>
            <option value="followers">Followers</option>
            <option value="following">Following</option>
        </select><br><br>

        <label>Number of Accounts to Message:</label><br>
        <input type="number" name="num_accounts" min="1" required><br><br>

        <label>Delay Between Messages (seconds):</label><br>
        <input type="number" name="delay" step="0.1" min="0.1" required><br><br>

        <button type="submit">Send DMs</button>
    </form>
</body>
</html>
"""

HTML_2FA = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Enter 2FA Code</title>
</head>
<body>
    <h1>Two-Factor Authentication Required</h1>
    <form method="POST">
        <label>Enter 2FA Code:</label><br>
        <input type="text" name="verification_code" required><br><br>
        <button type="submit">Verify</button>
    </form>
</body>
</html>
"""

client = Client()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'verification_code' in request.form:
            verification_code = request.form['verification_code']
            try:
                client.login(
                    session['username'],
                    session['password'],
                    verification_code=verification_code,
                    two_factor_identifier=session['two_factor_identifier']
                )
                return redirect(url_for('send_dms'))
            except Exception as e:
                return f"<h3>2FA failed: {str(e)}</h3>"

        session['username'] = request.form['username']
        session['password'] = request.form['password']
        session['account'] = request.form['account']
        session['message'] = request.form['message']
        session['followers_or_following'] = request.form['followers_or_following']
        session['num_accounts'] = int(request.form['num_accounts'])
        session['delay'] = float(request.form['delay'])

        try:
            client.login(session['username'], session['password'])
            return redirect(url_for('send_dms'))
        except TwoFactorRequired as e:
            session['two_factor_identifier'] = e.two_factor_identifier
            return render_template_string(HTML_2FA)
        except Exception as e:
            return f"<h3>Login failed: {str(e)}</h3>"

    return render_template_string(HTML_FORM)

@app.route('/send_dms')
def send_dms():
    account = session['account']
    message = session['message']
    target_type = session['followers_or_following']
    num_accounts = session['num_accounts']
    delay = session['delay']

    try:
        user_id = client.user_id_from_username(account)
        if target_type == "followers":
            users = client.user_followers(user_id, amount=num_accounts)
        else:
            users = client.user_following(user_id, amount=num_accounts)

        count = 0
        for user in users.values():
            client.direct_send(message, [user.pk])
            count += 1
            time.sleep(delay)

        return f"<h3>Successfully messaged {count} users.</h3>"

    except Exception as e:
        return f"<h3>Error sending DMs: {str(e)}</h3>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
