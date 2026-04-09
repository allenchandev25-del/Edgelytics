import serial
import json
import time
import random
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import threading
from typing import Dict, Any

SERIAL_PORT = 'COM10'  
BAUD_RATE = 9600
SIMULATE = True      # Set to True to enable "Virtual Display" mode by default
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

current_data: Dict[str, Any] = {
    "temperature": 24.5,
    "humidity": 55.0,
    "tampered": False,
    "device_connected": False
}

def read_serial():
    global current_data
    while True:
        if not SIMULATE:
            try:
                ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                print(f"Connected to {SERIAL_PORT}", flush=True)
                current_data["device_connected"] = True
                socketio.emit('telemetry_update', current_data)
                while True:
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if "temperature" in data and "humidity" in data:
                                t = float(data["temperature"])
                                h = float(data["humidity"])
                                
                                # Detect tampering based on physically impossible rapid changes
                                tampered = False
                                if abs(t - current_data["temperature"]) > 5.0 or abs(h - current_data["humidity"]) > 10.0:
                                    tampered = True
                                    print("TAMPER DETECTED! Data impossible.", flush=True)
                                
                                current_data.update(data)
                                current_data["tampered"] = tampered
                                
                            socketio.emit('telemetry_update', current_data)
                            print(f"Real Data -> {current_data}", flush=True)
                        except json.JSONDecodeError:
                            print(f"Error parsing JSON: {line}")
                    else:
                        time.sleep(0.05)
            except Exception as e:
                if current_data.get("device_connected", True):
                    current_data["device_connected"] = False
                    socketio.emit('telemetry_update', current_data)
                print(f"Serial Error/Disconnected: {e}. Retrying in 3 seconds...", flush=True)
                time.sleep(3)
        else:
            # SIMULATION MODE (Virtual Display Logic)
            current_data["device_connected"] = True
            # Randomly jitter data
            current_data["temperature"] += random.uniform(-0.2, 0.2)
            current_data["humidity"] += random.uniform(-0.5, 0.5)
            
            # Keep values in realistic bounds
            current_data["temperature"] = max(18.0, min(current_data["temperature"], 45.0))
            current_data["humidity"] = max(30.0, min(current_data["humidity"], 90.0))
            
            # 5% chance of a random "Tamper" spike during simulation for testing
            current_data["tampered"] = random.random() < 0.05
            if current_data["tampered"]:
                current_data["temperature"] += random.uniform(10, 20)
                print("🚨 SIMULATED TAMPER DETECTED!", flush=True)

            socketio.emit('telemetry_update', current_data)
            print(f"Simulated Data -> {current_data}", flush=True)
            time.sleep(2) # Send data every 2 seconds

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('telemetry_update', current_data)

import urllib.request
import urllib.parse
@app.route('/send-alert', methods=['POST', 'OPTIONS'])
def send_alert():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        headers = request.headers.get('ACCESS_CONTROL_REQUEST_HEADERS')
        h = response.headers
        h['Access-Control-Allow-Origin'] = '*'
        h['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        if headers:
            h['Access-Control-Allow-Headers'] = headers
        return response
    
    payload = request.json or {}
    phone = payload.get('phoneNumber', '9487432081')
    email = payload.get('email', 'allenchandev25@gmail.com')
    message = payload.get('message', 'Alert')
    print(f"\n\n>>> [ALERT TRIGGERED] Sending to mobile and email...\n\n", flush=True)
    
    # 1. Email and Push via ntfy
    try:
        # Using X- headers which are the official standard for ntfy
        req_ntfy = urllib.request.Request(
            'https://ntfy.sh/iot_alert_allen', 
            data=message.encode('utf-8'), 
            headers={
                'X-Email': email,
                'X-Title': '🚨 SECURITY ALERT: IoT Tampering',
                'X-Priority': '5',
                'X-Tags': 'siren,warning'
            }
        )
        with urllib.request.urlopen(req_ntfy) as res:
            status = res.getcode()
            response_body = res.read().decode('utf-8')
            print(f">>> [NTFY] Status: {status} | Response: {response_body}", flush=True)
            print(f">>> [NTFY] Alert sent successfully to topic 'iot_alert_allen' and email '{email}'", flush=True)
    except Exception as e:
        print(f">>> [NTFY] CRITICAL ERROR: {e}", flush=True)

    resp = jsonify({"status": "Alert Processed"})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp, 200

# --- EXTERNAL TESTING API ---
@app.route('/test_anomaly', methods=['POST'])
def test_anomaly():
    global current_data
    try:
        payload = request.json
        if "temperature" in payload and "humidity" in payload:
            t = float(payload["temperature"])
            h = float(payload["humidity"])
            
            # Run the anomaly detection logic on this external payload
            tampered = False
            if abs(t - current_data["temperature"]) > 5.0 or abs(h - current_data["humidity"]) > 10.0:
                tampered = True
                print("🚨 NETWORK TAMPER DETECTED!!! External payload flagged.", flush=True)
                
            current_data["temperature"] = t
            current_data["humidity"] = h
            current_data["tampered"] = tampered
            
            socketio.emit('telemetry_update', current_data)
            return jsonify({"status": "Success", "tampered_flagged": tampered}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"error": "Invalid payload"}), 400

if __name__ == '__main__':
    threading.Thread(target=read_serial, daemon=True).start()
    
    print("Python Bridge Server running on http://localhost:5001")
    socketio.run(app, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)