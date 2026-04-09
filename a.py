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
    print(f"Searching for hardware on {SERIAL_PORT}...")
    
    while True:
        try:
            # Attempt to connect to the real sensor
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"SUCCESS: Connected to {SERIAL_PORT}. Using real sensor data.", flush=True)
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
                            
                            # Detect tampering based on rapid changes
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
            # FALLBACK TO SIMULATION if hardware is missing
            print(f"Hardware not found on {SERIAL_PORT} ({e}). Entering Simulation Mode...", flush=True)
            current_data["device_connected"] = True # Keep UI active
            
            # Simulation loop
            while True:
                try:
                    # Randomly jitter data
                    current_data["temperature"] += random.uniform(-0.1, 0.1)
                    current_data["humidity"] += random.uniform(-0.2, 0.2)
                    
                    # Bounds
                    current_data["temperature"] = max(20.0, min(current_data["temperature"], 40.0))
                    current_data["humidity"] = max(40.0, min(current_data["humidity"], 80.0))
                    
                    # Periodic tamper simulation
                    current_data["tampered"] = random.random() < 0.02
                    if current_data["tampered"]:
                        current_data["temperature"] += random.uniform(8, 15)
                        print("SIMULATED TAMPER DETECTED!", flush=True)

                    socketio.emit('telemetry_update', current_data)
                    print(f"Simulated Data -> {current_data.get('temperature', 0):.1f}C | {current_data.get('humidity', 0):.1f}%", flush=True)
                    
                    # Every 10 simulation cycles, try to check if the real device was plugged in
                    for _ in range(10):
                        time.sleep(1)
                    
                    # Try to probe serial port again
                    test_ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
                    test_ser.close()
                    print(f"Hardware detected on {SERIAL_PORT}! Reconnecting...", flush=True)
                    break # Break simulation loop to retry the real serial connection
                    
                except Exception:
                    # Still no hardware, stay in simulation
                    continue

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('telemetry_update', current_data)

import requests

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
    email = payload.get('email', 'allenchandev25@gmail.com')
    message = payload.get('message', 'Alert triggered')
    
    print(f"\n>>> [ALERT] Triggering ntfy for: {email}", flush=True)
    
    try:
        # NOTE: ntfy.sh anonymous email is restricted, but mobile push is free.
        # Removing the 'email' field allows the mobile push to succeed.
        ntfy_data = {
            "topic": "iot_alert_allen",
            "message": message,
            "title": "SECURITY ALERT: IoT Tampering",
            "priority": 5,
            "tags": ["siren", "warning"]
        }
        
        response = requests.post("https://ntfy.sh/", json=ntfy_data, timeout=10)
        
        if response.status_code == 200:
            print(f">>> [NTFY] MOBILE PUSH SUCCESS: {response.text}", flush=True)
            print(f">>> [INFO] Mobile notification sent to topic 'iot_alert_allen'.", flush=True)
        else:
            print(f">>> [NTFY] FAILED (Status {response.status_code}): {response.text}", flush=True)
            
    except Exception as e:
        print(f">>> [NTFY] REQUEST ERROR: {e}", flush=True)

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
                print("NETWORK TAMPER DETECTED!!! External payload flagged.", flush=True)
                
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