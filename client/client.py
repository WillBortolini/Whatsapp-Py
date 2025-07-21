import socket
import threading

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode('utf-8')
            if not message:
                print("[!] Conexão encerrada pelo servidor.")
                break
            print("\n" + message)
        except Exception as e:
            print(f"[!] Erro ao receber dados: {e}")
            break

def send_messages(sock):
    while True:
        try:
            msg = input()
            sock.sendall(msg.encode('utf-8'))
        except Exception as e:
            print(f"[!] Erro ao enviar dados: {e}")
            break

def main():
    host = input("Digite o IP do servidor (ex: 127.0.0.1): ")
    port = int(input("Digite a porta (ex: 5000): "))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except Exception as e:
        print(f"[!] Falha ao conectar: {e}")
        return

    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    try:
        for _ in range(2):
            server_msg = sock.recv(1024).decode('utf-8')
            print(server_msg, end="")
            user_input = input()
            sock.sendall(user_input.encode('utf-8'))
    except Exception as e:
        print(f"[!] Erro durante registro: {e}")
        sock.close()
        return

    send_messages(sock)

    sock.close()

if __name__ == "__main__":
    main()
