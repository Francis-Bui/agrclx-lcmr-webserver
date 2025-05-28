from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import eventlet
import time
import os
import json
import threading
import csv
import signal
import sys

def graceful_exit(signum, frame):
    print("Shutting down webhandler...")
    log_event('Webserver shutdown (signal)', 'success')
    sys.exit(0)

signal.signal(signal.SIGTERM, graceful_exit)
signal.signal(signal.SIGINT, graceful_exit)
'''
webhandler.py
-------------
This is the Flask backend for the lighting control system. It provides:
  - REST API endpoints for lighting state, profiles, and schedules
  - WebSocket support for real-time slider updates
  - File-based storage for profiles and schedules (JSON on disk)
  - Local lockout logic to prevent remote changes during local use
  - Thread safety for concurrent access to profile/schedule files

All API endpoints are documented with comments. This backend is designed for easy integration with the Vue frontend and supports multi-client real-time sync.
'''

eventlet.monkey_patch()

app = Flask(__name__, static_folder='templates/assets')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

STATE_FILE = 'state.json'
PROFILE_DIR = os.path.expanduser("~/Desktop/LCMR/profiles")
PROFILE_LOCK = threading.Lock()

SCHEDULE_DIR = os.path.expanduser("~/Desktop/LCMR/schedules")
SCHEDULE_LOCK = threading.Lock()

LOGS_DIR = os.path.expanduser("~/Desktop/LCMR/logs")
LED_HISTORY_CSV = os.path.join(LOGS_DIR, "LED_history.csv")
EVENT_HISTORY_CSV = os.path.join(LOGS_DIR, "event_history.csv")

# Ensure profile and schedule directories exist
os.makedirs(PROFILE_DIR, exist_ok=True)
os.makedirs(SCHEDULE_DIR, exist_ok=True)

def load_state():
    # Load lighting and schedule state from disk (if exists)
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
    # Save lighting and schedule state to disk
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

LIGHTING_COND = threading.Condition()

# For slider change event logging cooldown
SLIDER_LOG_COOLDOWN = 1.0  # seconds
last_slider_log_time = 0
last_slider_log_values = None
slider_log_timer = None
pending_slider_log = None
pending_slider_log_first = None

import threading

def log_slider_change(prev, new):
    log_event(f"Intensity values changed from {prev} to {new}", "success")

@app.route('/api/state', methods=['GET', 'POST'])
def state():
    global last_local_interaction, lighting_values, schedules
    global last_slider_log_time, last_slider_log_values, slider_log_timer, pending_slider_log, pending_slider_log_first

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
        lighting_changed = False
        if data.get('lighting'):
            if data['lighting'] != lighting_values:
                lighting_changed = True
                prev = lighting_values
                new = data['lighting']
                # Cancel any existing timer
                if slider_log_timer is not None:
                    slider_log_timer.cancel()
                # On first change in a burst, record the initial value
                if pending_slider_log_first is None:
                    pending_slider_log_first = prev.copy() if hasattr(prev, 'copy') else list(prev)
                # Always update the latest value
                pending_slider_log = new.copy() if hasattr(new, 'copy') else list(new)
                # Start a new timer
                def do_log():
                    global last_slider_log_time, last_slider_log_values, slider_log_timer, pending_slider_log, pending_slider_log_first
                    log_slider_change(pending_slider_log_first, pending_slider_log)
                    last_slider_log_time = time.time()
                    last_slider_log_values = pending_slider_log
                    slider_log_timer = None
                    pending_slider_log = None
                    pending_slider_log_first = None
                slider_log_timer = threading.Timer(SLIDER_LOG_COOLDOWN, do_log)
                slider_log_timer.start()
            lighting_values = data['lighting']
        if data.get('scheduleData') and data['scheduleData']:
            schedules = data['scheduleData']['schedules']
        save_state(lighting_values, schedules)
        if lighting_changed:
            with LIGHTING_COND:
                LIGHTING_COND.notify_all()
            # Emit slider update to all websocket clients
            socketio.emit('slider_update', {'lighting': lighting_values})
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
    # List all saved lighting profiles from disk
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

def list_schedules():
    # List all saved schedules from disk
    schedules = []
    for fname in os.listdir(SCHEDULE_DIR):
        if fname.endswith(".json"):
            try:
                with open(os.path.join(SCHEDULE_DIR, fname), 'r') as f:
                    data = json.load(f)
                    schedules.append(data)
            except Exception:
                continue
    return schedules

@app.route('/api/schedules', methods=['GET', 'POST', 'PUT', 'DELETE'])
def schedules_api():
    """
    GET: List all schedules
    POST: Create new schedule {title, start, end, profile_name, profile_values, enabled}
    PUT: Edit schedule {id, ...fields}
    DELETE: Delete schedule {id}
    """
    if request.method == 'GET':
        try:
            with SCHEDULE_LOCK:
                schedules = list_schedules()
            return jsonify({'schedules': schedules}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'POST':
        data = request.get_json()
        required = ['title', 'start', 'end', 'profile_name', 'profile_values', 'enabled']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing fields'}), 400
        schedule_id = str(int(time.time() * 1000))
        fname = os.path.join(SCHEDULE_DIR, f'{schedule_id}.json')
        schedule = {
            'id': schedule_id,
            'title': data['title'],
            'start': data['start'],
            'end': data['end'],
            'profile_name': data['profile_name'],
            'profile_values': data['profile_values'],
            'enabled': data['enabled']
        }
        with SCHEDULE_LOCK:
            try:
                with open(fname, 'w') as f:
                    json.dump(schedule, f)
                return jsonify({'status': 'created', 'schedule': schedule}), 201
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    elif request.method == 'PUT':
        data = request.get_json()
        schedule_id = data.get('id')
        if not schedule_id:
            return jsonify({'error': 'Missing id'}), 400
        fname = os.path.join(SCHEDULE_DIR, f'{schedule_id}.json')
        with SCHEDULE_LOCK:
            if not os.path.exists(fname):
                return jsonify({'error': 'Schedule not found'}), 404
            try:
                with open(fname, 'w') as f:
                    json.dump(data, f)
                return jsonify({'status': 'updated', 'schedule': data}), 200
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        data = request.get_json()
        schedule_id = data.get('id')
        if not schedule_id:
            return jsonify({'error': 'Missing id'}), 400
        fname = os.path.join(SCHEDULE_DIR, f'{schedule_id}.json')
        with SCHEDULE_LOCK:
            if not os.path.exists(fname):
                return jsonify({'error': 'Schedule not found'}), 404
            try:
                os.remove(fname)
                return jsonify({'status': 'deleted'}), 200
            except Exception as e:
                return jsonify({'error': str(e)}), 500

@app.route('/api/logs/led_history', methods=['GET'])
def led_history():
    """
    GET: Return LED history as a list of dicts from the CSV file.
    """
    if not os.path.exists(LED_HISTORY_CSV):
        return jsonify({'history': []}), 200
    history = []
    try:
        with open(LED_HISTORY_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=["timestamp", "IR", "R", "G", "B", "W", "UV"])
            for row in reader:
                # Optionally convert numeric fields
                for k in ["IR", "R", "G", "B", "W", "UV"]:
                    try:
                        row[k] = float(row[k])
                    except Exception:
                        pass
                history.append(row)
        return jsonify({'history': history}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def log_event(action, status):
    """Append an event to the event_history.csv with timestamp, action, and status (success/error)."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    with open(EVENT_HISTORY_CSV, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([time.strftime('%Y-%m-%dT%H:%M:%S'), action, status])

@app.route('/api/logs/event_history', methods=['POST'])
def add_event():
    """POST: Add an event to the event_history.csv."""
    data = request.get_json()
    action = data.get('action')
    status = data.get('status')
    if not action or not status:
        return jsonify({'error': 'Missing action or status'}), 400
    try:
        log_event(action, status)
        return jsonify({'status': 'logged'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/event_history', methods=['GET'])
def get_event_history():
    """GET: Return event history as a list of dicts from the CSV file."""
    if not os.path.exists(EVENT_HISTORY_CSV):
        return jsonify({'history': []}), 200
    history = []
    try:
        with open(EVENT_HISTORY_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=["timestamp", "action", "status"])
            for row in reader:
                history.append(row)
        return jsonify({'history': history}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    # On WebSocket connect, send current lighting state
    emit('slider_update', {'lighting': lighting_values})

@socketio.on('get_state')
def handle_get_state():
    # On WebSocket request, send current lighting state
    emit('slider_update', {'lighting': lighting_values})

if __name__ == '__main__':
    # Log webserver start
    log_event('Webserver started', 'success')
    try:
        # Start the Flask app with SocketIO
        socketio.run(app, host = '0.0.0.0', debug=True, use_reloader=False, port=8080)
    finally:
        # Log webserver shutdown
        log_event('Webserver shutdown', 'success')
