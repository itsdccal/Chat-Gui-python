import socket
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import pickle
from datetime import datetime
import os
import threading
import struct

# Mengambil alamat IP lokal
HOST = socket.gethostbyname(socket.gethostname())
# Port yang akan digunakan untuk koneksi
PORT = 6969


class FirstScreen(tk.Tk):
    def __init__(self):
        super().__init__()

        # Konfigurasi tampilan jendela
        self.geometry("640x480")
        self.title("Chat Room")
        self.resizable(False, False)

        self.user = None
        self.image_extension = None
        self.image_path = None

        # Membuat frame pertama
        self.first_frame = tk.Frame(self)
        self.first_frame.pack(fill="both", expand=True)

        # Mengatur ikon aplikasi
        app_icon = Image.open('images/icon.png')
        app_icon = ImageTk.PhotoImage(app_icon)
        self.iconphoto(False, app_icon)

        # Menyiapkan gambar latar belakang
        background = Image.open("images/background-login.png")
        background = ImageTk.PhotoImage(background)

        # Menyiapkan gambar untuk tombol unggah gambar
        upload_image = Image.open('images/send-img.png')
        upload_image = upload_image.resize((25, 25), Image.ANTIALIAS)
        upload_image = ImageTk.PhotoImage(upload_image)

        # Mengatur gambar pengguna default
        self.user_image = 'images/user.png'

        # Menampilkan latar belakang
        tk.Label(self.first_frame, image=background).place(x=0, y=0)

        # Menampilkan label "LOGIN"
        head = tk.Label(self.first_frame, text="LOGIN",
                        font="lucida 12 bold", bg="#128C7E")
        head.place(relwidth=1, y=24)

        # Menampilkan label untuk gambar profil
        self.profile_label = tk.Label(self.first_frame, bg="#128C7E")
        self.profile_label.place(x=448, y=182.7, width=150, height=140)

        # Menampilkan tombol unggah gambar
        upload_button = tk.Button(self.first_frame, image=upload_image, compound="left", text="Upload Image",
                                  cursor="hand2", font="lucida 12 bold", padx=2, command=self.add_photo)
        upload_button.place(x=448, y=344.1, width=150)

        # Menampilkan label "Username"
        self.username = tk.Label(
            self.first_frame, text="Username", font="lucida 12 bold", bg="#128C7E")
        self.username.place(x=110.2, y=344.1)

        # Menampilkan input untuk username
        self.username_entry = tk.Entry(self.first_frame,  font="lucida 12 bold", width=10,
                                       highlightcolor="blue", highlightthickness=1)
        self.username_entry.place(x=212.7, y=344.1, width=214.6)
        self.username_entry.focus_set()

        # Tombol "Connect"
        submit_button = tk.Button(self.first_frame, text="Connect", font="lucida 12 bold", padx=30, cursor="hand2",
                                  command=self.process_data, bg="#34B7F1", relief="solid", bd=2)
        submit_button.place(x=248, y=388.4)

        # Memulai perulangan utama
        self.first_frame.mainloop()()

    def add_photo(self):
        # Memilih path file gambar menggunakan dialog file
        self.image_path = filedialog.askopenfilename()

        # Mendapatkan nama file gambar dan ekstensi file
        image_name = os.path.basename(self.image_path)
        self.image_extension = image_name[image_name.rfind('.')+1:]

        if self.image_path:
            # Membuka gambar pengguna yang dipilih
            user_image = Image.open(self.image_path)

            # Mengubah ukuran gambar menjadi 150x140 piksel
            user_image = user_image.resize((150, 140), Image.ANTIALIAS)

            # Menyimpan gambar pengguna yang diubah ukurannya
            user_image.save('resized'+image_name)
            user_image.close()

            # Mengatur path gambar yang diubah ukurannya
            self.image_path = 'resized'+image_name

            # Membuka kembali gambar pengguna yang telah diubah ukurannya
            user_image = Image.open(self.image_path)

            # Mengkonversi gambar menjadi format yang dapat ditampilkan oleh Tkinter
            user_image = ImageTk.PhotoImage(user_image)

            # Menampilkan gambar pengguna pada label profil
            self.profile_label.image = user_image
            self.profile_label.config(image=user_image)

    def process_data(self):
        # Memeriksa apakah ada input nama pengguna
        if self.username_entry.get():
            self.profile_label.config(image="")

            # Mengatur nama pengguna yang akan digunakan
            if len(self.username_entry.get().strip()) > 6:
                self.user = self.username_entry.get()[:6] + "."
            else:
                self.user = self.username_entry.get()

            # Membuat socket klien dan mencoba untuk terhubung ke server
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_socket.connect((HOST, PORT))
                status = client_socket.recv(1024).decode()
                if status == 'not_allowed':
                    client_socket.close()
                    # Menampilkan pesan kesalahan jika server penuh
                    messagebox.showinfo(
                        title="Can't connect!", message='Sorry, server is completely occupied. Try again later.')
                    return
            except ConnectionRefusedError:
                client_socket.close()
                # Menampilkan pesan kesalahan jika server offline
                messagebox.showinfo(
                    title="Can't connect!", message="Server is offline, try again later.")
                print("Server is offline, try again later.")
                return

            # Mengirimkan nama pengguna ke server
            client_socket.send(self.user.encode('utf-8'))

            # Menentukan path gambar pengguna yang akan dikirimkan
            if not self.image_path:
                self.image_path = self.user_image

            # Membuka file gambar dan membaca byte-datanya
            with open(self.image_path, 'rb') as image_data:
                image_bytes = image_data.read()

            # Mengirimkan ukuran gambar ke server
            image_len = len(image_bytes)
            image_len_bytes = struct.pack('i', image_len)
            client_socket.send(image_len_bytes)

            # Menerima konfirmasi penerimaan ukuran gambar dari server
            if client_socket.recv(1024).decode() == 'received':
                # Mengirimkan ekstensi gambar ke server
                client_socket.send(str(self.image_extension).strip().encode())

            # Mengirimkan byte-data gambar ke server
            client_socket.send(image_bytes)

            # Menerima data terkait klien yang terhubung dari server
            clients_data_size_bytes = client_socket.recv(1024 * 8)
            clients_data_size_int = struct.unpack(
                'i', clients_data_size_bytes)[0]
            b = b''
            while True:
                clients_data_bytes = client_socket.recv(1024)
                b += clients_data_bytes
                if len(b) == clients_data_size_int:
                    break

            # Melakukan unpickling untuk mendapatkan data terkait klien yang terhubung
            clients_connected = pickle.loads(b)

            # Mengirimkan konfirmasi penerimaan gambar dari server
            client_socket.send('image_received'.encode())

            # Menerima ID pengguna dari server
            user_id = struct.unpack('i', client_socket.recv(1024))[0]
            print(f"{self.user} is user no. {user_id}")

            # Membuka jendela ChatScreen untuk komunikasi
            ChatScreen(self, self.first_frame, client_socket,
                       clients_connected, user_id)


class ChatScreen(tk.Canvas):
    def __init__(self, parent, first_frame, client_socket, clients_connected, user_id):
        super().__init__(parent, bg="#075E54")

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

        self.parent.geometry("680x750")

        # Membuat gambar thumbnail pengguna dan menyimpannya sebagai atribut
        user_image = Image.open(self.parent.image_path)
        user_image = user_image.resize((40, 40), Image.ANTIALIAS)
        self.user_image = ImageTk.PhotoImage(user_image)

        # Membuat gambar thumbnail untuk grup chat dan menyimpannya sebagai atribut
        global group_chat
        group_chat = Image.open('images/icon.png')
        group_chat = group_chat.resize((60, 60), Image.ANTIALIAS)
        group_chat = ImageTk.PhotoImage(group_chat)

        self.y = 140
        self.clients_online_labels = {}

        # Membuat label "Online" di jendela chat
        self.create_text(545, 120, text="Online",
                         font="lucida 12 bold", fill="#25D366")

        # Membuat garis pemisah
        tk.Label(self, text="   ", font="lucida 15 bold",
                 bg="#b5b3b3").place(x=4, y=29)

        # Membuat label nama pengguna di jendela chat
        tk.Label(self, text="agakareba", font="lucida 15 bold", padx=20, fg="black",
                 bg="#b5b3b3", anchor="w", justify="left").place(x=88, y=29, relwidth=1)

        # Menampilkan gambar thumbnail grup chat
        self.create_image(60, 40, image=group_chat)

        # Membuat wadah untuk pesan-pesan di jendela chat dengan fungsi scroll
        container = tk.Frame(self)
        container.place(x=40, y=120, width=450, height=550)
        self.canvas = tk.Canvas(container, bg="#7d7d7d")
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")

        scrollable_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")

        # Mengatur ulang batas scroll saat ukuran wadah berubah
        def configure_scroll_region(e):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        # Mengubah ukuran wadah saat ukuran jendela berubah
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

        # Membuat tombol "Send" untuk mengirim pesan
        send_button = tk.Button(self, text="Send", fg="#34B7F1", font="lucida 11 bold", bg="#7d7d7d", padx=10,
                                relief="solid", bd=2, command=self.sent_message_format)
        send_button.place(x=400, y=680)

        # Membuat input teks untuk menulis pesan
        self.entry = tk.Text(self, font="lucida 10 bold", width=38, height=2,
                             highlightcolor="#34B7F1", highlightthickness=1)
        self.entry.place(x=40, y=681)

        self.entry.focus_set()

        # ---------------------------emoji code logic-----------------------------------

        emoji_data = [('emojis/u0001f44a.png', '\U0001F44A'), ('emojis/u0001f44c.png', '\U0001F44C'), ('emojis/u0001f44d.png', '\U0001F44D'),
                      ('emojis/u0001f495.png', '\U0001F495'), ('emojis/u0001f496.png',
                                                               '\U0001F496'), ('emojis/u0001f4a6.png', '\U0001F4A6'),
                      ('emojis/u0001f4a9.png', '\U0001F4A9'), ('emojis/u0001f4af.png',
                                                               '\U0001F4AF'), ('emojis/u0001f595.png', '\U0001F595'),
                      ('emojis/u0001f600.png', '\U0001F600'), ('emojis/u0001f602.png',
                                                               '\U0001F602'), ('emojis/u0001f603.png', '\U0001F603'),
                      ('emojis/u0001f605.png', '\U0001F605'), ('emojis/u0001f606.png',
                                                               '\U0001F606'), ('emojis/u0001f608.png', '\U0001F608'),
                      ('emojis/u0001f60d.png', '\U0001F60D'), ('emojis/u0001f60e.png',
                                                               '\U0001F60E'), ('emojis/u0001f60f.png', '\U0001F60F'),
                      ('emojis/u0001f610.png', '\U0001F610'), ('emojis/u0001f618.png',
                                                               '\U0001F618'), ('emojis/u0001f61b.png', '\U0001F61B'),
                      ('emojis/u0001f61d.png', '\U0001F61D'), ('emojis/u0001f621.png',
                                                               '\U0001F621'), ('emojis/u0001f624.png', '\U0001F621'),
                      ('emojis/u0001f631.png', '\U0001F631'), ('emojis/u0001f632.png',
                                                               '\U0001F632'), ('emojis/u0001f634.png', '\U0001F634'),
                      ('emojis/u0001f637.png', '\U0001F637'), ('emojis/u0001f642.png',
                                                               '\U0001F642'), ('emojis/u0001f64f.png', '\U0001F64F'),
                      ('emojis/u0001f920.png', '\U0001F920'), ('emojis/u0001f923.png', '\U0001F923'), ('emojis/u0001f928.png', '\U0001F928')]

        emoji_x_pos = 490
        emoji_y_pos = 520

        for Emoji in emoji_data:
            global emojis
            emojis = Image.open(Emoji[0])
            emojis = emojis.resize((20, 20), Image.ANTIALIAS)
            emojis = ImageTk.PhotoImage(emojis)

            emoji_unicode = Emoji[1]

            # Membuat label emoji yang dapat diklik
            emoji_label = tk.Label(
                self, image=emojis, text=emoji_unicode, bg="#194548", cursor="hand2")
            emoji_label.image = emojis
            emoji_label.place(x=emoji_x_pos, y=emoji_y_pos)
            emoji_label.bind('<Button-1>', lambda x: self.insert_emoji(x))

            emoji_x_pos += 25
            cur_index = emoji_data.index(Emoji)
            if (cur_index + 1) % 6 == 0:
                emoji_y_pos += 25
                emoji_x_pos = 490

        # -------------------------------------------------------

        m_frame = tk.Frame(self.scrollable_frame, bg="#d9d5d4")

        t_label = tk.Label(m_frame, bg="#d9d5d4", text=datetime.now().strftime(
            '%H:%M'), font="lucida 9 bold")
        t_label.pack()

        m_label = tk.Label(m_frame, wraplength=250,
                           text=f"hello {self.parent.user}", font="lucida 10 bold", bg="#128C7E")
        m_label.pack(fill="x")

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.pack(fill="both", expand=True)

        self.clients_online([])

        t = threading.Thread(target=self.receive_data)
        t.setDaemon(True)
        t.start()

    def receive_data(self):
        while True:
            try:
                # Menerima tipe data dari socket
                data_type = self.client_socket.recv(1024).decode()

                if data_type == 'notification':
                    # Jika tipe data adalah notifikasi
                    data_size = self.client_socket.recv(2048)
                    data_size_int = struct.unpack('i', data_size)[0]

                    b = b''
                    while True:
                        # Menerima data notifikasi dalam bentuk byte
                        data_bytes = self.client_socket.recv(1024)
                        b += data_bytes
                        if len(b) == data_size_int:
                            break
                    # Mengubah data notifikasi dari byte menjadi objek
                    data = pickle.loads(b)
                    self.notification_format(data)

                else:
                    # Jika tipe data bukan notifikasi
                    # Menerima data pesan dalam bentuk byte
                    data_bytes = self.client_socket.recv(1024)
                    # Mengubah data pesan dari byte menjadi objek
                    data = pickle.loads(data_bytes)
                    self.received_message_format(data)

            except ConnectionAbortedError:
                # Menangani kesalahan ketika koneksi terputus
                print("you disconnected ...")
                self.client_socket.close()
                break
            except ConnectionResetError:
                # Menampilkan pesan kesalahan saat koneksi ulang terjadi
                messagebox.showinfo(
                    title='No Connection!', message="Server offline..try connecting again later")
                self.client_socket.close()
                self.first_screen()
                break

    def on_closing(self):
        if self.window == 'ChatScreen':
            # Jika jendela saat ini adalah ChatScreen
            res = messagebox.askyesno(
                title='Warning!', message="Do you really want to disconnect?")
            if res:
                import os
                os.remove(self.all_user_image[self.user_id])
                self.client_socket.close()
                self.first_screen()
        else:
            self.parent.destroy()

    def received_message_format(self, data):
        # Mendapatkan pesan dan pengirim dari data yang diterima
        message = data['message']
        from_ = data['from']

        # Mendapatkan gambar pengirim dan ekstensi gambar
        sender_image = self.clients_connected[from_][1]
        sender_image_extension = self.clients_connected[from_][2]

        # Menyimpan gambar pengirim dalam file
        with open(f"{from_}.{sender_image_extension}", 'wb') as f:
            f.write(sender_image)

        # Membuka dan mengubah ukuran gambar pengirim
        im = Image.open(f"{from_}.{sender_image_extension}")
        im = im.resize((40, 40), Image.ANTIALIAS)
        im = ImageTk.PhotoImage(im)

        # Membuat frame untuk menampilkan pesan
        m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

        m_frame.columnconfigure(1, weight=1)

        # Label untuk menampilkan waktu pengiriman
        t_label = tk.Label(m_frame, bg="#595656", fg="white", text=datetime.now().strftime('%H:%M'), font="lucida 7 bold",
                           justify="left", anchor="w")
        t_label.grid(row=0, column=1, padx=2, sticky="w")

        # Label untuk menampilkan pesan
        m_label = tk.Label(m_frame, wraplength=250, fg="black", bg="#c5c7c9", text=message, font="lucida 9 bold", justify="left",
                           anchor="w")
        m_label.grid(row=1, column=1, padx=2, pady=2, sticky="w")

        # Label untuk menampilkan gambar pengirim
        i_label = tk.Label(m_frame, bg="#595656", image=im)
        i_label.image = im
        i_label.grid(row=0, column=0, rowspan=2)

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def sent_message_format(self, event=None):
        # Mendapatkan pesan yang dikirim
        message = self.entry.get('1.0', 'end-1c')

        if message:
            if event:
                message = message.strip()
            self.entry.delete("1.0", "end-1c")

            # Mendapatkan id pengirim
            from_ = self.user_id

            # Membuat data pesan yang akan dikirim
            data = {'from': from_, 'message': message}
            data_bytes = pickle.dumps(data)

            # Mengirim data pesan melalui socket
            self.client_socket.send(data_bytes)

            # Membuat frame untuk menampilkan pesan yang dikirim
            m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

            m_frame.columnconfigure(0, weight=1)

            # Label untuk menampilkan waktu pengiriman
            t_label = tk.Label(m_frame, bg="#595656", fg="white", text=datetime.now().strftime('%H:%M'),
                               font="lucida 7 bold", justify="right", anchor="e")
            t_label.grid(row=0, column=0, padx=2, sticky="e")

            # Label untuk menampilkan pesan
            m_label = tk.Label(m_frame, wraplength=250, text=message, fg="black", bg="#40C961",
                               font="lucida 9 bold", justify="left",
                               anchor="e")
            m_label.grid(row=1, column=0, padx=2, pady=2, sticky="e")

            # Label untuk menampilkan gambar pengirim
            i_label = tk.Label(m_frame, bg="#595656", image=self.user_image)
            i_label.image = self.user_image
            i_label.grid(row=0, column=1, rowspan=2, sticky="e")

            m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

            self.canvas.update_idletasks()
            self.canvas.yview_moveto(1.0)

    def notification_format(self, data):
        # Jika notifikasi tipe 'joined'
        if data['n_type'] == 'joined':
            # Mendapatkan informasi dari data
            name = data['name']
            image = data['image_bytes']
            extension = data['extension']
            message = data['message']
            client_id = data['id']
            # Menyimpan informasi pengguna yang terhubung dalam kamus
            self.clients_connected[client_id] = (name, image, extension)
            # Menambahkan pengguna ke daftar pengguna online
            self.clients_online([client_id, name, image, extension])
        # Jika notifikasi tipe 'left'
        elif data['n_type'] == 'left':
            # Mendapatkan informasi dari data
            client_id = data['id']
            message = data['message']
            # Menghapus label pengguna yang keluar
            self.remove_labels(client_id)
            # Menghapus informasi pengguna yang terhubung dari kamus
            del self.clients_connected[client_id]

        # Membuat frame notifikasi
        m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

        t_label = tk.Label(m_frame, fg="white", bg="#595656", text=datetime.now().strftime('%H:%M'),
                           font="lucida 9 bold")
        t_label.pack()

        m_label = tk.Label(m_frame, wraplength=250, text=message,
                           font="lucida 10 bold", justify="left", bg="sky blue")
        m_label.pack()

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.yview_moveto(1.0)

    def clients_online(self, new_added):
        # Jika tidak ada pengguna yang baru ditambahkan
        if not new_added:
            pass
            # Iterasi melalui pengguna yang terhubung
            for user_id in self.clients_connected:
                # Mendapatkan informasi pengguna
                name = self.clients_connected[user_id][0]
                image_bytes = self.clients_connected[user_id][1]
                extension = self.clients_connected[user_id][2]

                # Menyimpan gambar pengguna dalam file
                with open(f"{user_id}.{extension}", 'wb') as f:
                    f.write(image_bytes)

                self.all_user_image[user_id] = f"{user_id}.{extension}"

                # Memuat gambar pengguna dan mengubah ukurannya
                user = Image.open(f"{user_id}.{extension}")
                user = user.resize((45, 45), Image.ANTIALIAS)
                user = ImageTk.PhotoImage(user)

                # Membuat label pengguna online
                b = tk.Label(self, image=user, text=name, compound="left",
                             fg="white", bg="#2b2b2b", font="lucida 10 bold", padx=15)
                b.image = user
                self.clients_online_labels[user_id] = (b, self.y)

                b.place(x=500, y=self.y)
                self.y += 60

        else:
            # Mendapatkan informasi pengguna baru yang ditambahkan
            user_id = new_added[0]
            name = new_added[1]
            image_bytes = new_added[2]
            extension = new_added[3]

            # Menyimpan gambar pengguna dalam file
            with open(f"{user_id}.{extension}", 'wb') as f:
                f.write(image_bytes)

            self.all_user_image[user_id] = f"{user_id}.{extension}"

            # Memuat gambar pengguna dan mengubah ukurannya
            user = Image.open(f"{user_id}.{extension}")
            user = user.resize((45, 45), Image.ANTIALIAS)
            user = ImageTk.PhotoImage(user)

            # Membuat label pengguna online
            b = tk.Label(self, image=user, text=name, compound="left", fg="white", bg="#2b2b2b",
                         font="lucida 10 bold", padx=15)
            b.image = user
            self.clients_online_labels[user_id] = (b, self.y)

            b.place(x=500, y=self.y)
            self.y += 60

    def remove_labels(self, client_id):
        # Iterasi melalui label-label online yang ada
        for user_id in self.clients_online_labels.copy():
            # Mendapatkan objek label dan koordinat y dari label
            b = self.clients_online_labels[user_id][0]
            y_co = self.clients_online_labels[user_id][1]

            # Jika user_id sama dengan client_id yang ingin dihapus
            if user_id == client_id:
                print("yes")
                # Menghapus label dari tampilan
                b.destroy()
                # Menghapus entri label dari kamus
                del self.clients_online_labels[client_id]
                import os
                # ...

            # Jika user_id lebih besar dari client_id
            elif user_id > client_id:
                # Menggeser koordinat y ke atas
                y_co -= 60
                # Menempatkan ulang label dengan koordinat yang baru
                b.place(x=510, y=y_co)
                # Memperbarui kamus dengan koordinat yang baru
                self.clients_online_labels[user_id] = (b, y_co)
                self.y -= 60

    def insert_emoji(self, x):
        # Menyisipkan emoji ke dalam entri teks
        self.entry.insert("end-1c", x.widget['text'])

    def first_screen(self):
        # Menghancurkan tampilan saat ini dan beralih ke tampilan pertama
        self.destroy()
        self.parent.geometry("640x480")
        self.parent.first_frame.pack(fill="both", expand=True)
        self.window = None


# Membuat objek FirstScreen
FirstScreen()
