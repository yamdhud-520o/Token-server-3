from flask import Flask, request, render_template_string, redirect, url_for, jsonify, session
import requests
import time
import threading
from datetime import datetime
import os
import uuid
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Global variables
tasks = {}
total_messages_sent = 0
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

# HTML Template with Original Design + Task System
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
            max-width: 1200px;
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

        .user-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
        }

        .user-id {
            font-family: monospace;
            font-size: 14px;
            background: rgba(0,0,0,0.3);
            padding: 8px 15px;
            border-radius: 20px;
            font-weight: bold;
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

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }

        .form-section, .tasks-section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .form-section h3, .tasks-section h3 {
            color: #ff6b6b;
            margin-bottom: 20px;
            text-align: center;
            font-size: 20px;
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
            width: 100%;
        }

        button:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }

        .btn-stop-task {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 8px 20px;
            font-size: 14px;
            width: auto;
        }

        .task-card {
            background: white;
            border-left: 4px solid #00ff00;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }

        .task-card.stopped {
            border-left-color: #ff4444;
            opacity: 0.7;
        }

        .task-card:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 10px;
        }

        .task-id {
            color: #667eea;
            font-family: monospace;
            font-weight: bold;
            font-size: 14px;
        }

        .task-status {
            padding: 3px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
        }

        .status-active {
            background: #00ff00;
            color: #000;
        }

        .status-stopped {
            background: #ff4444;
            color: #fff;
        }

        .task-details {
            font-size: 12px;
            color: #666;
            margin-bottom: 10px;
            line-height: 1.6;
        }

        .task-owner {
            color: #764ba2;
            font-family: monospace;
            font-size: 11px;
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

        .no-tasks {
            text-align: center;
            color: #999;
            padding: 40px;
        }

        @keyframes glow {
            0% { box-shadow: 0 0 5px #ff6b6b; }
            100% { box-shadow: 0 0 20px #ff6b6b; }
        }

        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            .container {
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚜️9MAN-x-YAMDHUD⚜️</h1>
        <p style="text-align: center; color: #666; margin-bottom: 20px;">Advanced Task-Based Facebook Message Attacker</p>

        <div class="user-section">
            <div class="user-info">
                <span>👤 YOUR USER ID:</span>
                <span class="user-id" id="userId">{{ session.get('user_id', 'Not set') }}</span>
            </div>
            <button onclick="regenerateUserId()" style="width: auto; padding: 8px 20px; font-size: 12px;">🔄 NEW ID</button>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>📊 TOTAL TASKS</h3>
                <div class="value" id="totalTasks">0</div>
            </div>
            <div class="stat-card">
                <h3>✅ ACTIVE TASKS</h3>
                <div class="value" id="activeTasks">0</div>
            </div>
            <div class="stat-card">
                <h3>📨 TOTAL MESSAGES</h3>
                <div class="value" id="totalMessages">{{ total_messages }}</div>
            </div>
            <div class="stat-card">
                <h3>👥 YOUR TASKS</h3>
                <div class="value" id="userTasks">0</div>
            </div>
        </div>

        <div class="main-content">
            <div class="form-section">
                <h3>🚀 CREATE NEW TASK</h3>
                <form id="attackForm" enctype="multipart/form-data">
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
                    <button type="submit">🚀 START TASK</button>
                </form>
            </div>

            <div class="tasks-section">
                <h3>📋 YOUR ACTIVE TASKS</h3>
                <div id="tasksList">
                    <div class="no-tasks">No active tasks. Create one above!</div>
                </div>
            </div>
        </div>

        <div class="log-container" id="logContainer">
            <div class="log-entry">[*] System Ready - Task System Active</div>
            <div class="log-entry">[*] 365 Days continuous run mode active</div>
        </div>
    </div>

    <script>
        let userId = '{{ session.get("user_id", "") }}';

        function showAlert(message, type) {
            const alertDiv = document.createElement('div');
            alertDiv.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${type === 'success' ? '#00ff00' : '#ff4444'};
                color: white;
                padding: 15px 20px;
                border-radius: 10px;
                z-index: 9999;
                animation: slideIn 0.3s ease;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            `;
            alertDiv.innerHTML = message;
            document.body.appendChild(alertDiv);
            setTimeout(() => {
                alertDiv.remove();
            }, 3000);
        }

        function regenerateUserId() {
            fetch('/regenerate_user_id', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.user_id) {
                        document.getElementById('userId').innerText = data.user_id;
                        userId = data.user_id;
                        showAlert('User ID regenerated successfully!', 'success');
                        loadTasks();
                        loadStats();
                    }
                });
        }

        document.getElementById('attackForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            const startBtn = e.target.querySelector('button[type="submit"]');
            startBtn.disabled = true;
            startBtn.innerHTML = '⏳ CREATING TASK...';
            
            try {
                const response = await fetch('/api/tasks/create', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                if (data.success) {
                    showAlert(`✅ Task created successfully! ID: ${data.task_id}`, 'success');
                    e.target.reset();
                    loadTasks();
                    loadStats();
                } else {
                    showAlert(`❌ Error: ${data.error}`, 'error');
                }
            } catch (error) {
                showAlert(`❌ Error: ${error.message}`, 'error');
            } finally {
                startBtn.disabled = false;
                startBtn.innerHTML = '🚀 START TASK';
            }
        });

        async function stopTask(taskId) {
            if (!confirm(`Are you sure you want to stop task ${taskId}?`)) return;
            
            const response = await fetch(`/api/tasks/${taskId}/stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id: userId })
            });
            
            const data = await response.json();
            if (data.success) {
                showAlert(`✅ Task ${taskId} stopped successfully!`, 'success');
                loadTasks();
                loadStats();
            } else {
                showAlert(`❌ ${data.error}`, 'error');
            }
        }

        async function loadTasks() {
            const response = await fetch('/api/tasks');
            const tasks = await response.json();
            
            const tasksList = document.getElementById('tasksList');
            const userTasks = tasks.filter(t => t.owner_id === userId);
            
            document.getElementById('userTasks').innerText = userTasks.length;
            
            if (userTasks.length === 0) {
                tasksList.innerHTML = '<div class="no-tasks">📭 No active tasks. Create one above!</div>';
                return;
            }
            
            tasksList.innerHTML = userTasks.map(task => `
                <div class="task-card ${task.active ? '' : 'stopped'}">
                    <div class="task-header">
                        <span class="task-id">🔖 TASK ID: ${task.task_id}</span>
                        <span class="task-status ${task.active ? 'status-active' : 'status-stopped'}">
                            ${task.active ? '🟢 ACTIVE' : '🔴 STOPPED'}
                        </span>
                    </div>
                    <div class="task-details">
                        <div>🎯 TARGET: ${task.target_name}</div>
                        <div>💬 MESSAGES SENT: ${task.messages_sent}</div>
                        <div>⏱️ DURATION: ${task.duration}</div>
                        <div class="task-owner">👤 OWNER: ${task.owner_id}</div>
                    </div>
                    ${task.active ? 
                        `<button class="btn-stop-task" onclick="stopTask('${task.task_id}')">🛑 STOP TASK</button>` : 
                        '<span style="color: #999; font-size: 12px;">✓ TASK STOPPED</span>'
                    }
                </div>
            `).join('');
        }

        async function loadStats() {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            document.getElementById('totalTasks').innerText = stats.total_tasks;
            document.getElementById('activeTasks').innerText = stats.active_tasks;
            document.getElementById('totalMessages').innerText = stats.total_messages;
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

        setInterval(loadTasks, 3000);
        setInterval(loadStats, 2000);
        setInterval(fetchLogs, 2000);
        
        loadTasks();
        loadStats();
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

def attack_worker(task_id, thread_id, mn, time_interval, access_tokens, messages, owner_id):
    global total_messages_sent
    
    task_info = tasks.get(task_id)
    if not task_info:
        return
    
    num_comments = len(messages)
    max_tokens = len(access_tokens)
    post_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
    message_index = 0
    
    add_log(f"Task {task_id} started by {owner_id} on conversation {thread_id}", "success")
    
    while task_info['active']:
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
                task_info['total_messages'] += 1
                log_msg = f"✅ Task {task_id} | Msg #{task_info['total_messages']} | {mn} {message}"
                add_log(log_msg, "success")
            else:
                log_msg = f"❌ Task {task_id} FAILED | {mn} {message} | Error: {response.status_code}"
                add_log(log_msg, "error")
            
            message_index += 1
            time.sleep(time_interval)
            
        except Exception as e:
            add_log(f"Task {task_id} Error: {str(e)}", "error")
            time.sleep(30)
    
    add_log(f"Task {task_id} stopped by {owner_id}", "info")

@app.route('/')
def index():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())[:8]
    return render_template_string(HTML_TEMPLATE, total_messages=total_messages_sent, session=session)

@app.route('/regenerate_user_id', methods=['POST'])
def regenerate_user_id():
    session['user_id'] = str(uuid.uuid4())[:8]
    return jsonify({'user_id': session['user_id']})

@app.route('/api/tasks/create', methods=['POST'])
def create_task():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())[:8]
    
    owner_id = session['user_id']
    
    try:
        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))
        
        txt_file = request.files['txtFile']
        access_tokens = txt_file.read().decode().splitlines()
        
        messages_file = request.files['messagesFile']
        messages = messages_file.read().decode().splitlines()
        
        if not access_tokens or not messages:
            return jsonify({'success': False, 'error': 'Files are empty!'})
        
        task_id = str(uuid.uuid4())[:8]
        
        task_info = {
            'task_id': task_id,
            'owner_id': owner_id,
            'active': True,
            'thread': None,
            'start_time': datetime.now(),
            'thread_id': thread_id,
            'target_name': mn,
            'total_messages': 0
        }
        
        task_thread = threading.Thread(
            target=attack_worker,
            args=(task_id, thread_id, mn, time_interval, access_tokens, messages, owner_id),
            daemon=True
        )
        
        task_info['thread'] = task_thread
        tasks[task_id] = task_info
        task_thread.start()
        
        add_log(f"✅ Task {task_id} created by {owner_id}", "success")
        
        return jsonify({'success': True, 'task_id': task_id})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/tasks/<task_id>/stop', methods=['POST'])
def stop_task(task_id):
    data = request.get_json()
    requester_id = data.get('user_id')
    
    # Error handling: Invalid Task ID
    if task_id not in tasks:
        return jsonify({'success': False, 'error': 'Invalid Task ID - Task not found'}), 404
    
    task_info = tasks[task_id]
    
    # Error handling: Already stopped
    if not task_info['active']:
        return jsonify({'success': False, 'error': 'Task already stopped'}), 400
    
    # Security: Check authorization
    if task_info['owner_id'] != requester_id:
        return jsonify({'success': False, 'error': 'Unauthorized - You can only stop your own tasks'}), 403
    
    # Stop the task
    task_info['active'] = False
    add_log(f"🛑 Task {task_id} stopped by owner {requester_id}", "error")
    
    return jsonify({'success': True, 'message': f'Task {task_id} stopped successfully'})

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    task_list = []
    for task_id, task_info in tasks.items():
        duration = datetime.now() - task_info['start_time']
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        task_list.append({
            'task_id': task_id,
            'owner_id': task_info['owner_id'],
            'active': task_info['active'],
            'target_name': task_info['target_name'],
            'messages_sent': task_info['total_messages'],
            'duration': f"{hours}h {minutes}m"
        })
    return jsonify(task_list)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    active_tasks = sum(1 for task in tasks.values() if task['active'])
    return jsonify({
        'total_tasks': len(tasks),
        'active_tasks': active_tasks,
        'total_messages': total_messages_sent
    })

@app.route('/logs', methods=['GET'])
def get_logs():
    return jsonify({'logs': logs[-50:]})

if __name__ == '__main__':
    add_log("🚀 Task System Started Successfully!", "success")
    add_log("🔐 Each task is owned by a unique user ID", "info")
    add_log("✅ Only task owners can stop their tasks", "info")
    add_log("📅 365 Days continuous run mode active", "info")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
