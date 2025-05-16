from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import time

app = Flask(__name__, static_folder='templates/assets')
CORS(app)

lighting_values = [0, 0, 0, 0, 0, 0]
schedules = [
    []
]

# Store the last local interaction timestamp
last_local_interaction = 0
LOCAL_LOCK_TIMEOUT = 5  # seconds

def is_local_request():
    return request.remote_addr in ('127.0.0.1', '::1')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/lock_status')
def lock_status():
    global last_local_interaction
    import time
    return jsonify({
        "local_lock": (time.time() - last_local_interaction < LOCAL_LOCK_TIMEOUT)
    })

@app.route('/api/state', methods=['GET', 'POST'])
def state():
    global last_local_interaction, lighting_values, schedules

    if request.method == 'POST':
        data = request.get_json()
        now = time.time()
        if is_local_request():
            last_local_interaction = now
            print("[LOCAL] Received from frontend:", data)
        else:
            if now - last_local_interaction < LOCAL_LOCK_TIMEOUT:
                print("[REMOTE BLOCKED] Local interface in use.")
                return jsonify({"status": "locked", "message": "Manual interface in use"}), 423
            print("[REMOTE] Received from frontend:", data)
        # Update global state
        if data.get('lighting'):
            lighting_values = data['lighting']
        if data.get('scheduleData') and data['scheduleData'].get('schedules'):
            schedules = data['scheduleData']['schedules']
        return jsonify({"status": "ok", "received": data})
    else:
        schedule_dict = {
            "scheduleCount": len(schedules),
            "schedules": schedules
        }
        result = {
            "lighting": lighting_values,
            "scheduleData": schedule_dict
        }
        return jsonify(result)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug=True, port=8080)