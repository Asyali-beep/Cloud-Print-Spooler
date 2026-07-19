# 🖨️ Cloud-to-Local Print Spooler (Hardware Bridge)

![Python](https://img.shields.io/badge/Python-3.x-3776AB.svg?logo=python)
![PHP](https://img.shields.io/badge/PHP-8.x-777BB4.svg?logo=php)
![Windows](https://img.shields.io/badge/OS-Windows_|_Linux-brightgreen)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

A resilient local hardware agent and cloud API designed to bridge the gap between cloud-based applications (like POS systems, WMS, or ERPs) and local network receipt printers (ESC/POS).

## 📖 The Backstory: Surviving the Monolith

Every architecture has a birth story. This solution wasn't born in a vacuum; it was forged in the fires of a massive monolithic legacy system. If you want to read the engineering journey of how I rescued a SaaS from spaghetti code and transformed it into a scalable, hardware-integrated architecture, check out the full story:

*   🇬🇧 **English:** [The Monolith Survival Guide: Rescuing a SaaS from Spaghetti Code](https://asyali-beep.hashnode.dev/the-monolith-survival-guide-rescuing-a-saas-from-spaghetti-code-to-scalable-architecture)
*   🇹🇷 **Türkçe:** [Monolitik Bir Projede Hayatta Kalma Rehberi](https://www.linkedin.com/pulse/monolitik-bir-projede-hayatta-kalma-rehberi-cumaali-eren-pxdvf/)

---

## 🧠 The Architecture & Defense in Depth

Web browsers cannot directly communicate with local TCP/IP or USB hardware printers due to strict security sandboxes. This project solves that problem by introducing a highly fault-tolerant local **Print Agent**.

### 1. Connection Fallback (WS -> Long-Polling)
The agent is designed to maintain a persistent connection to the cloud queue. If the primary real-time connection (WebSocket) drops due to network instability, the agent seamlessly degrades to an **HTTP Long-Polling (Wake)** mechanism to ensure zero print jobs are missed.

### 2. Transport Fallback (TCP/IP -> Win32 Spooler)
Printers often change IP addresses or face network isolation. The agent implements a dynamic routing fallback mechanism:
1. **TCP Raw Socket:** Attempts to send the ESC/POS payload directly to port `9100`.
2. **Win32 Spooler Fallback:** If the TCP connection fails (or times out) and the host OS is Windows, the agent dynamically imports `pywin32` and passes the RAW payload directly to the Windows Spooler API as a native `StartDocPrinter` job.

## 🚀 Key Features
*   **Guaranteed Delivery (ACK/NACK):** Implements a strict `Fetch -> Print -> ACK` loop. If printing fails across all transports, the job is NACKed and routed to a Dead-Letter Queue.
*   **Protocol Agnostic:** Handles Raw ESC/POS bytes dynamically without requiring specific printer drivers.
*   **Secure Auth:** Uses Bearer token authentication to prevent unauthorized queue fetching.

## 🛠️ Quick Start

**1. Start the Cloud API (Mock Server)**
```bash
cd backend-php
php -S localhost:8000
```

**2. Start the Local Print Agent**
```bash
cd local-agent
export API_ENDPOINT="http://localhost:8000/api.php"
python print_agent.py
```
> **Note for Windows Users:** To test the Win32 Spooler fallback, ensure you have the library installed via `pip install pywin32`.
