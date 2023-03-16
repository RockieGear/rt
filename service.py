import os
import sys
import socket
import threading
import asyncio
import random
from flask import Flask, render_template_string, jsonify

def get_ssh_port():
    ssh_config_path = '/etc/ssh/sshd_config'
    port = 22  # default SSH port

    try:
        with open(ssh_config_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('Port ') and not line.startswith('#'):
                    port = int(line.split()[1])
                    break
    except FileNotFoundError:
        print(f"Warning: {ssh_config_path} not found. Using default SSH port 22.")

    return port


app = Flask(__name__)
tunnels = {}

html_template = '''<!DOCTYPE html>
<html>
<head>
  <title>SSH Tunnels</title>
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
  <style>
    .tunnel { margin: 5px; padding: 5px; border: 1px solid black; display: inline-block; }
    .tunnel:hover { cursor: pointer; background-color: #f0f0f0; }
  </style>
  <script>
    function copyToClipboard(text) {
      var $temp = $("<input>");
      $("body").append($temp);
      $temp.val(text).select();
      document.execCommand("copy");
      $temp.remove();
    }

    function refreshTunnels() {
      $.getJSON('/tunnels', function(data) {
        $('#tunnels').empty();
        $.each(data, function(key, val) {
          $('#tunnels').append('<div class="tunnel" onclick="copyToClipboard(\'' + val + '\')">' + key + ': ' + val + '</div>');
        });
      });
    }

    $(document).ready(function() {
      refreshTunnels();
      setInterval(refreshTunnels, 10000);
    });
  </script>
</head>
<body>
  <div id="tunnels"></div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(html_template)

@app.route('/tunnels')
def get_tunnels():
    return jsonify(tunnels)

def monitor_tunnel(remote_port, local_port):
    while True:
        try:
            conn = socket.create_connection(('127.0.0.1', local_port))
            conn.close()
            time.sleep(5)
        except:
            del tunnels[remote_port]
            break

def handle_client(sock):
    try:
        data = sock.recv(1024).decode('utf-8')
        remote_port = int(data.split(' ')[-1].strip())
        local_port = unused_port()
        tunnels[remote_port] = f'127.0.0.1:{local_port}'
        os.system(f'ssh -f -N -L {local_port}:127.0.0.1:{remote_port} localhost')
        monitor_thread = threading.Thread(target=monitor_tunnel, args=(remote_port, local_port))
        monitor_thread.start()
    except Exception as e:
        print(e)
    finally:
        sock.close()

def start_ssh_server(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('', port))
    server.listen(100)

    while True:
        try:
            client, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client,))
            thread.start()
        except Exception as e:
            print(e)

def unused_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

if __name__ == '__main__':
    ssh_port = get_ssh_port()
    threading.Thread(target=start_ssh_server, args=(ssh_port,)).start()
    app.run(host='0.0.0.0', port=5000)

