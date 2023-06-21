import socket
import struct
import pickle
import threading

HOST = '10.5.30.90'
PORT = 6969

# Membuat socket server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(4)

# Informasi terkait klien yang terhubung
clients_connected = {}
clients_data = {}
count = 1


def connection_requests():
    global count
    while True:
        print("Waiting for connection...")
        # Menerima permintaan koneksi dari klien
        client_socket, address = server_socket.accept()

        print(f"Connections from {address} has been established")
        print(len(clients_connected))

        # Membatasi jumlah klien yang dapat terhubung
        if len(clients_connected) == 4:
            client_socket.send('not_allowed'.encode())

            client_socket.close()
            continue
        else:
            client_socket.send('allowed'.encode())

        try:
            # Menerima nama klien
            client_name = client_socket.recv(1024).decode('utf-8')
        except:
            print(f"{address} disconnected")
            client_socket.close()
            continue

        print(f"{address} identified itself as {client_name}")

        # Menambahkan informasi klien yang terhubung
        clients_connected[client_socket] = (client_name, count)

        # Menerima ukuran gambar dalam bentuk byte
        image_size_bytes = client_socket.recv(1024)
        image_size_int = struct.unpack('i', image_size_bytes)[0]

        client_socket.send('received'.encode())
        # Menerima ekstensi gambar
        image_extension = client_socket.recv(1024).decode()

        b = b''
        while True:
            # Menerima data gambar
            image_bytes = client_socket.recv(1024)
            b += image_bytes
            if len(b) == image_size_int:
                break

        # Menyimpan data klien yang terhubung
        clients_data[count] = (client_name, b, image_extension)

        clients_data_bytes = pickle.dumps(clients_data)

        clients_data_length = struct.pack('i', len(clients_data_bytes))

        # Mengirimkan ukuran data klien ke klien terkait
        client_socket.send(clients_data_length)
        # Mengirimkan data klien ke klien terkait
        client_socket.send(clients_data_bytes)

        if client_socket.recv(1024).decode() == 'image_received':
            # Mengirimkan ID klien ke klien terkait
            client_socket.send(struct.pack('i', count))

            for client in clients_connected:
                if client != client_socket:
                    # Mengirim notifikasi ke klien lain bahwa klien baru telah bergabung
                    client.send('notification'.encode())
                    data = pickle.dumps(
                        {'message': f"{clients_connected[client_socket][0]} joined the chat", 'extension': image_extension,
                         'image_bytes': b, 'name': clients_connected[client_socket][0], 'n_type': 'joined', 'id': count})
                    data_length_bytes = struct.pack('i', len(data))
                    # Mengirim data bergabung ke klien lain
                    client.send(data_length_bytes)
                    client.send(data)

        # Meningkatkan hitungan untuk ID klien berikutnya
        count += 1
        # Membuat thread baru untuk menerima data dari klien
        t = threading.Thread(target=receive_data, args=(client_socket,))
        t.start()


def receive_data(client_socket):
    while True:
        try:
            # Menerima data dari klien
            data_bytes = client_socket.recv(1024)
        except ConnectionResetError:
            # Menangani jika koneksi dengan klien terputus secara tiba-tiba (ConnectionResetError)
            print(f"{clients_connected[client_socket][0]} disconnected")

            for client in clients_connected:
                if client != client_socket:
                    # Mengirim notifikasi ke klien lain bahwa klien telah keluar
                    client.send('notification'.encode())

                    data = pickle.dumps({'message': f"{clients_connected[client_socket][0]} left the chat",
                                         'id': clients_connected[client_socket][1], 'n_type': 'left'})

                    data_length_bytes = struct.pack('i', len(data))
                    # Mengirim data keluar ke klien lain
                    client.send(data_length_bytes)
                    client.send(data)

            # Menghapus data klien yang keluar
            del clients_data[clients_connected[client_socket][1]]
            del clients_connected[client_socket]
            client_socket.close()
            break
        except ConnectionAbortedError:
            # Menangani jika koneksi dengan klien terputus secara tiba-tiba (ConnectionAbortedError)
            print(
                f"{clients_connected[client_socket][0]} disconnected unexpectedly.")

            for client in clients_connected:
                if client != client_socket:
                    # Mengirim notifikasi ke klien lain bahwa klien telah keluar
                    client.send('notification'.encode())
                    data = pickle.dumps({'message': f"{clients_connected[client_socket][0]} left the chat",
                                         'id': clients_connected[client_socket][1], 'n_type': 'left'})
                    data_length_bytes = struct.pack('i', len(data))
                    # Mengirim data keluar ke klien lain
                    client.send(data_length_bytes)
                    client.send(data)

            # Menghapus data klien yang keluar
            del clients_data[clients_connected[client_socket][1]]
            del clients_connected[client_socket]
            client_socket.close()
            break

        for client in clients_connected:
            if client != client_socket:
                # Mengirim data kepada klien lain
                client.send('message'.encode())
                client.send(data_bytes)


# Memanggil fungsi untuk menerima permintaan koneksi
connection_requests()
