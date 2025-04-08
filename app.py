import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

from flask import Flask, render_template, request
from dm_bot import send_bulk_dms

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = {
            'username': request.form['username'],
            'password': request.form['password'],
            'target_user': request.form['target_user'],
            'message': request.form['message'],
            'limit': int(request.form['limit']),
            'delay': float(request.form['delay']),
            'mode': request.form['mode']
        }
        response = send_bulk_dms(**data)
        return render_template('index.html', response=response)
    return render_template('index.html', response=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
