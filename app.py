import os
import logging
from flask import Flask, request, jsonify
from instagrapi import Client

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)


# Function to login to Instagram
def login(username, password):
    client = Client()
    try:
        # Attempt login with username and password
        client.login(username, password)
    except Exception as e:
        logging.error(f"Login failed: {e}")
        if 'Two-Factor Authentication' in str(e):
            # Handle 2FA using environment variable
            code = os.getenv('INSTAGRAM_2FA_CODE')  # Get 2FA code from environment variable
            if code:
                client.login(username, password, 2fa_code=code)
            else:
                raise Exception("2FA code not provided via environment variable.")
    return client


# Function to get followers of a target username
def get_followers_list(client, target_username):
    user_id = client.user_id_from_username(target_username)
    followers = client.user_followers(user_id)
    return [follower.pk for follower in followers]


# Function to send DMs to all followers
def send_bulk_dms(client, message, followers_list):
    try:
        for follower in followers_list:
            client.direct_send(message, user_ids=[follower])
            logging.info(f"DM sent to {follower}")
    except Exception as e:
        logging.error(f"Error sending DM: {e}")
        raise Exception("Error when sending bulk DMs.")


# Flask route to handle DM sending
@app.route('/send_dms', methods=['POST'])
def send_dms():
    try:
        # Get the data from the POST request
        username = request.form.get('username')
        password = request.form.get('password')
        message = request.form.get('message')
        target_username = request.form.get('target_username')

        if not username or not password or not message or not target_username:
            return jsonify({"error": "Missing required fields"}), 400

        # Login to Instagram
        client = login(username, password)

        # Get followers list
        followers_list = get_followers_list(client, target_username)

        # Send DMs to all followers
        send_bulk_dms(client, message, followers_list)

        return jsonify({"success": "DMs sent successfully!"}), 200

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


# Running the Flask application
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
