from instagrapi import Client
from instagrapi.exceptions import LoginRequired

def login(username, password):
    cl = Client()
    try:
        cl.login(username, password)
    except LoginRequired:
        cl.relogin()
    return cl
