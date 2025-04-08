import time
from instagrapi import Client
from flask import Flask, render_template, request

app = Flask(__name__)

def login_to_instagram(username, password):
    client = Client()
    
    try:
        # Attempt to login without 2FA first
        client.login(username, password)
        print("Logged in successfully without 2FA.")
    
    except Exception as e:
        if "Please enter the code" in str(e):
            # This exception indicates that 2FA is required
            print("2FA required. Please check your phone for the code.")
            two_factor_code = input("Enter 2FA code: ")
            
            # Now login again with the 2FA code
            client.login(username, password, two_factor_code=two_factor_code)
            print("Logged in successfully with 2FA.")
        else:
            print(f"An error occurred: {e}")

    return client

def send_messages(client, account, message, num_accounts, followers_or_following, delay):
    # Get the list of followers or following
    if followers_or_following == "followers":
        accounts = client.users_followers(account, amount=num_accounts)
    elif followers_or_following == "following":
        accounts = client.users_following(account, amount=num_accounts)
    else:
        print("Invalid choice for followers_or_following.")
        return
    
    # Send the message to the chosen accounts with a delay
    for account in accounts:
        client.direct_send(message, [account.pk])
        print(f"Sent message to {account.username}")
        time.sleep(delay)  # Adding delay between messages

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get form data
        username = request.form["username"]
        password = request.form["password"]
        account = request.form["account"]
        message = request.form["message"]
        followers_or_following = request.form["followers_or_following"]
        num_accounts = int(request.form["num_accounts"])
        delay = float(request.form["delay"])

        try:
            # Log in to Instagram
            client = login_to_instagram(username, password)

            # Send the messages
            send_messages(client, account, message, num_accounts, followers_or_following, delay)

            return "Messages sent successfully!"

        except Exception as e:
            return f"An error occurred: {e}"

    return render_template("index.html")  # This should render the HTML correctly

if __name__ == "__main__":
    app.run(debug=True)
