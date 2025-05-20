from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import time
import os
import json
import threading

app = Flask(__name__, static_folder='templates/assets')
CORS(app)

STATE_FILE = 'state.json'
PROFILE_DIR = os.path.expanduser("~/Desktop/profiles")
PROFILE_LOCK = threading.Lock()

# Ensure profile directory exists
os.makedirs(PROFILE_DIR, exist_ok=True)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            try:
                state = json.load(f)
                return (
                    state.get('lighting_values', [0, 0, 0, 0, 0, 0]),
                    state.get('schedules', [])
                )
            except Exception:
                pass
    return [0, 0, 0, 0, 0, 0], []

def save_state(lighting_values, schedules):
    with open(STATE_FILE, 'w') as f:
        json.dump({
            'lighting_values': lighting_values,
            'schedules': schedules
        }, f)

lighting_values, schedules = load_state()

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
        if data.get('scheduleData') and data['scheduleData']:
            schedules = data['scheduleData']['schedules']
        save_state(lighting_values, schedules)
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

def list_profiles():
    profiles = []
    for fname in os.listdir(PROFILE_DIR):
        if fname.endswith(".json"):
            try:
                with open(os.path.join(PROFILE_DIR, fname), 'r') as f:
                    data = json.load(f)
                    profiles.append({
                        "name": data.get("name", fname[:-5]),
                        "values": data.get("values", [])
                    })
            except Exception:
                continue
    return profiles

@app.route('/api/profiles', methods=['GET', 'POST', 'PUT', 'DELETE'])
def profiles():
    """
    GET: List all profiles (name, values)
    POST: Save new profile (error on duplicate)
    PUT: Update existing profile
    DELETE: Delete profile by name
    """
    if request.method == 'GET':
        try:
            with PROFILE_LOCK:
                profiles = list_profiles()
            return jsonify({"profiles": profiles}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        values = data.get('values')
        if not name or values is None:
            return jsonify({"error": "Missing name or values"}), 400
        fname = os.path.join(PROFILE_DIR, f"{name}.json")
        with PROFILE_LOCK:
            if os.path.exists(fname):
                return jsonify({"error": "Profile with this name already exists"}), 409
            try:
                with open(fname, 'w') as f:
                    json.dump({"name": name, "values": values}, f)
                return jsonify({"status": "created"}), 201
            except Exception as e:
                return jsonify({"error": str(e)}), 500

    elif request.method == 'DELETE':
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify({"error": "Missing name"}), 400
        fname = os.path.join(PROFILE_DIR, f"{name}.json")
        with PROFILE_LOCK:
            if not os.path.exists(fname):
                return jsonify({"error": "Profile not found"}), 404
            try:
                os.remove(fname)
                return jsonify({"status": "deleted"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug=True, port=8080)