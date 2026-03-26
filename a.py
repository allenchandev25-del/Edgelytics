import serial
import json
import time
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import threading
from typing import Dict, Any

SERIAL_PORT = 'COM10'  
BAUD_RATE = 9600
SIMULATE = False     
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

current_data: Dict[str, Any] = {
    "temperature": 0.0,
    "humidity": 0.0,
    "tampered": False,
    "device_connected": False
}

def read_serial():
    global current_data
    while True:
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
                                print("🚨 TAMPER DETECTED! Data impossible.", flush=True)
                            
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
    print(f"\n\n>>> [ALERT TRIGGERED] Requesting to send alerts...\n\n", flush=True)
    
    # 1. Email via ntfy (Completely Free & Reliable)
    try:
        req_email = urllib.request.Request('https://ntfy.sh/iot_alert_allen', data=message.encode('utf-8'), headers={'Email': email})
        with urllib.request.urlopen(req_email) as res:
            print(f">>> [EMAIL] Sent perfectly to {email}!", flush=True)
    except Exception as e:
        print(f">>> [EMAIL] Error sending to {email}: {e}", flush=True)

    # 2. Mobile Push Notification via Ntfy (Instant & Free)
    # The payload sent to 'iot_alert_allen' in step 1 already triggers push notifications 
    # directly to your phone if you have the Ntfy app! No extra code needed.
    print(f">>> [PHONE PUSH] To receive this instantly on your phone like an SMS:", flush=True)
    print(f"    1. Download the free 'ntfy' app on your iOS / Android device.", flush=True)
    print(f"    2. Subscribe to the topic: iot_alert_allen", flush=True)
        
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
                print("🚨 NETWORK TAMPER DETECTED! External payload flagged.", flush=True)
                
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
    socketio.run(app, host='0.0.0.0', port=5001)