from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify
import requests
import time
import threading
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this-12345'

# Store application state
app_state = {
    'is_running': False,
    'start_time': datetime.now(),
    'total_messages_sent': 0,
    'total_users': 0,
    'active_users': 0,
    'logs': [],
    'stop_flag': threading.Event(),
    'bot_thread': None,
    'current_config': {}
}

# Admin credentials (change these)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# User database (simple file-based)
USER_FILE = 'users.json'

def load_users():
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
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
    if len(app_state['logs']) > 100:
        app_state['logs'].pop(0)
    print(f"[{timestamp}] {message}")

def send_messages_thread():
    try:
        thread_id = app_state['current_config'].get('thread_id')
        haters_name = app_state['current_config'].get('haters_name')
        time_interval = app_state['current_config'].get('time_interval', 60)
        access_tokens = app_state['current_config'].get('access_tokens', [])
        messages = app_state['current_config'].get('messages', [])
        
        if not all([thread_id, haters_name, access_tokens, messages]):
            add_log("Missing configuration data", 'error')
            app_state['is_running'] = False
            return
            
        post_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
        num_comments = len(messages)
        max_tokens = len(access_tokens)
        
        message_index = 0
        
        while app_state['is_running'] and not app_state['stop_flag'].is_set():
            try:
                for message_index in range(num_comments):
                    if not app_state['is_running'] or app_state['stop_flag'].is_set():
                        break
                        
                    token_index = message_index % max_tokens
                    access_token = access_tokens[token_index].strip()
                    
                    if not access_token:
                        continue
                    
                    message = messages[message_index].strip()
                    
                    if not message:
                        continue
                    
                    final_message = f"{haters_name} {message}"
                    
                    parameters = {
                        'access_token': access_token,
                        'message': final_message
                    }
                    
                    try:
                        response = requests.post(post_url, data=parameters, headers=headers, timeout=30)
                        
                        current_time = time.strftime("%Y-%m-%d %I:%M:%S %p")
                        
                        if response.status_code == 200:
                            app_state['total_messages_sent'] += 1
                            log_msg = f"[✓] SUCCESS - Message {message_index + 1} - Token {token_index + 1} - {final_message[:50]}"
                            add_log(log_msg, 'success')
                            print(f"[✓] SENT: {final_message}")
                        else:
                            error_text = response.text[:100] if response.text else "Unknown error"
                            log_msg = f"[✗] FAILED - Status {response.status_code} - {error_text}"
                            add_log(log_msg, 'error')
                            print(f"[✗] FAILED: {final_message} - {response.status_code}")
                            
                    except requests.exceptions.RequestException as e:
                        log_msg = f"[!] NETWORK ERROR - {str(e)[:100]}"
                        add_log(log_msg, 'error')
                        print(f"[!] ERROR: {str(e)}")
                    
                    time.sleep(time_interval)
                    
            except Exception as e:
                error_msg = f"Error in main loop: {str(e)}"
                add_log(error_msg, 'error')
                print(error_msg)
                time.sleep(30)
                
    except Exception as e:
        add_log(f"Thread error: {str(e)}", 'error')
        print(f"Thread error: {str(e)}")
    finally:
        app_state['is_running'] = False
        add_log("Bot thread stopped", 'info')

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚜️ 9MAN-x-YAMDHUD ⚜️</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, #800080 0%, #FF1493 50%, #FFD700 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: rgba(0, 0, 0, 0.9);
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
        
        .form-control, input[type="text"], input[type="number"], input[type="file"] {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid #FFD700;
            border-radius: 10px;
            color: #FFF;
            font-size: 14px;
        }
        
        .form-control:focus, input:focus {
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
            background: rgba(0, 0, 0, 0.95);
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
            font-size: 11px;
            word-wrap: break-word;
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
        
        .status-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .status-running {
            background: #00FF00;
            color: #000;
        }
        
        .status-stopped {
            background: #FF0000;
            color: #FFF;
        }
        
        .refresh-btn {
            background: #FFD700;
            color: #800080;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            margin-left: 10px;
        }
    </style>
    <script>
        function updateStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalMessages').innerText = data.total_messages;
                    document.getElementById('activeUsers').innerText = data.active_users;
                    const statusElem = document.getElementById('isRunning');
                    if (data.is_running) {
                        statusElem.innerHTML = '<span class="status-badge status-running">🟢 RUNNING</span>';
                    } else {
                        statusElem.innerHTML = '<span class="status-badge status-stopped">🔴 STOPPED</span>';
                    }
                    document.getElementById('uptime').innerText = data.uptime_days;
                })
                .catch(err => console.log('Stats error:', err));
        }
        
        function updateLogs() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    const logContainer = document.getElementById('liveLogs');
                    if (data.logs && data.logs.length > 0) {
                        logContainer.innerHTML = data.logs.slice().reverse().map(log => 
                            `<div class="log-entry log-${log.type}">[${log.time}] ${escapeHtml(log.message)}</div>`
                        ).join('');
                    } else {
                        logContainer.innerHTML = '<div class="log-entry">No logs yet...</div>';
                    }
                })
                .catch(err => console.log('Logs error:', err));
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        setInterval(updateStats, 3000);
        setInterval(updateLogs, 3000);
        
        function stopBot() {
            if(confirm('⚠️ Are you sure you want to stop the bot?')) {
                fetch('/api/stop', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        updateStats();
                    })
                    .catch(err => alert('Error: ' + err));
            }
        }
        
        // Initial load
        updateStats();
        updateLogs();
    </script>
</head>
<body>
<div class="container">
    <h1>⚜️ 9MAN-x-YAMDHUD ⚜️</h1>
    <h3>🔥 Advanced Facebook Message Bot 🔥</h3>
    
    <div class="nav-links">
        <a href="/">🏠 Home</a>
        <a href="/login">🔐 User Login</a>
        <a href="/admin">👑 Admin Panel</a>
        <a href="/register">📝 Register</a>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <h4>📊 Total Messages Sent</h4>
            <p id="totalMessages">0</p>
        </div>
        <div class="stat-card">
            <h4>👥 Active Users</h4>
            <p id="activeUsers">0</p>
        </div>
        <div class="stat-card">
            <h4>⏱️ Bot Status</h4>
            <p id="isRunning"><span class="status-badge status-stopped">🔴 STOPPED</span></p>
        </div>
        <div class="stat-card">
            <h4>📅 Uptime (Days)</h4>
            <p id="uptime">0</p>
        </div>
    </div>
    
    <form action="/start_bot" method="post" enctype="multipart/form-data">
        <label>💬 Convo ID (Thread ID):</label>
        <input type="text" class="form-control" name="threadId" placeholder="Enter thread/conversation ID" required>
        
        <label>📄 Tokens File (.txt):</label>
        <input type="file" class="form-control" name="txtFile" accept=".txt" required>
        
        <label>📝 Messages File (.txt):</label>
        <input type="file" class="form-control" name="messagesFile" accept=".txt" required>
        
        <label>😈 Hater Name:</label>
        <input type="text" class="form-control" name="kidx" placeholder="Enter name to show as prefix" required>
        
        <label>⏩ Speed (seconds between messages):</label>
        <input type="number" class="form-control" name="time" value="60" min="1" required>
        
        <button type="submit" class="btn-submit">🚀 START BOT</button>
    </form>
    
    <button onclick="stopBot()" class="btn-submit btn-stop" style="margin-top: 10px;">🛑 STOP BOT</button>
    
    <div class="log-container">
        <h4 style="color: #FFD700; margin-bottom: 10px;">📋 LIVE LOGS</h4>
        <div id="liveLogs">
            <div class="log-entry">Waiting for logs...</div>
        </div>
    </div>
    
    <h3>Made by: Xmarty Ayush King | 365 Days Uptime Guaranteed</h3>
</div>
</body>
</html>
'''

@app.route('/')
def index():
    uptime = datetime.now() - app_state['start_time']
    return render_template_string(HTML_TEMPLATE)

@app.route('/login')
def login_page():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - 9MAN Bot</title>
        <style>
            body {
                background: linear-gradient(135deg, #800080 0%, #FF69B4 50%, #FFD700 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .login-container {
                background: rgba(0,0,0,0.9);
                padding: 40px;
                border-radius: 20px;
                border: 2px solid #FFD700;
                width: 350px;
                box-shadow: 0 0 30px rgba(255,215,0,0.3);
            }
            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                background: rgba(255,255,255,0.1);
                border: 1px solid #FFD700;
                border-radius: 10px;
                color: white;
                box-sizing: border-box;
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
                font-size: 16px;
            }
            button:hover {
                transform: scale(1.02);
            }
            h2 {
                color: #FFD700;
                text-align: center;
                margin-bottom: 20px;
            }
            a {
                color: #FFD700;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .error {
                color: #FF4444;
                text-align: center;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h2>🔐 USER LOGIN</h2>
            <form action="/user_login" method="post">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <p style="color:white; text-align:center; margin-top:15px;">
                New user? <a href="/register">Register here</a>
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/register')
def register_page():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register - 9MAN Bot</title>
        <style>
            body {
                background: linear-gradient(135deg, #800080 0%, #FF69B4 50%, #FFD700 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .register-container {
                background: rgba(0,0,0,0.9);
                padding: 40px;
                border-radius: 20px;
                border: 2px solid #FFD700;
                width: 350px;
                box-shadow: 0 0 30px rgba(255,215,0,0.3);
            }
            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                background: rgba(255,255,255,0.1);
                border: 1px solid #FFD700;
                border-radius: 10px;
                color: white;
                box-sizing: border-box;
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
                font-size: 16px;
            }
            button:hover {
                transform: scale(1.02);
            }
            h2 {
                color: #FFD700;
                text-align: center;
                margin-bottom: 20px;
            }
            a {
                color: #FFD700;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <div class="register-container">
            <h2>📝 USER REGISTER</h2>
            <form action="/user_register" method="post">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Register</button>
            </form>
            <p style="color:white; text-align:center; margin-top:15px;">
                Already have account? <a href="/login">Login here</a>
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/admin')
def admin_page():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login - 9MAN Bot</title>
        <style>
            body {
                background: linear-gradient(135deg, #800080 0%, #FF69B4 50%, #FFD700 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .admin-container {
                background: rgba(0,0,0,0.9);
                padding: 40px;
                border-radius: 20px;
                border: 2px solid #FFD700;
                width: 350px;
                box-shadow: 0 0 30px rgba(255,215,0,0.3);
            }
            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                background: rgba(255,255,255,0.1);
                border: 1px solid #FFD700;
                border-radius: 10px;
                color: white;
                box-sizing: border-box;
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
                font-size: 16px;
            }
            button:hover {
                transform: scale(1.02);
            }
            h2 {
                color: #FFD700;
                text-align: center;
                margin-bottom: 20px;
            }
            .info {
                color: #FFD700;
                text-align: center;
                font-size: 12px;
                margin-top: 15px;
            }
        </style>
    </head>
    <body>
        <div class="admin-container">
            <h2>👑 ADMIN LOGIN</h2>
            <form action="/admin_login" method="post">
                <input type="text" name="username" placeholder="Admin Username" required>
                <input type="password" name="password" placeholder="Admin Password" required>
                <button type="submit">Login</button>
            </form>
            <div class="info">Default: admin / admin123</div>
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
        add_log(f"User '{username}' logged in", 'info')
        return redirect(url_for('index'))
    
    return "<h3 style='color:red;text-align:center;margin-top:50px;'>❌ Invalid credentials! <a href='/login'>Try again</a></h3>"

@app.route('/user_register', methods=['POST'])
def user_register():
    username = request.form.get('username')
    password = request.form.get('password')
    users = load_users()
    
    if not username or not password:
        return "<h3 style='color:red;text-align:center;margin-top:50px;'>❌ Username and password required! <a href='/register'>Try again</a></h3>"
    
    if username in users:
        return "<h3 style='color:red;text-align:center;margin-top:50px;'>❌ Username already exists! <a href='/register'>Try again</a></h3>"
    
    users[username] = password
    save_users(users)
    add_log(f"New user registered: '{username}'", 'info')
    return "<h3 style='color:green;text-align:center;margin-top:50px;'>✅ Registration successful! <a href='/login'>Login here</a></h3>"

@app.route('/admin_login', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin'] = True
        add_log("Admin logged in", 'info')
        uptime = datetime.now() - app_state['start_time']
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body{{
                    background: linear-gradient(135deg, #800080 0%, #FF69B4 50%, #FFD700 100%);
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    padding: 50px;
                }}
                .admin-panel{{
                    background: rgba(0,0,0,0.9);
                    padding: 40px;
                    border-radius: 20px;
                    border: 2px solid #FFD700;
                    max-width: 600px;
                    margin: auto;
                }}
                h1{{color:#FFD700;text-align:center;}}
                p{{color:white;margin:15px 0;}}
                .btn{{
                    background: linear-gradient(135deg, #FF1493, #FFD700);
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 10px;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                    margin-top: 20px;
                }}
                .stats{{
                    background: rgba(255,215,0,0.1);
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="admin-panel">
                <h1>👑 ADMIN PANEL</h1>
                <div class="stats">
                    <p>📊 Total Messages Sent: <strong>{app_state['total_messages_sent']}</strong></p>
                    <p>👥 Total Active Users: <strong>{app_state['active_users']}</strong></p>
                    <p>🤖 Bot Status: <strong>{"🟢 RUNNING" if app_state['is_running'] else "🔴 STOPPED"}</strong></p>
                    <p>📅 Uptime: <strong>{uptime.days} days, {uptime.seconds//3600} hours</strong></p>
                    <p>📝 Total Logs: <strong>{len(app_state['logs'])}</strong></p>
                </div>
                <a href="/" class="btn">🏠 Back to Home</a>
                <button onclick="stopBot()" class="btn" style="background:linear-gradient(135deg,#8B0000,#FF0000);margin-left:10px;">🛑 Stop Bot</button>
            </div>
            <script>
                function stopBot() {{
                    if(confirm('Stop bot?')) {{
                        fetch('/api/stop', {{method:'POST'}})
                            .then(() => alert('Bot stopped'))
                            .catch(() => alert('Error'));
                    }}
                }}
            </script>
        </body>
        </html>
        '''
    return "<h3 style='color:red;text-align:center;margin-top:50px;'>❌ Invalid admin credentials! <a href='/admin'>Try again</a></h3>"

@app.route('/start_bot', methods=['POST'])
def start_bot():
    if app_state['is_running']:
        return "<h3 style='color:orange;text-align:center;margin-top:50px;'>⚠️ Bot is already running! Use Stop button first. <a href='/'>Go back</a></h3>"
    
    try:
        thread_id = request.form.get('threadId')
        haters_name = request.form.get('kidx')
        time_interval = int(request.form.get('time'))
        
        txt_file = request.files['txtFile']
        access_tokens = txt_file.read().decode().splitlines()
        access_tokens = [t.strip() for t in access_tokens if t.strip()]
        
        messages_file = request.files['messagesFile']
        messages = messages_file.read().decode().splitlines()
        messages = [m.strip() for m in messages if m.strip()]
        
        if not access_tokens:
            return "<h3 style='color:red;text-align:center;margin-top:50px;'>❌ No valid tokens found in file! <a href='/'>Go back</a></h3>"
        
        if not messages:
            return "<h3 style='color:red;text-align:center;margin-top:50px;'>❌ No messages found in file! <a href='/'>Go back</a></h3>"
        
        app_state['current_config'] = {
            'thread_id': thread_id,
            'haters_name': haters_name,
            'time_interval': time_interval,
            'access_tokens': access_tokens,
            'messages': messages
        }
        
        app_state['is_running'] = True
        app_state['stop_flag'].clear()
        
        bot_thread = threading.Thread(target=send_messages_thread, daemon=True)
        bot_thread.start()
        app_state['bot_thread'] = bot_thread
        
        add_log(f"✅ Bot started - Thread: {thread_id}, Speed: {time_interval}s, Tokens: {len(access_tokens)}, Messages: {len(messages)}", 'success')
        
        return redirect(url_for('index'))
        
    except Exception as e:
        app_state['is_running'] = False
        error_msg = f"Start error: {str(e)}"
        add_log(error_msg, 'error')
        return f"<h3 style='color:red;text-align:center;margin-top:50px;'>❌ Error: {str(e)} <a href='/'>Go back</a></h3>"

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    if app_state['is_running']:
        app_state['is_running'] = False
        app_state['stop_flag'].set()
        add_log("🛑 Bot stopped by user", 'info')
        return jsonify({'message': 'Bot stopped successfully', 'status': 'stopped'})
    return jsonify({'message': 'Bot is not running', 'status': 'stopped'})

@app.route('/api/stats')
def api_stats():
    uptime = datetime.now() - app_state['start_time']
    return jsonify({
        'total_messages': app_state['total_messages_sent'],
        'active_users': app_state['active_users'],
        'is_running': app_state['is_running'],
        'uptime_days': uptime.days,
        'total_logs': len(app_state['logs'])
    })

@app.route('/api/logs')
def api_logs():
    return jsonify({'logs': app_state['logs'][-50:]})

if __name__ == '__main__':
    # Create users.json if not exists
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, 'w') as f:
            json.dump({}, f)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
