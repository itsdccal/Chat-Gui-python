import socket
import threading
import tkinter
import tkinter.scrolledtext
from tkinter import simpledialog
# from ttkthemes import ThemedTk

HOST = socket.gethostbyname(socket.gethostname())
PORT = 6969


class Client:
    
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

        msg = tkinter.Tk()
        msg.withdraw()

        self.nickname = simpledialog.askstring("Nickname", "Please choose a nickname", parent=msg)

        self.gui_done = False
        self.running = True
        
        gui_thread = threading.Thread(target=self.gui_loop)
        receive_thread = threading.Thread(target=self.receive)
        
        gui_thread.start()
        receive_thread.start()

    def gui_loop(self):
        self.win = tkinter.Tk()
        self.win.configure(bg="#161616")


        self.chat_label = tkinter.Label(self.win, text=f"{self.nickname}",bg="#E2856E", width=15)
        self.chat_label.config(font=("Segoe UI Black", 12))
        self.chat_label.grid(row=0, column=0, padx=20, pady=5, sticky='n')

        self.text_area = tkinter.scrolledtext.ScrolledText(self.win, bg="#CCDAD1")
        self.text_area.grid(row=1, column=0, padx=20, pady=5, sticky='n')
        self.text_area.config(state='disabled')

        # self.msg_label = tkinter.Label(self.win, text="Message", bg="#E2856E", width=15)
        # self.msg_label.config(font=("Segoe UI Black", 12))
        # self.msg_label.grid(row=2, column=0, padx=20, pady=5, sticky='n')

        self.input_area = tkinter.Text(self.win, height=2, bg="#CCDAD1")
        self.input_area.grid(row=3, column=0, padx=20,pady=5, sticky='w')
        # self.input_area.insert('1.0', 'Enter Message')
        self.input_area.bind('<FocusIn>', self.clear_default_text)
        self.input_area.bind('<FocusOut>', self.restore_default_text)

        self.send_button = tkinter.Button(self.win, text="\u2708", command=self.write)
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
client = Client(HOST, PORT)