import customtkinter as ctk
from tkinter import scrolledtext, simpledialog, messagebox
import socket
import threading
import sys

# Variáveis globais
client_socket = None
receive_thread = None
is_connected = False
my_name = ""
my_phone = ""

ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "dark-blue", "green"

def update_message_display(message):
    """Atualiza a área de exibição de mensagens de forma segura."""
    message_display.configure(state="normal")
    message_display.insert(ctk.END, message + "\n")
    message_display.configure(state="disabled")
    message_display.yview(ctk.END)

def receive_messages(sock):
    """Recebe continuamente mensagens do servidor e as exibe na GUI."""
    global is_connected
    while is_connected:
        try:
            message = sock.recv(1024).decode('utf-8')
            if not message:
                update_message_display("[!] Conexão encerrada pelo servidor.")
                is_connected = False
                break
            update_message_display(message)
        except OSError:
            if is_connected:
                update_message_display("[!] Erro na conexão: Socket fechado ou erro de rede.")
            break
        except Exception as e:
            update_message_display(f"[!] Erro ao receber dados: {e}")
            is_connected = False
            break
    disconnect_client(silent=True)

def send_message(event=None):
    """Envia a mensagem digitada no campo de entrada para o servidor."""
    global client_socket
    if client_socket and is_connected:
        msg = message_input.get()
        if msg.strip():
            try:
                client_socket.sendall(msg.encode('utf-8'))
                message_input.delete(0, ctk.END)
            except Exception as e:
                update_message_display(f"[!] Erro ao enviar dados: {e}")
                disconnect_client()
    else:
        update_message_display("[!] Não conectado ao servidor.")

def connect_to_server():
    """Estabelece a conexão com o servidor e lida com o registro."""
    global client_socket, receive_thread, is_connected, my_name, my_phone

    if is_connected:
        messagebox.showinfo("Conectado", "Você já está conectado ao servidor.")
        return

    host = host_entry.get()
    port_str = port_entry.get()

    if not host or not port_str:
        update_message_display("[!] Por favor, digite o IP e a Porta do servidor.")
        return

    try:
        port = int(port_str)
    except ValueError:
        update_message_display("[!] Porta inválida. Digite um número.")
        return

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        is_connected = True
        update_message_display(f"[+] Conectado a {host}:{port}")

        receive_thread = threading.Thread(target=receive_messages, args=(client_socket,), daemon=True)
        receive_thread.start()

        server_msg_name = client_socket.recv(1024).decode('utf-8')
        update_message_display(server_msg_name.strip())
        my_name = simpledialog.askstring("Registro", server_msg_name.strip())
        if my_name is None:
            update_message_display("[!] Registro de nome cancelado. Conexão fechada.")
            disconnect_client()
            return
        client_socket.sendall(my_name.encode('utf-8'))
        update_message_display(f"> {my_name}")

        server_msg_phone = client_socket.recv(1024).decode('utf-8')
        update_message_display(server_msg_phone.strip())
        my_phone = simpledialog.askstring("Registro", server_msg_phone.strip())
        if my_phone is None:
            update_message_display("[!] Registro de número cancelado. Conexão fechada.")
            disconnect_client()
            return
        client_socket.sendall(my_phone.encode('utf-8'))
        update_message_display(f"> {my_phone}")

        update_user_list(my_name, my_phone) # Adiciona o próprio usuário à lista
        
        send_button.configure(state="normal")
        message_input.configure(state="normal")
        connect_button.configure(state="disabled")
        disconnect_button.configure(state="normal")

    except ConnectionRefusedError:
        update_message_display("[!] Falha na conexão: Servidor não encontrado ou recusou a conexão.")
        disconnect_client(silent=True)
    except Exception as e:
        update_message_display(f"[!] Falha ao conectar ou durante o registro: {e}")
        disconnect_client(silent=True)

def disconnect_client(silent=False):
    """Desconecta o cliente do servidor."""
    global client_socket, is_connected
    if client_socket and is_connected:
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
        except Exception as e:
            if not silent:
                update_message_display(f"[!] Erro ao fechar o socket: {e}")
        finally:
            client_socket = None
            is_connected = False
            send_button.configure(state="disabled")
            message_input.configure(state="disabled")
            connect_button.configure(state="normal")
            disconnect_button.configure(state="disabled")
            user_list.delete("all") # Limpa a lista de usuários ao desconectar
            if not silent:
                update_message_display("[!] Desconectado do servidor.")
    elif not silent:
        update_message_display("[!] Não há conexão ativa para desconectar.")

def on_closing():
    """Lida com o desligamento adequado quando a janela da GUI é fechada."""
    disconnect_client(silent=True)
    root.destroy()
    sys.exit()

def update_user_list(name, phone):
    """Atualiza a lista de usuários (simulada)."""
    # Em um sistema real, o servidor enviaria eventos de "usuário online" e "usuário offline".
    # Esta é uma simulação simples para fins de design da GUI.
    user_list.insert(ctk.END, f"{name} ({phone})")


# --- Configuração da GUI ---
root = ctk.CTk()
root.title("Chat Avançado")
root.geometry("900x650")
root.minsize(700, 500)
root.protocol("WM_DELETE_WINDOW", on_closing)

# Frame de Conexão no topo
conn_frame = ctk.CTkFrame(root, corner_radius=10)
conn_frame.pack(fill=ctk.X, padx=15, pady=(15, 10))

ctk.CTkLabel(conn_frame, text="IP do Servidor:").pack(side=ctk.LEFT, padx=(10, 5))
host_entry = ctk.CTkEntry(conn_frame, width=150)
host_entry.pack(side=ctk.LEFT, padx=5)
host_entry.insert(0, "127.0.0.1")

ctk.CTkLabel(conn_frame, text="Porta:").pack(side=ctk.LEFT, padx=5)
port_entry = ctk.CTkEntry(conn_frame, width=80)
port_entry.pack(side=ctk.LEFT, padx=5)
port_entry.insert(0, "5000")

connect_button = ctk.CTkButton(conn_frame, text="Conectar", command=connect_to_server,
                               fg_color="green", hover_color="#286e2d")
connect_button.pack(side=ctk.LEFT, padx=(10, 5))

disconnect_button = ctk.CTkButton(conn_frame, text="Desconectar", command=disconnect_client,
                                  fg_color="red", hover_color="#8b0000", state="disabled")
disconnect_button.pack(side=ctk.LEFT, padx=(0, 10))


# Painel Principal (Divisão Horizontal para Usuários e Chat)
main_frame = ctk.CTkFrame(root, corner_radius=10)
main_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=(0, 15))

# Frame Esquerdo (Usuários)
users_frame = ctk.CTkFrame(main_frame, width=200, corner_radius=10)
users_frame.pack(side=ctk.LEFT, fill=ctk.Y, padx=(10, 5), pady=10)
users_frame.pack_propagate(False) # Impede que o frame se redimensione para o conteúdo

ctk.CTkLabel(users_frame, text="USUÁRIOS ONLINE", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
user_list = ctk.CTkScrollableFrame(users_frame, fg_color="transparent")
user_list.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)

# A lista de usuários dentro do scrollable frame será preenchida dinamicamente
# com CTkLabels ou outro widget se quisermos mais interatividade.
# Por enquanto, é apenas um frame para conter a lista.
# A função update_user_list adicionará nomes aqui.
# Exemplo (remova em produção se não for alimentado pelo servidor):
# ctk.CTkLabel(user_list, text="Fulano (123)", anchor="w").pack(fill=ctk.X, pady=2)
# ctk.CTkLabel(user_list, text="Ciclano (456)", anchor="w").pack(fill=ctk.X, pady=2)


# Frame Direito (Mensagens e Entrada)
chat_panel = ctk.CTkFrame(main_frame, corner_radius=10)
chat_panel.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=(5, 10), pady=10)

ctk.CTkLabel(chat_panel, text="MENSAGENS", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
message_display = ctk.CTkTextbox(chat_panel, wrap="word", state="disabled", corner_radius=10)
message_display.pack(padx=10, pady=(0, 10), fill=ctk.BOTH, expand=True)

# Campo de Entrada de Mensagens e Botão de Envio
input_send_frame = ctk.CTkFrame(chat_panel, fg_color="transparent")
input_send_frame.pack(fill=ctk.X, padx=10, pady=(0, 10))

message_input = ctk.CTkEntry(input_send_frame, placeholder_text="Escreva sua mensagem aqui...",
                             state="disabled", corner_radius=10)
message_input.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=(0, 10))
message_input.bind("<Return>", send_message)

send_button = ctk.CTkButton(input_send_frame, text="Enviar", command=send_message,
                            fg_color="#1F6AA5", hover_color="#185582", state="disabled")
send_button.pack(side=ctk.RIGHT)

root.mainloop()