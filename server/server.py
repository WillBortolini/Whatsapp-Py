import socket
import threading

clients = {}
lock = threading.Lock()

def broadcast(message, sender_phone=None):
    with lock:
        for phone, (name, conn) in clients.items():
            if phone != sender_phone:
                try:
                    conn.sendall(message.encode('utf-8'))
                except:
                    pass

def handle_client(conn, addr):
    try:
        conn.sendall("Digite seu nome: ".encode('utf-8'))
        name = conn.recv(1024).decode('utf-8').strip()

        conn.sendall("Digite seu número: ".encode('utf-8'))
        phone = conn.recv(1024).decode('utf-8').strip()

        with lock:
            clients[phone] = (name, conn)

        print(f"[+] {name} ({phone}) conectado de {addr}")
        conn.sendall(f"Bem-vindo ao chat, {name}!\n".encode('utf-8'))

        while True:
            data = conn.recv(1024).decode('utf-8').strip()
            if not data:
                break

            if data.startswith("/all "):
                msg = data[5:]
                print(f"[Broadcast] {name}: {msg}")
                broadcast(f"{name} (Todos): {msg}", sender_phone=phone)

            elif data.startswith("/to "):
                try:
                    parts = data.split(" ", 2)
                    target_phone = parts[1]
                    msg = parts[2]
                    with lock:
                        if target_phone in clients:
                            target_conn = clients[target_phone][1]
                            target_conn.sendall(f"{name} (Privado): {msg}".encode('utf-8'))
                        else:
                            conn.sendall("Usuário não encontrado.\n".encode('utf-8'))
                except:
                    conn.sendall("Formato inválido. Use /to <numero> <mensagem>\n".encode('utf-8'))

            else:
                conn.sendall("Comando desconhecido.\n".encode('utf-8'))

    except Exception as e:
        print(f"[!] Erro com cliente {addr}: {e}")
    finally:
        with lock:
            for phone, (n, c) in list(clients.items()):
                if c == conn:
                    del clients[phone]
                    break
        conn.close()
        print(f"[-] Cliente {addr} desconectado")

def start_server(host='0.0.0.0', port=5000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    print(f"Servidor rodando em {host}:{port}...")

    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
