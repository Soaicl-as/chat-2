import os
import time
from instagrapi import Client
from flask import Flask, render_template_string, request, session
from instagrapi.exceptions import TwoFactorRequired
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)

HTML_2FA = """
<!DOCTYPE html>
<html>
    <head>
        <title>Instagram 2FA</title>
    </head>
    <body>
        <h2>Instagram 2FA Authentication</h2>
        <form method="POST" action="/verify_2fa">
            <label for="code">Enter the 2FA code you received:</label>
            <input type="text" id="code" name="code" required>
            <input type="submit" value="Submit">
        </form>
    </body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        session['username'] = username
        session['password'] = password

        client = Client()

        try:
            # Login attempt
            client.login(username, password)
        except TwoFactorRequired as e:
            try:
                # Attempt to handle 2FA by extracting the required data
                if e.response is None:
                    return "<h3>Error: Instagram did not send a valid response.</h3>"

                error_data = json.loads(e.response.text)
                two_factor_info = error_data.get("two_factor_info", {})
                session['two_factor_identifier'] = two_factor_info.get("two_factor_identifier")
                
                if not session['two_factor_identifier']:
                    return "<h3>2FA failed: Missing two_factor_identifier from Instagram.</h3>"
                
                # Render 2FA input form
                return render_template_string(HTML_2FA)
            except Exception as ex:
                return f"<h3>Failed to extract 2FA info: {str(ex)}</h3>"

        except Exception as e:
            return f"<h3>Login failed: {str(e)}</h3>"

        return "<h3>Login successful!</h3>"

    return '''
        <form method="POST">
            <label for="username">Username:</label><br>
            <input type="text" id="username" name="username" required><br><br>
            <label for="password">Password:</label><br>
            <input type="password" id="password" name="password" required><br><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/verify_2fa', methods=['POST'])
def verify_2fa():
    verification_code = request.form['code']
    two_factor_identifier = session.get('two_factor_identifier')

    if not two_factor_identifier:
        return "<h3>2FA identifier missing, unable to verify.</h3>"

    client = Client()

    try:
        # Attempt login with 2FA
        client.complete_two_factor_login(
            two_factor_identifier,
            verification_code
        )
        return "<h3>2FA Authentication successful!</h3>"

    except Exception as e:
        return f"<h3>2FA failed: {str(e)}</h3>"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
