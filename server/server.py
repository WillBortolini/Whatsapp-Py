import socket
import threading

clients = {}
message_history = []
lock = threading.Lock()

def broadcast(message, sender_phone=None):
    with lock:
        for phone, (name, conn) in clients.items():
            if phone != sender_phone: 
                try:
                    conn.sendall(message.encode('utf-8'))
                except:
                    pass

def broadcast_user_list():
    with lock:
        users = [f"{name} ({phone})" for phone, (name, _) in clients.items()]
        msg = "/userlist " + "|".join(users)
        for _, (_, conn) in clients.items():
            try:
                conn.sendall(msg.encode('utf-8'))
            except:
                pass                

def handle_client(conn, addr):
    phone = None  # inicializa para uso no finally
    try:
        conn.sendall("Digite seu nome: ".encode('utf-8'))
        name = conn.recv(1024).decode('utf-8').strip()

        conn.sendall("Digite seu número: ".encode('utf-8'))
        phone = conn.recv(1024).decode('utf-8').strip()

        with lock:
            clients[phone] = (name, conn)
        broadcast_user_list()

        print(f"[+] {name} ({phone}) conectado de {addr}")
        conn.sendall(f"Bem-vindo ao chat, {name}!\n".encode('utf-8'))
        if message_history:
            conn.sendall("Histórico de mensagens:\n".encode('utf-8'))
            for m in message_history:
                conn.sendall(f"{m}\n".encode('utf-8'))

        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                data = data.decode('utf-8').strip()

                if data == "/quit":
                    break

                if data.startswith("/all "):
                    msg = data[5:]
                    full_msg = f"{name} (Todos): {msg}"
                    message_history.append(full_msg)
                    broadcast(full_msg, sender_phone=phone)
                    conn.sendall(full_msg.encode('utf-8'))  # envia só para o remetente

                elif data.startswith("/to "):
                    try:
                        parts = data.split(" ", 2)
                        target_phone = parts[1]
                        msg = parts[2]
                        with lock:
                            if target_phone in clients:
                                target_conn = clients[target_phone][1]
                                private_msg = f"{name} (Privado): {msg}"
                                message_history.append(f"{name} -> {target_phone}: {msg}")
                                target_conn.sendall(private_msg.encode('utf-8'))
                                conn.sendall(f"Você -> {target_phone}: {msg}".encode('utf-8'))
                            else:
                                conn.sendall("Usuário não encontrado.\n".encode('utf-8'))
                    except:
                        conn.sendall("Formato inválido. Use /to <numero> <mensagem>\n".encode('utf-8'))

                else:
                    conn.sendall("Comando desconhecido.\n".encode('utf-8'))

            except (ConnectionResetError, ConnectionAbortedError):
                print(f"[!] Cliente {addr} encerrou abruptamente.")
                break

    except Exception as e:
        print(f"[!] Erro com cliente {addr}: {e}")

    finally:
        with lock:
            for p, (n, c) in list(clients.items()):
                if c == conn:
                    del clients[p]
                    break
        broadcast_user_list()
        conn.close()
        print(f"[-] Cliente {addr} desconectado")

def start_server(host='0.0.0.0', port=5000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()

    print(f"Servidor rodando em {host}:{port}...")

    try:
        while True:
            try:
                conn, addr = server.accept()
                thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                thread.start()
            except Exception as e:
                print(f"[!] Erro ao aceitar cliente: {e}")
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
