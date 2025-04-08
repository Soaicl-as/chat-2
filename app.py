from flask import Flask, render_template, request, redirect, url_for
from instagrapi import Client
import time

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Getting data from the form
        username = request.form['username']
        password = request.form['password']
        account = request.form['account']
        message = request.form['message']
        followers_or_following = request.form['followers_or_following']
        num_accounts = int(request.form['num_accounts'])
        delay = float(request.form['delay'])

        # Initialize Instagram client
        client = Client()

        try:
            # Attempt to login
            client.login(username, password)
        except Exception as e:
            # If login fails and requires 2FA, prompt for the 2FA code
            if 'two_factor' in str(e).lower():
                two_factor_code = input("Enter the 2FA code sent to your phone: ")
                client.login(username, password, two_factor_code=two_factor_code)

        # Get the list of followers or following from the specified account
        if followers_or_following == 'followers':
            users = client.user_followers(account, amount=num_accounts)
        else:
            users = client.user_following(account, amount=num_accounts)

        # Send messages to the selected accounts
        for user in users:
            try:
                client.direct_send(message, user.pk)
                print(f"Message sent to {user.username}")
                time.sleep(delay)  # Add delay between messages
            except Exception as e:
                print(f"Error sending message to {user.username}: {str(e)}")

        return "DMs have been sent!"

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
