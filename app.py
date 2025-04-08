from flask import Flask, render_template, request, redirect, url_for
from instagrapi import Client

app = Flask(__name__)

# Initialize the Instagram client
client = Client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_dms', methods=['POST'])
def send_dms():
    # Get the input values from the form
    username = request.form['username']
    password = request.form['password']
    target_account = request.form['target_account']
    message_count = int(request.form['message_count'])  # Number of accounts to message
    target = request.form['target']  # Followers or following
    two_factor_code = request.form.get('two_factor_code', '').strip()  # Optional 2FA code

    # Attempt to login
    try:
        # Login to Instagram
        client.login(username, password, two_factor_code=two_factor_code)

        # Get the target account's followers or following
        target_user_id = client.user_id_from_username(target_account)

        # Fetch the followers or following based on the selected option
        if target == 'followers':
            target_list = client.user_followers(target_user_id)
        elif target == 'following':
            target_list = client.user_following(target_user_id)

        # Ensure we don't send messages to more than the specified count
        target_list = target_list[:message_count]

        # Send messages to the selected accounts
        for user in target_list:
            client.direct_send("Hello from the bot!", [user.username])

        return f"DMs sent successfully to {len(target_list)} accounts!"

    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Makes the app accessible externally
