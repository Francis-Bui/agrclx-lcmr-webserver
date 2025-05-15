from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

app = Flask(__name__, static_folder='templates/assets')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/state', methods=['GET', 'POST'])
def state():
    if request.method == 'POST':
        data = request.get_json()
        print("Received from frontend:", data)  # Debug print
        return jsonify({"status": "ok", "received": data})
    else:
        # Lighting format: [IR, R, G, B, W, UV]; each value is an integer from 0-100
        lighting_values = [0, 0, 0, 0, 0, 0]
        # Schedule format: [scheduleEnabled, startTime, endTime, IR, R, G, B, W, UV]
        schedules = [
            [False, 0, 2400, False, False, False, False, False, False]
        ]
        schedule_dict = {
            "scheduleCount": len(schedules),
            "schedules": schedules
        }
        result = {
            "lighting": lighting_values,
            "scheduleData": schedule_dict
        }
        print(result)
        return jsonify(result)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug=True, port=5000)