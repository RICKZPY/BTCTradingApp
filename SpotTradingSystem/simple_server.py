#!/usr/bin/env python3
"""
简单的HTTP服务器用于演示Web界面
"""

import http.server
import socketserver
import webbrowser
import os
from threading import Timer

PORT = 8080

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def open_browser():
    """延迟打开浏览器"""
    webbrowser.open(f'http://localhost:{PORT}/web-demo/index.html')

if __name__ == "__main__":
    # 切换到项目根目录
    os.chdir('.')
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🌐 启动Web服务器在端口 {PORT}")
        print(f"📱 访问地址: http://localhost:{PORT}/web-demo/index.html")
        print("按 Ctrl+C 停止服务器")
        
        # 1秒后自动打开浏览器
        Timer(1.0, open_browser).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务器已停止")