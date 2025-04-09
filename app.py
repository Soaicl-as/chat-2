from flask import Flask, render_template, request, redirect, session, url_for
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired

app = Flask(__name__)

# Replace this with the generated secret key
app.secret_key = 'cba548b8096f4e348adfca99fcedd66b'  # Random 24-byte key (example)

client = Client()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            # Attempt login
            client.login(username, password)

            # If login is successful, return to a new route (e.g., dashboard)
            return redirect(url_for('dashboard'))

        except TwoFactorRequired as e:
            # If 2FA is required, handle it by storing the identifier in the session
            session['two_factor_identifier'] = e.two_factor_identifier
            return render_template('two_factor.html', identifier=e.two_factor_identifier)

        except Exception as e:
            # Catch any other exceptions and return an error page
            return render_template('error.html', message=str(e))

    return render_template("login.html")

@app.route("/two_factor", methods=["POST"])
def two_factor():
    # Check if a 2FA identifier is present in session
    identifier = session.get('two_factor_identifier')

    if identifier:
        verification_code = request.form["verification_code"]
        try:
            # Attempt to complete the login with the verification code
            client.complete_two_factor_login(identifier, verification_code)

            # If 2FA is successful, redirect to the dashboard or home page
            return redirect(url_for('dashboard'))

        except Exception as e:
            return render_template('error.html', message=str(e))

    return redirect(url_for('login'))

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")  # Replace with the actual dashboard page

if __name__ == "__main__":
    app.run(debug=True)
