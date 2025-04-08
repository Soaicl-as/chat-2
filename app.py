from flask import Flask, request, render_template_string
from instagrapi import Client
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
        <input type="text" name="username" required><br><br>

        <label>Instagram Password:</label><br>
        <input type="password" name="password" required><br><br>

        {% if show_2fa %}
        <label>Enter 2FA Code:</label><br>
        <input type="text" name="code" required><br><br>
        <input type="hidden" name="username" value="{{ saved_username }}">
        <input type="hidden" name="password" value="{{ saved_password }}">
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

        if step == "2fa":
            username = request.form["username"]
            password = request.form["password"]
            code = request.form["code"]
            client = clients.get(username)

            if not client:
                return "Session expired. Please restart."

            try:
                client.two_factor_login(code)
                return render_template_string(HTML_FORM, show_2fa=False)
            except Exception as e:
                return f"2FA failed: {e}"

        username = request.form["username"]
        password = request.form["password"]

        target_account = request.form.get("target_account")
        message = request.form.get("message")
        direction = request.form.get("direction")
        limit = int(request.form.get("limit", 1))
        delay = float(request.form.get("delay", 1.0))

        client = Client()

        try:
            client.login(username, password)
        except Exception as e:
            if "two-factor authentication is required" in str(e).lower():
                clients[username] = client
                return render_template_string(HTML_FORM, show_2fa=True, saved_username=username, saved_password=password)
            return f"Login failed: {e}"

        try:
            user_id = client.user_id_from_username(target_account)
            if direction == "followers":
                users = client.user_followers(user_id, amount=limit)
            else:
                users = client.user_following(user_id, amount=limit)

            for user in users.values():
                client.direct_send(message, [user.pk])
                time.sleep(delay)

            return "Messages sent successfully."
        except Exception as e:
            return f"An error occurred while sending DMs: {e}"

    return render_template_string(HTML_FORM, show_2fa=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
