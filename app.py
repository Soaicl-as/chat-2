from flask import Flask, render_template_string, request, session, redirect
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")

HTML_FORM = '''
<!DOCTYPE html>
<html>
<head><title>Instagram Mass DM</title></head>
<body>
  <h2>Send Mass DMs</h2>
  <form method="POST">
    <label>Username:</label><br><input type="text" name="username" required><br>
    <label>Password:</label><br><input type="password" name="password" required><br>
    <label>Target Account:</label><br><input type="text" name="target_account" required><br>
    <label>Message:</label><br><textarea name="message" required></textarea><br>
    <label>Number of Accounts to Message:</label><br><input type="number" name="num_accounts" value="10" min="1"><br>
    <label>Target:</label><br>
    <select name="target_type">
      <option value="following">Following</option>
      <option value="followers">Followers</option>
    </select><br><br>
    <input type="submit" value="Send DMs">
  </form>
</body>
</html>
'''

HTML_2FA = '''
<!DOCTYPE html>
<html>
<head><title>2FA Verification</title></head>
<body>
  <h2>Enter 2FA Code</h2>
  <form method="POST" action="/2fa">
    <label>Verification Code:</label><br>
    <input type="text" name="verification_code" required><br><br>
    <input type="submit" value="Verify 2FA">
  </form>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session['username'] = request.form['username']
        session['password'] = request.form['password']
        session['target_account'] = request.form['target_account']
        session['message'] = request.form['message']
        session['num_accounts'] = int(request.form['num_accounts'])
        session['target_type'] = request.form['target_type']

        client = Client()
        try:
            client.login(session['username'], session['password'])
        except TwoFactorRequired as e:
            try:
                two_factor_info = e.last_json.get("two_factor_info", {})
                session['two_factor_identifier'] = two_factor_info.get("two_factor_identifier")
                if not session['two_factor_identifier']:
                    return "<h3>2FA failed: Missing two_factor_identifier from Instagram.</h3>"
                return render_template_string(HTML_2FA)
            except Exception as ex:
                return f"<h3>Failed to extract 2FA info: {str(ex)}</h3>"

        return send_dms(client)

    return render_template_string(HTML_FORM)

@app.route('/2fa', methods=['POST'])
def handle_2fa():
    verification_code = request.form['verification_code']
    client = Client()
    try:
        client.login(
            session['username'],
            session['password'],
            verification_code=verification_code,
            two_factor_identifier=session['two_factor_identifier']
        )
    except Exception as e:
        return f"<h3>2FA failed: {str(e)}</h3>"

    return send_dms(client)

def send_dms(client):
    account = session['target_account']
    message = session['message']
    num_accounts = session['num_accounts']
    target_type = session['target_type']

    try:
        user_id = client.user_id_from_username(account)
        if target_type == 'followers':
            users = client.user_followers(user_id, amount=num_accounts)
        else:
            users = client.user_following(user_id, amount=num_accounts)

        usernames = [user.username for user in users.values()]
        results = []
        for username in usernames:
            try:
                recipient_id = client.user_id_from_username(username)
                client.direct_send(message, [recipient_id])
                results.append(f"✅ Sent to {username}")
            except Exception as dm_error:
                results.append(f"❌ Failed to send to {username}: {str(dm_error)}")

        return '<br>'.join(results)

    except Exception as main_error:
        return f"<h3>Error: {str(main_error)}</h3>"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
