import customtkinter as ctk
import socket
import threading
import sys

# Variáveis globais
client_socket = None
receive_thread = None
is_connected = False
my_name = None
my_phone = None

ctk.set_appearance_mode("System")  # "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # "blue", "dark-blue", "green"

def update_message_display(message):
    message_display.configure(state="normal")
    message_display.insert(ctk.END, message + "\n")
    message_display.configure(state="disabled")
    message_display.yview(ctk.END)

def receive_messages(sock):
    global is_connected
    while is_connected:
        try:
            data = sock.recv(1024).decode('utf-8')
            if not data:
                update_message_display("[!] Conexão encerrada pelo servidor.")
                is_connected = False
                break

            messages = data.split("\n")
            for message in messages:
                message = message.strip()
                if not message:
                    continue

                if message.startswith("/userlist "):
                    users_str = message[len("/userlist "):]
                    users = users_str.split("|")
                    for widget in user_list.winfo_children():
                        widget.destroy()
                    for u in users:
                        ctk.CTkLabel(user_list, text=u, anchor="w").pack(fill=ctk.X, pady=2)
                else:
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
    global client_socket, is_connected
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

def disconnect_client(silent=False):
    global client_socket, is_connected
    if client_socket and is_connected:
        try:
            try:
                client_socket.sendall("/quit".encode('utf-8'))
            except:
                pass

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
            user_list.delete("all")

            for widget in user_list.winfo_children():
                widget.destroy()

            if not silent:
                update_message_display("[!] Desconectado do servidor.")
    elif not silent:
        update_message_display("[!] Não há conexão ativa para desconectar.")


def on_closing():
    disconnect_client(silent=True)
    root.destroy()
    sys.exit()

def update_user_list(name, phone):
    ctk.CTkLabel(user_list, text=f"{name} ({phone})", anchor="w").pack(fill=ctk.X, pady=2)

def connect_to_server():
    global client_socket, receive_thread, is_connected, my_name, my_phone

    host = host_entry.get()
    port_str = port_entry.get()

    try:
        port = int(port_str)
    except ValueError:
        update_message_display("[!] Porta inválida. Digite um número.")
        return

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        is_connected = True
        update_message_display(f"[+] Conectado a {host}:{port}")

        receive_thread = threading.Thread(target=receive_messages, args=(client_socket,), daemon=True)
        receive_thread.start()

        # Enviar nome e telefone para o servidor
        client_socket.sendall(my_name.encode('utf-8'))
        update_message_display(f"> {my_name}")

        client_socket.sendall(my_phone.encode('utf-8'))
        update_message_display(f"> {my_phone}")

        send_button.configure(state="normal")
        message_input.configure(state="normal")
        connect_button.configure(state="disabled")
        disconnect_button.configure(state="normal")

    except Exception as e:
        update_message_display(f"[!] Falha ao conectar: {e}")
        disconnect_client(silent=True)

def on_login_submit():
    global my_name, my_phone
    name = name_entry.get().strip()
    phone = phone_entry.get().strip()

    if not name or not phone:
        error_label.configure(text="Preencha ambos os campos!")
        return

    my_name = name
    my_phone = phone

    error_label.configure(text="")
    login_window.destroy()
    connect_button.configure(state="normal")

# --- Janela Principal ---
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

connect_button = ctk.CTkButton(conn_frame, text="Conectar", command=lambda: threading.Thread(target=connect_to_server, daemon=True).start(),
                               fg_color="green", hover_color="#286e2d", state="disabled")
connect_button.pack(side=ctk.LEFT, padx=(10, 5))

disconnect_button = ctk.CTkButton(conn_frame, text="Desconectar", command=disconnect_client,
                                  fg_color="red", hover_color="#8b0000", state="disabled")
disconnect_button.pack(side=ctk.LEFT, padx=(0, 10))

# Painel Principal (Usuários e Chat)
main_frame = ctk.CTkFrame(root, corner_radius=10)
main_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=(0, 15))

# Frame Usuários
users_frame = ctk.CTkFrame(main_frame, width=200, corner_radius=10)
users_frame.pack(side=ctk.LEFT, fill=ctk.Y, padx=(10, 5), pady=10)
users_frame.pack_propagate(False)

ctk.CTkLabel(users_frame, text="USUÁRIOS ONLINE", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
user_list = ctk.CTkScrollableFrame(users_frame, fg_color="transparent")
user_list.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)

# Frame Chat
chat_panel = ctk.CTkFrame(main_frame, corner_radius=10)
chat_panel.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=(5, 10), pady=10)

ctk.CTkLabel(chat_panel, text="MENSAGENS", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
message_display = ctk.CTkTextbox(chat_panel, wrap="word", state="disabled", corner_radius=10)
message_display.pack(padx=10, pady=(0, 10), fill=ctk.BOTH, expand=True)

input_send_frame = ctk.CTkFrame(chat_panel, fg_color="transparent")
input_send_frame.pack(fill=ctk.X, padx=10, pady=(0, 10))

message_input = ctk.CTkEntry(input_send_frame, placeholder_text="Escreva sua mensagem aqui...",
                             state="disabled", corner_radius=10)
message_input.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=(0, 10))
message_input.bind("<Return>", send_message)

send_button = ctk.CTkButton(input_send_frame, text="Enviar", command=send_message,
                            fg_color="#1F6AA5", hover_color="#185582", state="disabled")
send_button.pack(side=ctk.RIGHT)

# --- Janela de Login ---
login_window = ctk.CTkToplevel(root)
login_window.title("Login")
login_window.geometry("350x220")
login_window.grab_set()  # Foca na janela de login

ctk.CTkLabel(login_window, text="Digite seu nome:").pack(pady=(20, 5))
name_entry = ctk.CTkEntry(login_window, width=250)
name_entry.pack(pady=5)

ctk.CTkLabel(login_window, text="Digite seu telefone:").pack(pady=5)
phone_entry = ctk.CTkEntry(login_window, width=250)
phone_entry.pack(pady=5)

error_label = ctk.CTkLabel(login_window, text="", text_color="red")
error_label.pack(pady=5)

submit_btn = ctk.CTkButton(login_window, text="Enviar", command=on_login_submit)
submit_btn.pack(pady=15)
root.mainloop()
