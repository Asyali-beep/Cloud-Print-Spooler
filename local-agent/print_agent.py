import os
import time
import json
import base64
import urllib.request
import urllib.parse
import urllib.error
import socket
import platform

class CloudPrintAgent:
    def __init__(self, api_url, token):
        self.api_url = api_url
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        self.poll_interval = 3.0
        self.ws_active = True 

    def request(self, data=None, timeout=10):
        req_url = self.api_url
        if data and 'action' in data and data['action'] == 'fetch':
            query = urllib.parse.urlencode(data)
            req_url = f"{self.api_url}?{query}"
            body = None
        elif data:
            body = urllib.parse.urlencode(data).encode('utf-8')
        else:
            body = None

        req = urllib.request.Request(req_url, data=body, headers=self.headers)
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.URLError as e:
            return None
        except json.JSONDecodeError:
            return None

    def send_to_printer_tcp(self, ip, port, payload_bytes):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5.0)
                s.connect((ip, port))
                s.sendall(payload_bytes)
            return True, "Printed successfully via TCP/IP"
        except Exception as e:
            return False, f"TCP Error: {e}"

    def send_to_printer_win32(self, printer_name, payload_bytes):
        try:
            import win32print
            hprinter = win32print.OpenPrinter(printer_name)
            try:
                win32print.StartDocPrinter(hprinter, 1, ("CloudPrintJob", None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                win32print.WritePrinter(hprinter, payload_bytes)
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
                return True, "Printed successfully via Windows Spooler"
            finally:
                win32print.ClosePrinter(hprinter)
        except ImportError:
            return False, "pywin32 library is missing"
        except Exception as e:
            return False, f"Win32 Spooler Error: {e}"

    def run(self):
        print("[INFO] Cloud Print Agent started.")
        
        while True:
            if not self.ws_active:
                print("[WARN] WebSocket connection lost. Falling back to HTTP Long-Polling (Wake)...")
            
            job = self.request({'action': 'fetch'}, timeout=15)
            
            if not job or job.get('status') != 'success' or not job.get('job_id'):
                time.sleep(self.poll_interval)
                continue

            job_id = job['job_id']
            payload = base64.b64decode(job['content'])
            transport_mode = job.get('transport_preference', 'auto')
            
            print(f"\n[INFO] Processing Job: {job_id} | Mode: {transport_mode}")
            
            success = False
            msg = "No compatible transport found"

            if transport_mode in ['tcp', 'auto'] and job.get('printer_ip'):
                ip = job['printer_ip']
                port = int(job.get('printer_port', 9100))
                print(f"[DEBUG] Attempting TCP socket connection to {ip}:{port}...")
                success, msg = self.send_to_printer_tcp(ip, port, payload)

            if not success and transport_mode in ['win32', 'auto'] and platform.system() == "Windows":
                printer_name = job.get('windows_printer_name', 'Default')
                print(f"[DEBUG] TCP failed. Attempting Win32 RAW Spooler fallback for '{printer_name}'...")
                success, msg = self.send_to_printer_win32(printer_name, payload)

            if success:
                print(f"[SUCCESS] {msg}")
                self.request({'action': 'ack', 'job_id': job_id})
            else:
                print(f"[ERROR] Job {job_id} failed: {msg}")
                self.request({'action': 'fail', 'job_id': job_id, 'reason': msg})

            time.sleep(self.poll_interval)

if __name__ == "__main__":
    AGENT_TOKEN = os.environ.get("AGENT_TOKEN", "default_secure_token_123")
    API_ENDPOINT = os.environ.get("API_ENDPOINT", "http://localhost:8000/api.php")
    
    agent = CloudPrintAgent(API_ENDPOINT, AGENT_TOKEN)
    agent.run()