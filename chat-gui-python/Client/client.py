import os
import pickle
import socket
import struct
import threading
from tkinter import filedialog, messagebox, ttk
import tkinter.scrolledtext
import tkinter as tk
from PIL import ImageTk, Image

HOST = socket.gethostbyname(socket.gethostname())
PORT = 6969


class firstScreen(tk.Tk):
    def __init__(self):
        super().__init__()

        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()

        self.x_co = int((screen_width / 2) - (550 / 2))
        self.y_co = int((screen_height / 2) - (400 / 2)) - 80
        self.geometry(f"550x400+{self.x_co}+{self.y_co}")
        self.title("Chat Room")

        self.user = None
        self.image_extension = None
        self.image_path = None

        self.first_frame = tk.Frame(self, bg="sky blue")
        self.first_frame.pack(fill="both", expand=True)

        app_icon = Image.open('images/icon.png')
        app_icon = ImageTk.PhotoImage(app_icon)

        self.iconphoto(False, app_icon)

        background = Image.open("images/background-chat.jpg")
        background = background.resize((550, 400), Image.ANTIALIAS)
        background = ImageTk.PhotoImage(background)

        upload_image = Image.open('images/send-img.png')
        upload_image = upload_image.resize((25, 25), Image.ANTIALIAS)
        upload_image = ImageTk.PhotoImage(upload_image)

        self.user_image = 'images/user.png'

        tk.Label(self.first_frame, image=background).place(x=0, y=0)

        head = tk.Label(self.first_frame, text="Sign Up",
                        font="Segoe UI Black", bg="grey")
        head.place(relwidth=1, y=24)

        self.profile_label = tk.Label(self.first_frame, bg="grey")
        self.profile_label.place(x=350, y=75, width=150, height=140)

        upload_button = tk.Button(self.first_frame, image=upload_image, compound="left",
                                  text="Upload Image", cursor="hand2", font="Segoe UI Black", padx=2, command=self.add_photo)
        upload_button.place(x=345, y=220)

        self.username = tk.Label(
            self.first_frame, text="Username", font="Segoe UI Black", bg="grey")
        self.username.place(x=80, y=150)

        self.username_entry = tk.Entry(
            self.first_frame,  font="Segoe UI Black", width=10, highlightcolor="blue", highlightthickness=1)
        self.username_entry.place(x=195, y=150)

        self.username_entry.focus_set()

        submit_button = tk.Button(self.first_frame, text="Connect", font="Segoe UI Black", padx=30,
                                  cursor="hand2", command=self.process_data, bg="#16cade", relief="solid", bd=2)

        submit_button.place(x=200, y=275)

        self.mainloop()

    def add_photo(self):
        self.image_path = filedialog.askopenfilename()
        image_name = os.path.basename(self.image_path)
        self.image_extension = image_name[image_name.rfind('.')+1:]

        if self.image_path:
            user_image = Image.open(self.image_path)
            user_image = user_image.resize((150, 140), Image.ANTIALIAS)
            user_image.save('resized'+image_name)
            user_image.close()

            self.image_path = 'resized'+image_name
            user_image = Image.open(self.image_path)

            user_image = ImageTk.PhotoImage(user_image)
            self.profile_label.image = user_image
            self.profile_label.config(image=user_image)

    def connect(self):
        if self.username_entry.get():
            self.profile_label.config(image="")

            if len(self.username_entry.get().strip()) > 6:
                self.user = self.username_entry.get()[:6] + "."
            else:
                self.user = self.username_entry.get()

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_socket.connect((HOST, PORT))
                status = client_socket.recv(1024).decode()
                if status == 'not_allowed':
                    client_socket.close()
                    messagebox.showinfo(
                        title="Can't connect!", message='Sorry, server is completely occupied. Try again later.')
                    return
            except ConnectionRefusedError:
                messagebox.showinfo(
                    title="Can't connect!", message="Server is offline, try again later.")
                print("Server is offline, try again later.")
                return

            client_socket.send(self.user.encode('utf-8'))

            if not self.image_path:
                self.image_path = self.user_image
            with open(self.image_path, 'rb') as image_data:
                image_bytes = image_data.read()

            image_len = len(image_bytes)
            image_len_bytes = struct.pack('i', image_len)
            client_socket.send(image_len_bytes)

            if client_socket.recv(1024).decode() == 'received':
                client_socket.send(str(self.image_extension).strip().encode())

            client_socket.send(image_bytes)

            clients_data_size_bytes = client_socket.recv(1024 * 8)
            clients_data_size_int = struct.unpack(
                'i', clients_data_size_bytes)[0]
            b = b''
            while True:
                clients_data_bytes = client_socket.recv(1024)
                b += clients_data_bytes
                if len(b) == clients_data_size_int:
                    break

            clients_connected = pickle.loads(b)

            client_socket.send('image_received'.encode())

            user_id = struct.unpack('i', client_socket.recv(1024))[0]
            print(f"{self.user} is user no. {user_id}")
            ChatScreen(self, self.first_frame, client_socket,
                       clients_connected, user_id)


class ChatScreen(tk.Canvas):
    def __init__(self, parent, first_frame, client_socket, clients_connected, user_id):
        super().__init__(parent, bg="#2b2b2b")

        self.window = 'ChatScreen'

        self.first_frame = first_frame
        self.first_frame.pack_forget()

        self.parent = parent
        self.parent.bind('<Return>', lambda e: self.sent_message_format(e))

        self.all_user_image = {}

        self.user_id = user_id

        self.clients_connected = clients_connected

        
        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.client_socket = client_socket
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()

        x_co = int((screen_width / 2) - (680 / 2))
        y_co = int((screen_height / 2) - (750 / 2)) - 80
        self.parent.geometry(f"680x750+{x_co}+{y_co}")

        user_image = Image.open(self.parent.image_path)
        user_image = user_image.resize((40, 40), Image.ANTIALIAS)
        self.user_image = ImageTk.PhotoImage(user_image)


        global chat_room_icon
        chat_room_icon = Image.open('images/icon.png')
        chat_room_icon = chat_room_icon.resize((60, 60), Image.ANTIALIAS)
        chat_room_icon = ImageTk.PhotoImage(chat_room_icon)

        self.y = 140
        self.clients_online_labels = {}


        self.create_text(545, 120, text="Online",
                         font="Segoe UI Black", fill="#40C961")

        tk.Label(self, text="   ", font="Segoe UI Black",
                 bg="#b5b3b3").place(x=4, y=29)

        tk.Label(self, text="chat room", font="Segoe UI Black", padx=20, fg="green",
                 bg="#b5b3b3", anchor="w", justify="left").place(x=88, y=29, relwidth=1)

        self.create_image(60, 40, image=chat_room_icon)

        container = tk.Frame(self)

        container.place(x=40, y=120, width=450, height=550)
        self.canvas = tk.Canvas(container, bg="#595656")
        self.scrollable_frame = tk.Frame(self.canvas, bg="#595656")

        scrollable_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")

        def configure_scroll_region(e):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        def resize_frame(e):
            self.canvas.itemconfig(scrollable_window, width=e.width)

        self.scrollable_frame.bind("<Configure>", configure_scroll_region)

        scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.yview_moveto(1.0)

        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", resize_frame)
        self.canvas.pack(fill="both", expand=True)

        send_button = tk.Button(self, text="Send", fg="#83eaf7", font="Segoe UI Black", bg="#7d7d7d", padx=10,
                                relief="solid", bd=2, command=self.sent_message_format)
        send_button.place(x=400, y=680)

        self.entry = tk.Text(self, font="Segoe UI Black", width=38, height=2,
                             highlightcolor="blue", highlightthickness=1)
        self.entry.place(x=40, y=681)

        self.entry.focus_set()


class Client:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

        self.nickname_window = NicknameWindow()
        self.nickname = self.nickname_window.nickname

        self.gui_done = False
        self.running = True

        gui_thread = threading.Thread(target=self.gui_loop)
        receive_thread = threading.Thread(target=self.receive)

        gui_thread.start()
        receive_thread.start()

    def gui_loop(self):
        self.win = tkinter.Tk()
        self.win.title("chat room")
        self.win.configure(bg="#161616")

        self.chat_label = tkinter.Label(
            self.win, text=f"{self.nickname}", bg="#E2856E", width=15)
        self.chat_label.config(font=("Segoe UI Black", 12))
        self.chat_label.grid(row=0, column=0, padx=20, pady=5, sticky='n')

        self.text_area = tkinter.scrolledtext.ScrolledText(
            self.win, bg="#CCDAD1")
        self.text_area.grid(row=1, column=0, padx=20, pady=5, sticky='n')
        self.text_area.config(state='disabled')

        self.input_area = tkinter.Text(self.win, height=2, bg="#CCDAD1")
        self.input_area.grid(row=3, column=0, padx=20, pady=5, sticky='w')
        self.input_area.bind('<FocusIn>', self.clear_default_text)
        self.input_area.bind('<FocusOut>', self.restore_default_text)
        self.input_area.insert('1.0', 'Enter message')

        self.send_button = tkinter.Button(
            self.win, text="\u2708", command=self.write)
        self.send_button.config(font=("Arial", 11))
        self.send_button.grid(row=3, column=0, padx=5, sticky='e')

        self.gui_done = True

        self.win.protocol("WM_DELETE_WINDOW", self.stop)

        self.win.mainloop()

    def clear_default_text(self, event):
        if self.input_area.get('1.0', 'end-1c') == 'Enter message':
            self.input_area.delete('1.0', 'end-1c')

    def restore_default_text(self, event):
        if not self.input_area.get('1.0', 'end-1c'):
            self.input_area.insert('1.0', 'Enter message')

    def write(self):
        message = f"{self.nickname}: {self.input_area.get('1.0', 'end')}"
        self.sock.send(message.encode('utf-8'))
        self.input_area.delete('1.0', 'end')

    def stop(self):
        self.running = False
        self.win.destroy()
        self.sock.close()
        exit(0)

    def receive(self):
        while self.running:
            try:
                message = self.sock.recv(1024).decode('utf-8')
                if message == 'NICK':
                    self.sock.send(self.nickname.encode('utf-8'))
                else:
                    if self.gui_done:
                        self.text_area.config(state='normal')
                        self.text_area.insert('end', f"{message}\n")
                        self.text_area.yview('end')
                        self.text_area.config(state='disabled')
            except ConnectionAbortedError:
                break
            except:
                print("Error")
                self.sock.close()
                break


client = Client(HOST, PORT)
