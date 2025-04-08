from flask import Flask, request, render_template_string
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired
import time

app = Flask(__name__)

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
        <input type="text" name="username" value="{{ saved_username or '' }}" required><br><br>

        <label>Instagram Password:</label><br>
        <input type="password" name="password" value="{{ saved_password or '' }}" required><br><br>

        {% if show_2fa %}
        <label>Enter 2FA Code:</label><br>
        <input type="text" name="code" required><br><br>
        <input type="hidden" name="step" value="2fa">
        <button type="submit">Verify 2FA</button>
        {% else %}
        <label>Account to Pull From:</label><br>
        <input type="text" name="target_account" required><br><br>

        <label>Message to Send:</label><br>
        <textarea name="message" required></textarea><br><br>

        <label>Choose Followers or Following:</label><br>
        <select name="direction" required>
            <option value="followers">Followers</option>
            <option value="following">Following</option>
        </select><br><br>

        <label>Number of People to Message:</label><br>
        <input type="number" name="limit" min="1" required><br><br>

        <label>Delay Between Messages (seconds):</label><br>
        <input type="number" step="0.1" name="delay" required><br><br>

        <button type="submit">Send DMs</button>
        {% endif %}
    </form>
</body>
</html>
"""

clients = {}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        step = request.form.get("step")
        username = request.form["username"]
        password = request.form["password"]

        if step == "2fa":
            code = request.form["code"]
            client = clients.get(username)

            if not client:
                return "Session expired. Please restart."

            try:
                client.complete_two_factor_login(code)
                return "2FA successful. You can now restart and send DMs."
            except Exception as e:
                return f"2FA failed: {e}"

        # Otherwise: initial login attempt
        client = Client()
        try:
            client.login(username, password)
        except TwoFactorRequired:
            clients[username] = client
            return render_template_string(HTML_FORM, show_2fa=True, saved_username=username, saved_password=password)
        except Exception as e:
            return f"Login failed: {e}"

        # Continue to message sending
        target_account = request.form["target_account"]
        message = request.form["message"]
        direction = request.form["direction"]
        limit = int(request.form["limit"])
        delay = float(request.form["delay"])

        try:
            user_id = client.user_id_from_username(target_account)
            if direction == "followers":
                users = client.user_followers(user_id, amount=limit)
            else:
                users = client.user_following(user_id, amount=limit)

            for user in users.values():
                client.direct_send(message, [user.pk])
                time.sleep(delay)

            return "Messages sent successfully!"
        except Exception as e:
            return f"An error occurred while sending DMs: {e}"

    return render_template_string(HTML_FORM, show_2fa=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
