import os
import socket
import threading
from tkinter import filedialog
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
