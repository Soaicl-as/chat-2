from flask import Flask, render_template, request, redirect, url_for
from instagrapi import Client

app = Flask(__name__)

# Your login details (can be entered in the form)
username = ""
password = ""

# Initialize the Instagram client
client = Client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_dms', methods=['POST'])
def send_dms():
    global username, password

    # Get the input values from the form
    username = request.form['username']
    password = request.form['password']
    two_factor_code = request.form['two_factor_code']
    target = request.form['target']

    # Attempt to login
    try:
        client.login(username, password, 2fa_code=two_factor_code)
        
        # Choose between followers or following based on the user's selection
        if target == 'followers':
            # Code for sending DMs to followers
            # Example: client.user_followers(user_id)
            print(f"Sending DMs to {username}'s followers...")

        elif target == 'following':
            # Code for sending DMs to following
            # Example: client.user_following(user_id)
            print(f"Sending DMs to {username}'s following...")

        return "DMs sent successfully!"

    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Makes the app accessible externally
