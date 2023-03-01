from flask import Flask, render_template, request, redirect, url_for, json
import subprocess
import config

app = Flask(__name__)

# define username and password
username = config.user_name
password = config.password

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    # get the entered username and password
    entered_username = request.form['username']
    entered_password = request.form['password']

    # check if the entered username and password are correct
    if entered_username == username and entered_password == password:
        return redirect(url_for('status'))
    else:
        return "Invalid username or password. Please try again."

@app.route('/status')
def status():
    # get the status of the bots
    cmd = "pm2 jlist"
    result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
    output = result.stdout.decode('utf-8')

    # parse the JSON output and get the status of each bot
    bot_statuses = []
    for bot in json.loads(output):
        bot_statuses.append({
            'name': bot['name'],
            'status': bot['pm2_env']['status']
        })

    return render_template('status.html', bot_statuses=bot_statuses)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
