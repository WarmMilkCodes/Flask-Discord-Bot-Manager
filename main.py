from flask import Flask, render_template, request, redirect, url_for, json, Response
import subprocess
import config
import psutil

app = Flask(__name__)

# define username and password
username = config.user_name
password = config.password

# define bots pm2 process IDs
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
    cmd = "pm2 jlist"
    result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
    output = result.stdout.decode('utf-8')

    # parse the JSON output and get the status of each bot
    bot_statuses = []
    for bot in json.loads(output):
        # get CPU and memory usage for the bot process
        pid = bot['pid']
        cpu_usage = psutil.Process(pid).cpu_percent()
        memory_usage = psutil.Process(pid).memory_percent()

        bot_statuses.append({
            'name': bot['name'],
            'status': bot['pm2_env']['status'],
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage
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

    # get pm2 process ID for bot
    process_id = bot_processes[bot_name]

    # tail the log file for pm2 process
    log_process = subprocess.Popen(['pm2', 'logs', str(process_id)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # function to generate SSE events from log output
    def log_events():
        while True:
            line = log_process.stdout.readline()
            if not line:
                break
            yield 'data: %s\n\n' % line.decode('utf-8')

    # return response with SSE headers and event generator function
    return Response(log_events(), mimetype='text/event-stream')

    if request.method == 'POST':
        selected_bot = request.form['bot']
        logs = subprocess.check_output(['pm2', 'logs', '--lines', '100', selected_bot]).decode('utf-8')
        return render_template('logs.html', bots=['bot1', 'bot2', 'bot3'], logs=logs, selected_bot=selected_bot)
    else:
        return render_template('logs.html', bots=['bot1', 'bot2', 'bot3'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
