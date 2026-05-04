from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify
import requests
import time
import threading
from datetime import datetime, timedelta
import os
import json
import traceback
import logging

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this-12345'
app.permanent_session_lifetime = timedelta(days=365)

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Store application state
app_state = {
    'is_running': False,
    'start_time': datetime.now(),
    'total_messages_sent': 0,
    'total_failed': 0,
    'total_users': 0,
    'active_users': 0,
    'logs': [],
    'stop_flag': threading.Event(),
    'bot_thread': None,
    'current_config': {},
    'retry_count': 0
}

# Admin credentials - CHANGE THESE FOR SECURITY
ADMIN_USERNAME = 'YAMDHUD'
ADMIN_PASSWORD = '9MAN520'

# User database
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
    'referer': 'https://www.facebook.com/'
}

def add_log(message, log_type='info'):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {'time': timestamp, 'message': message, 'type': log_type}
    app_state['logs'].append(log_entry)
    if len(app_state['logs']) > 100:
        app_state['logs'].pop(0)
    
    if log_type == 'error':
        logger.error(f"[{timestamp}] {message}")
    elif log_type == 'success':
        logger.info(f"[{timestamp}] {message}")
    else:
        logger.debug(f"[{timestamp}] {message}")

def send_message_with_retry(post_url, parameters, max_retries=3):
    for attempt in range(max_retries):
        try:
            add_log(f"📤 Attempt {attempt + 1} to send message", 'info')
            
            response = requests.post(
                post_url, 
                data=parameters, 
                headers=headers, 
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    response_json = response.json()
                    add_log(f"✅ Response ID: {response_json.get('id', 'N/A')}", 'success')
                except:
                    add_log(f"✅ Response: {response.text[:100]}", 'success')
                return True, response
            
            elif response.status_code == 400:
                add_log(f"⚠️ Bad Request - Token may be invalid", 'error')
                return False, response
            elif response.status_code == 401:
                add_log(f"⚠️ Unauthorized - Token expired", 'error')
                return False, response
            elif response.status_code == 429:
                add_log(f"⚠️ Rate Limited - Waiting { (attempt + 1) * 5 } seconds", 'error')
                time.sleep((attempt + 1) * 5)
                continue
            elif response.status_code == 404:
                add_log(f"❌ Not Found - Invalid Thread ID", 'error')
                return False, response
            else:
                add_log(f"❌ Status: {response.status_code}", 'error')
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                    
        except requests.exceptions.Timeout:
            add_log(f"⏰ Timeout - Retry {attempt + 1}", 'error')
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
        except requests.exceptions.ConnectionError:
            add_log(f"🔌 Connection error - Retry {attempt + 1}", 'error')
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
        except Exception as e:
            add_log(f"❌ Error: {str(e)[:100]}", 'error')
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
    
    return False, None

def send_messages_thread():
    try:
        thread_id = app_state['current_config'].get('thread_id')
        haters_name = app_state['current_config'].get('haters_name')
        time_interval = app_state['current_config'].get('time_interval', 60)
        access_tokens = app_state['current_config'].get('access_tokens', [])
        messages = app_state['current_config'].get('messages', [])
        
        add_log(f"🚀 Bot started - {len(access_tokens)} tokens, {len(messages)} messages", 'info')
        add_log(f"📌 Thread ID: {thread_id}", 'info')
        
        if not all([thread_id, haters_name, access_tokens, messages]):
            add_log("❌ Missing configuration!", 'error')
            app_state['is_running'] = False
            return
            
        post_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
        num_comments = len(messages)
        max_tokens = len(access_tokens)
        
        consecutive_failures = 0
        
        while app_state['is_running'] and not app_state['stop_flag'].is_set():
            try:
                for message_index in range(num_comments):
                    if not app_state['is_running'] or app_state['stop_flag'].is_set():
                        break
                    
                    token_index = message_index % max_tokens
                    access_token = access_tokens[token_index].strip()
                    
                    if not access_token or len(access_token) < 20:
                        add_log(f"⚠️ Invalid token at index {token_index}", 'error')
                        consecutive_failures += 1
                        continue
                    
                    message = messages[message_index].strip()
                    if not message:
                        consecutive_failures += 1
                        continue
                    
                    final_message = f"{haters_name} {message}"
                    if len(final_message) > 1900:
                        final_message = final_message[:1900]
                    
                    parameters = {
                        'access_token': access_token,
                        'message': final_message
                    }
                    
                    add_log(f"📨 Sending {message_index + 1}/{num_comments}: {final_message[:50]}...", 'info')
                    
                    success, response = send_message_with_retry(post_url, parameters)
                    
                    if success:
                        app_state['total_messages_sent'] += 1
                        consecutive_failures = 0
                        add_log(f"✅ Message {message_index + 1}/{num_comments} SENT", 'success')
                    else:
                        app_state['total_failed'] += 1
                        consecutive_failures += 1
                        add_log(f"❌ Message {message_index + 1}/{num_comments} FAILED", 'error')
                        
                        if consecutive_failures > 5:
                            add_log(f"⚠️ Too many failures, waiting 30 seconds...", 'warning')
                            time.sleep(30)
                            consecutive_failures = 0
                            continue
                    
                    add_log(f"⏳ Waiting {time_interval} seconds...", 'info')
                    time.sleep(time_interval)
                    
                add_log(f"🔄 Completed all messages, restarting...", 'info')
                time.sleep(5)
                    
            except Exception as e:
                add_log(f"❌ Loop error: {str(e)[:100]}", 'error')
                time.sleep(30)
                
    except Exception as e:
        add_log(f"❌ Thread error: {str(e)[:100]}", 'error')
    finally:
        app_state['is_running'] = False
        add_log("🛑 Bot stopped", 'info')

# HTML Template - Admin section ONLY visible to admin
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
            background: linear-gradient(135deg, #0a2e0a 0%, #1a4a1a 50%, #004d00 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: rgba(0, 0, 0, 0.9);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 0 30px rgba(0, 255, 0, 0.3);
            backdrop-filter: blur(10px);
            border: 2px solid #00aa00;
        }
        
        h1 {
            text-align: center;
            color: #00ff00;
            font-family: 'Courier New', monospace;
            font-size: 32px;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px #004d00;
        }
        
        .subtitle {
            text-align: center;
            color: #90ee90;
            font-family: cursive;
            margin-bottom: 30px;
        }
        
        .register-main {
            background: linear-gradient(135deg, rgba(0,100,0,0.3), rgba(0,255,0,0.1));
            border: 2px solid #00aa00;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .register-main h2 {
            color: #00ff00;
            margin-bottom: 20px;
            font-size: 28px;
        }
        
        .register-main input {
            width: 80%;
            max-width: 350px;
            padding: 15px;
            margin: 10px;
            background: rgba(0,0,0,0.7);
            border: 2px solid #00aa00;
            border-radius: 10px;
            color: #90ee90;
            font-size: 16px;
        }
        
        .register-main button {
            padding: 15px 40px;
            background: linear-gradient(135deg, #006400, #00aa00);
            border: none;
            border-radius: 10px;
            color: white;
            font-weight: bold;
            font-size: 18px;
            cursor: pointer;
            transition: transform 0.3s ease;
        }
        
        .register-main button:hover {
            transform: scale(1.05);
        }
        
        .login-link {
            text-align: center;
            margin-top: 15px;
            color: #90ee90;
        }
        
        .login-link a {
            color: #00ff00;
            text-decoration: none;
            font-weight: bold;
        }
        
        .bot-section {
            display: {% if session.user %}block{% else %}none{% endif %};
            animation: fadeIn 0.5s ease;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: rgba(0, 170, 0, 0.1);
            border: 1px solid #00aa00;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        
        .stat-card h4 {
            color: #00ff00;
            margin-bottom: 10px;
        }
        
        .stat-card p {
            color: #90ee90;
            font-size: 24px;
            font-weight: bold;
        }
        
        .form-control, input[type="text"], input[type="number"], input[type="file"] {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: rgba(0, 0, 0, 0.7);
            border: 2px solid #00aa00;
            border-radius: 10px;
            color: #90ee90;
            font-size: 14px;
        }
        
        label {
            color: #00ff00;
            font-weight: bold;
            display: block;
            margin-top: 10px;
        }
        
        .btn-submit {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #006400, #00aa00);
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
            transform: scale(1.02);
        }
        
        .btn-stop {
            background: linear-gradient(135deg, #8B0000, #FF0000);
        }
        
        .log-container {
            background: rgba(0, 0, 0, 0.95);
            border: 1px solid #00aa00;
            border-radius: 10px;
            height: 350px;
            overflow-y: auto;
            padding: 10px;
            margin-top: 20px;
        }
        
        .log-entry {
            padding: 5px;
            margin: 5px 0;
            border-left: 3px solid #00aa00;
            font-family: monospace;
            font-size: 11px;
            word-wrap: break-word;
        }
        
        .log-success {
            color: #00ff00;
            border-left-color: #00ff00;
        }
        
        .log-error {
            color: #ff6666;
            border-left-color: #ff6666;
        }
        
        .log-info {
            color: #ffcc00;
            border-left-color: #ffcc00;
        }
        
        /* ADMIN SECTION - ONLY VISIBLE TO ADMIN */
        .admin-section {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #00aa00;
            background: rgba(0, 170, 0, 0.05);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            display: {% if session.admin %}block{% else %}none{% endif %};
        }
        
        .admin-section h3 {
            color: #00ff00;
            margin-bottom: 15px;
        }
        
        .admin-section h3::before {
            content: "🔐 ";
        }
        
        .admin-section h3::after {
            content: " (Admin Only)";
            font-size: 12px;
        }
        
        .admin-controls {
            display: flex;
            gap: 10px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .admin-btn {
            padding: 10px 20px;
            background: linear-gradient(135deg, #006400, #00aa00);
            border: none;
            border-radius: 10px;
            color: white;
            cursor: pointer;
            font-weight: bold;
        }
        
        .admin-btn-danger {
            background: linear-gradient(135deg, #8B0000, #FF0000);
        }
        
        .status-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .status-running {
            background: #00ff00;
            color: #000;
        }
        
        .status-stopped {
            background: #ff0000;
            color: #fff;
        }
        
        .user-info {
            text-align: right;
            color: #00ff00;
            margin-bottom: 15px;
            font-size: 14px;
        }
        
        .logout-btn {
            background: rgba(255,0,0,0.3);
            padding: 5px 10px;
            border-radius: 5px;
            text-decoration: none;
            color: #00ff00;
            margin-left: 10px;
        }
        
        .admin-login-btn {
            background: rgba(0,255,0,0.2);
            padding: 5px 10px;
            border-radius: 5px;
            text-decoration: none;
            color: #00ff00;
            margin-left: 10px;
            border: 1px solid #00ff00;
        }
        
        .welcome-msg {
            background: rgba(0,255,0,0.2);
            border: 1px solid #00ff00;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            color: #00ff00;
            font-size: 18px;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        ::-webkit-scrollbar {
            width: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(0, 170, 0, 0.1);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #00aa00;
            border-radius: 10px;
        }
    </style>
    <script>
        function updateStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalMessages').innerText = data.total_messages;
                    document.getElementById('totalFailed').innerText = data.total_failed;
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
                        logContainer.scrollTop = 0;
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
        
        setInterval(updateStats, 2000);
        setInterval(updateLogs, 2000);
        
        // Admin functions - only work if admin is logged in
        function stopBot() {
            if(confirm('⚠️ Are you sure you want to stop the bot? (Admin Only)')) {
                fetch('/api/stop', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        updateStats();
                    })
                    .catch(err => alert('Error: ' + err));
            }
        }
        
        function clearLogs() {
            if(confirm('⚠️ Clear all logs? (Admin Only)')) {
                fetch('/api/clear_logs', {method: 'POST'})
                    .then(() => alert('Logs cleared'))
                    .catch(err => alert('Error: ' + err));
            }
        }
        
        function resetStats() {
            if(confirm('⚠️ Reset all statistics? This cannot be undone! (Admin Only)')) {
                fetch('/api/reset_stats', {method: 'POST'})
                    .then(() => alert('Stats reset'))
                    .catch(err => alert('Error: ' + err));
            }
        }
        
        updateStats();
        updateLogs();
    </script>
</head>
<body>
<div class="container">
    <h1>⚜️ 9MAN-x-YAMDHUD ⚜️</h1>
    <div class="subtitle">🔥 Advanced Facebook Message Bot 🔥</div>
    
    {% if session.user %}
    <div class="user-info">
        👤 Welcome, {{ session.user }}! 
        {% if not session.admin %}
            <a href="/admin_login_page" class="admin-login-btn">👑 Admin Login</a>
        {% endif %}
        <a href="/logout" class="logout-btn">Logout</a>
    </div>
    {% endif %}
    
    <!-- REGISTER SECTION -->
    {% if not session.user %}
    <div class="register-main">
        <h2>📝 CREATE ACCOUNT</h2>
        <form action="/do_register" method="post">
            <input type="text" name="username" placeholder="Choose Username" required>
            <input type="password" name="password" placeholder="Choose Password" required>
            <button type="submit">🔐 REGISTER NOW</button>
        </form>
        <div class="login-link">
            Already have an account? <a href="/login_page">Login here</a>
        </div>
    </div>
    {% else %}
    
    <div class="welcome-msg">
        ✅ Welcome {{ session.user }}! You can now use the bot.
    </div>
    {% endif %}
    
    <!-- BOT SECTION -->
    {% if session.user %}
    <div class="bot-section">
        <div class="stats">
            <div class="stat-card">
                <h4>📊 Messages Sent</h4>
                <p id="totalMessages">0</p>
            </div>
            <div class="stat-card">
                <h4>❌ Failed</h4>
                <p id="totalFailed">0</p>
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
            
            <label>⏩ Speed (seconds):</label>
            <input type="number" class="form-control" name="time" value="60" min="1" required>
            
            <button type="submit" class="btn-submit">🚀 START BOT</button>
        </form>
        
        <!-- Stop button - Only visible to admin -->
        {% if session.admin %}
        <button onclick="stopBot()" class="btn-submit btn-stop" style="margin-top: 10px;">🛑 STOP BOT (Admin Only)</button>
        {% endif %}
    </div>
    {% endif %}
    
    <div class="log-container">
        <h4 style="color: #00ff00; margin-bottom: 10px;">📋 LIVE LOGS</h4>
        <div id="liveLogs">
            <div class="log-entry">Waiting for logs...</div>
        </div>
    </div>
    
    <!-- ADMIN SECTION - ONLY VISIBLE TO ADMIN -->
    {% if session.admin %}
    <div class="admin-section">
        <h3>👑 ADMIN CONTROL PANEL</h3>
        <div class="admin-controls">
            <button onclick="stopBot()" class="admin-btn admin-btn-danger">🛑 Stop Bot</button>
            <button onclick="clearLogs()" class="admin-btn">🗑️ Clear Logs</button>
            <button onclick="resetStats()" class="admin-btn">📊 Reset Stats</button>
        </div>
        <p style="color:#90ee90; text-align:center; margin-top:15px; font-size:12px;">
            🔐 Admin Access Only | Full Control
        </p>
    </div>
    {% elif session.user %}
    <div style="margin-top: 30px; padding: 15px; text-align: center; background: rgba(255,0,0,0.1); border-radius: 10px;">
        <p style="color: #ff6666;">⚠️ Admin panel is locked. <a href="/admin_login_page" style="color:#00ff00;">Login as Admin</a> to access controls.</p>
    </div>
    {% endif %}
    
    <div style="text-align: center; margin-top: 20px; color: #00aa00; font-size: 12px;">
        Made by: 9MAN X YAMDHUD | 365 Days Uptime
    </div>
</div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, session=session)

@app.route('/do_register', methods=['POST'])
def do_register():
    username = request.form.get('username')
    password = request.form.get('password')
    users = load_users()
    
    if not username or not password:
        return "<h3 style='color:#ff6666;text-align:center;margin-top:50px;'>❌ Username and password required! <a href='/'>Go back</a></h3>"
    
    if username in users:
        return "<h3 style='color:#ff6666;text-align:center;margin-top:50px;'>❌ Username already exists! <a href='/'>Try different username</a></h3>"
    
    users[username] = password
    save_users(users)
    
    session['user'] = username
    app_state['active_users'] += 1
    add_log(f"✅ New user registered: '{username}'", 'success')
    
    return redirect(url_for('index'))

@app.route('/login_page')
def login_page():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - 9MAN Bot</title>
        <style>
            body {
                background: linear-gradient(135deg, #0a2e0a 0%, #1a4a1a 50%, #004d00 100%);
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
                border: 2px solid #00aa00;
                width: 350px;
            }
            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                background: rgba(0,0,0,0.7);
                border: 1px solid #00aa00;
                border-radius: 10px;
                color: #90ee90;
            }
            button {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #006400, #00aa00);
                border: none;
                border-radius: 10px;
                color: white;
                font-weight: bold;
                cursor: pointer;
            }
            h2 {
                color: #00ff00;
                text-align: center;
            }
            a {
                color: #00ff00;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h2>🔐 USER LOGIN</h2>
            <form action="/do_login" method="post">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <p style="color:#90ee90; text-align:center; margin-top:15px;">
                New user? <a href="/">Register here</a>
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/do_login', methods=['POST'])
def do_login():
    username = request.form.get('username')
    password = request.form.get('password')
    users = load_users()
    
    if username in users and users[username] == password:
        session['user'] = username
        app_state['active_users'] += 1
        add_log(f"✅ User '{username}' logged in", 'success')
        return redirect(url_for('index'))
    
    return "<h3 style='color:#ff6666;text-align:center;margin-top:50px;'>❌ Invalid credentials! <a href='/login_page'>Try again</a></h3>"

@app.route('/logout')
def logout():
    if session.get('user'):
        add_log(f"👋 User '{session['user']}' logged out", 'info')
        if app_state['active_users'] > 0:
            app_state['active_users'] -= 1
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin_login_page')
def admin_login_page():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login - 9MAN Bot</title>
        <style>
            body {
                background: linear-gradient(135deg, #0a2e0a 0%, #1a4a1a 50%, #004d00 100%);
                font-family: 'Segoe UI', sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .admin-container {
                background: rgba(0,0,0,0.9);
                padding: 40px;
                border-radius: 20px;
                border: 2px solid #00aa00;
                width: 350px;
            }
            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                background: rgba(0,0,0,0.7);
                border: 1px solid #00aa00;
                border-radius: 10px;
                color: #90ee90;
            }
            button {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #006400, #00aa00);
                border: none;
                border-radius: 10px;
                color: white;
                font-weight: bold;
                cursor: pointer;
            }
            h2 {
                color: #00ff00;
                text-align: center;
            }
            .info {
                color: #90ee90;
                text-align: center;
                margin-top: 15px;
                font-size: 12px;
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
            <div class="info">Contact developer for admin access</div>
        </div>
    </body>
    </html>
    '''

@app.route('/admin_login', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin'] = True
        add_log("👑 Admin logged in", 'success')
        return redirect(url_for('index'))
    
    return "<h3 style='color:#ff6666;text-align:center;margin-top:50px;'>❌ Invalid admin credentials! <a href='/admin_login_page'>Try again</a></h3>"

@app.route('/start_bot', methods=['POST'])
def start_bot():
    if not session.get('user'):
        return "<h3 style='color:#ff6666;text-align:center;margin-top:50px;'>❌ Please login first!</h3>"
    
    if app_state['is_running']:
        return "<h3 style='color:#ffaa00;text-align:center;margin-top:50px;'>⚠️ Bot is already running!</h3>"
    
    try:
        thread_id = request.form.get('threadId').strip()
        haters_name = request.form.get('kidx').strip()
        time_interval = int(request.form.get('time'))
        
        if not thread_id:
            return "<h3 style='color:#ff6666;text-align:center;margin-top:50px;'>❌ Thread ID is required!</h3>"
        
        txt_file = request.files['txtFile']
        content = txt_file.read().decode()
        access_tokens = [t.strip() for t in content.splitlines() if t.strip() and len(t.strip()) > 10]
        
        messages_file = request.files['messagesFile']
        content = messages_file.read().decode()
        messages = [m.strip() for m in content.splitlines() if m.strip()]
        
        if not access_tokens:
            return "<h3 style='color:#ff6666;text-align:center;margin-top:50px;'>❌ No valid tokens found!</h3>"
        
        if not messages:
            return "<h3 style='color:#ff6666;text-align:center;margin-top:50px;'>❌ No messages found!</h3>"
        
        app_state['current_config'] = {
            'thread_id': thread_id,
            'haters_name': haters_name,
            'time_interval': time_interval,
            'access_tokens': access_tokens,
            'messages': messages
        }
        
        app_state['is_running'] = True
        app_state['stop_flag'].clear()
        app_state['total_failed'] = 0
        
        bot_thread = threading.Thread(target=send_messages_thread, daemon=True)
        bot_thread.start()
        app_state['bot_thread'] = bot_thread
        
        add_log(f"✅ Bot started by {session['user']}", 'success')
        
        return redirect(url_for('index'))
        
    except Exception as e:
        app_state['is_running'] = False
        add_log(f"Start error: {str(e)}", 'error')
        return f"<h3 style='color:#ff6666;text-align:center;margin-top:50px;'>❌ Error: {str(e)}<br><a href='/'>Go back</a></h3>"

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    # Only admin can stop the bot
    if not session.get('admin'):
        return jsonify({'message': 'Unauthorized! Admin only.', 'status': 'unauthorized'}), 401
    
    if app_state['is_running']:
        app_state['is_running'] = False
        app_state['stop_flag'].set()
        add_log("🛑 Bot stopped by admin", 'info')
        return jsonify({'message': 'Bot stopped successfully', 'status': 'stopped'})
    return jsonify({'message': 'Bot is not running', 'status': 'stopped'})

@app.route('/api/clear_logs', methods=['POST'])
def clear_logs():
    # Only admin can clear logs
    if not session.get('admin'):
        return jsonify({'message': 'Unauthorized! Admin only.', 'status': 'unauthorized'}), 401
    
    app_state['logs'] = []
    add_log("🗑️ Logs cleared by admin", 'info')
    return jsonify({'message': 'Logs cleared'})

@app.route('/api/reset_stats', methods=['POST'])
def reset_stats():
    # Only admin can reset stats
    if not session.get('admin'):
        return jsonify({'message': 'Unauthorized! Admin only.', 'status': 'unauthorized'}), 401
    
    app_state['total_messages_sent'] = 0
    app_state['total_failed'] = 0
    add_log("📊 Statistics reset by admin", 'info')
    return jsonify({'message': 'Stats reset'})

@app.route('/api/stats')
def api_stats():
    uptime = datetime.now() - app_state['start_time']
    return jsonify({
        'total_messages': app_state['total_messages_sent'],
        'total_failed': app_state['total_failed'],
        'active_users': app_state['active_users'],
        'is_running': app_state['is_running'],
        'uptime_days': uptime.days,
        'total_logs': len(app_state['logs'])
    })

@app.route('/api/logs')
def api_logs():
    return jsonify({'logs': app_state['logs'][-50:]})

if __name__ == '__main__':
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, 'w') as f:
            json.dump({}, f)
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Server running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
