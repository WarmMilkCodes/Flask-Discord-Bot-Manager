from flask import Flask, render_template, request, redirect, url_for, json, Response
import subprocess
import config
import psutil

app = Flask(__name__)

# define username and password
username = config.user_name
password = config.password

# define bots systemctl
bot_processes = {
    'bot1':0,
    'bot2':1
}

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
    bot_statuses = []
    for bot_name in bot_processes:
        # get CPU and memory usage for the bot process
        cmd = f"systemctl status {bot_name}"
        result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
        output = result.stdout.decode('utf-8')

        bot_statuses.append({
            'name': bot_name,
            'status': 'running' if 'Active: active' in output else 'stopped',
            'cpu_usage': 0,  # replace with actual CPU usage
            'memory_usage': 0  # replace with actual memory usage
        })

    # get system-wide network activity
    net_io_counters = psutil.net_io_counters()
    network_stats = {
        'sent': net_io_counters.bytes_sent,
        'received': net_io_counters.bytes_recv
    }

    return render_template('status.html', bot_statuses=bot_statuses, network_stats=network_stats)


@app.route('/logs/<bot_name>')
def logs(bot_name):
    # check if bot exists
    if bot_name not in bot_processes:
        return f'{bot_name} not found', 404

    # get logs for bot
    cmd = f"journalctl -u {bot_name} -f"
    log_process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)

    # function to generate SSE events from log output
    def log_events():
        while True:
            line = log_process.stdout.readline()
            if not line:
                break
            yield 'data: %s\n\n' % line.decode('utf-8')

    # return response with SSE headers and event generator function
    return Response(log_events(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
