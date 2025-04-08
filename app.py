from flask import Flask, render_template, request
from instagrapi import Client
import time  # for adding delay between messages

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
    message = request.form['message']  # The message to send
    delay_time = int(request.form['delay_time'])  # Delay time in seconds between each DM
    two_factor_code = request.form.get('two_factor_code', '').strip()  # Optional 2FA code

    try:
        # Login to Instagram
        client.login(username, password, two_factor_code=two_factor_code)

        # Get the target account's followers or following
        target_user_id = client.user_id_from_username(target_account)

        if target == 'followers':
            target_list = client.user_followers(target_user_id)
        elif target == 'following':
            target_list = client.user_following(target_user_id)

        # Ensure we don't send messages to more than the specified count
        target_list = target_list[:message_count]

        # Send messages with delay
        for user in target_list:
            client.direct_send(message, [user.username])
            print(f"Sent DM to {user.username}")  # Optional print for logging
            time.sleep(delay_time)  # Add the delay between messages

        return f"DMs sent successfully to {len(target_list)} accounts!"

    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Makes the app accessible externally
