# Edgelytics: Edge-Based Data Integrity Verification for IoT Streams

Edgelytics is a lightweight framework designed to ensure the integrity of data streams coming from IoT devices. By performing verification at the edge, the system reduces the risk of data tampering and ensures that only authentic, unaltered data reaches the backend or the end-user interface.

## 🚀 Overview

In modern IoT ecosystems, data integrity is critical. Edgelytics addresses this by:
1.  **Sensing:** Collecting real-time data from sensors via hardware (Arduino/ESP32).
2.  **Processing:** Using a Python-based edge controller to verify and sign data packets.
3.  **Visualization:** Displaying the verified data on a web-based dashboard.

## 🛠️ Tech Stack

-   **Hardware:** C++/Arduino (Sensor data collection)
-   **Backend/Edge Logic:** Python (Data verification and processing)
-   **Frontend:** HTML/JavaScript (Dashboard visualization)
-   **Security:** Integrity verification algorithms (e.g., Hashing/MAC)

## 📁 Repository Structure

-   `/sketch_mar23a`: Arduino source code for the IoT node.
-   `a.py`: Python script for edge processing and integrity checks.
-   `index.html`: Web interface for monitoring data streams.
-   `LICENSE`: MIT License.

## ⚙️ Getting Started

### Prerequisites

-   **Arduino IDE** for uploading code to your microcontroller.
-   **Python 3.x** installed on your machine (Fedora: `sudo dnf install python3`).
-   Any modern web browser.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/allenchandev25-del/Edgelytics.git](https://github.com/allenchandev25-del/Edgelytics.git)
    cd Edgelytics
    ```

2.  **Hardware Setup:**
    -   Open `sketch_mar23a/sketch_mar23a.ino` in the Arduino IDE.
    -   Connect your board and upload the sketch.

3.  **Run the Edge Controller:**
    ```bash
    python3 a.py
    ```

4.  **View the Dashboard:**
    -   Open `index.html` in your browser to see the real-time verified data.

## 🛡️ Security Features

-   **Data Integrity:** Implements verification checks to detect "Man-in-the-Middle" (MitM) attacks on IoT streams.
-   **Edge Efficiency:** Processing is handled locally to reduce latency and bandwidth.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
