# =============================================================================
# server.py — Cross-Device Local Web Server Launcher
# =============================================================================
# Run this script on Windows/Mac to serve the Matrix Camera Web App locally
# across all devices (Mobile phones, Tablets, Laptops) connected to your Wi-Fi!

import http.server
import socket
import socketserver
import os
import sys
import webbrowser

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')

def get_local_ip():
    """Find local network IP address (e.g. 192.168.1.X)"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

def main():
    os.chdir(WEB_DIR)
    local_ip = get_local_ip()
    local_url = f"http://localhost:{PORT}"
    network_url = f"http://{local_ip}:{PORT}"

    print("===============================================================")
    print(" MATRIX CAMERA — CROSS-DEVICE WEB & MOBILE SERVER")
    print("===============================================================")
    print(f" [*] Local PC URL : {local_url}")
    print(f" [*] Mobile / Wi-Fi URL: {network_url}")
    print("---------------------------------------------------------------")
    print(" Open the Mobile URL on your iPhone/Android phone to use it live!")
    print(" Press Ctrl+C to stop the server.")
    print("===============================================================\n")

    # Automatically open local browser
    try:
        webbrowser.open(local_url)
    except Exception:
        pass

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[INFO] Server stopped gracefully.")
            sys.exit(0)

if __name__ == '__main__':
    main()
