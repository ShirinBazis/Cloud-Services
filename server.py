import socket
import time
import random
import string
import os
import sys

#finals
BUFFER_SIZE = 2300
END_MARK = '.'
ACCEPT = 'ok'
DEFAULT_ID = '0'
ID_LEN = 128
FOLDER_MARK = '@'
FILE_MARK = 'f'

try:
    DEST_IP = sys.argv[1]
except:
    DEST_IP = 0

#list of client ids
ID_LIST = []
SERVER_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/'

def id_generator(size = ID_LEN, chars=string.ascii_uppercase + string.digits):
    new_id = ''.join(random.choice(chars) for _ in range(size))
    while (new_id in ID_LIST):
        new_id = ''.join(random.choice(chars) for _ in range(size))
    ID_LIST.append(new_id)
    return new_id

def insert_new_folder(folder_path, client_socket):
    #file transfer sequence
    file_data = client_socket.recv(BUFFER_SIZE).decode()
    while(file_data != END_MARK):
        file_name = file_data[1:]
        data_type = file_data[0]
        if data_type == FOLDER_MARK:
            os.makedirs(folder_path + file_name)
            new_folder_path = folder_path + file_name + '/'   
            #sends approval       
            client_socket.send(ACCEPT.encode())
            #insert file of the new folder
            insert_new_folder(new_folder_path, client_socket)
            #sends approval
            client_socket.send(ACCEPT.encode())
            
        else:
            client_socket.send(ACCEPT.encode())
            #file creation sequence
            new_file = folder_path + file_name
            f = open(new_file,'wb')
            #gets file bytes from client
            data = client_socket.recv(BUFFER_SIZE)
            try:
                end_check = data.decode()
            except:
                end_check = 0
            while(end_check != END_MARK):
                f.write(data)
                client_socket.send(ACCEPT.encode())
                data = client_socket.recv(BUFFER_SIZE)
                try:
                    end_check = data.decode()
                except:
                    end_check = 0
            f.close()
            #sends approval
            client_socket.send(ACCEPT.encode())
            #gets new file name
        file_data = client_socket.recv(BUFFER_SIZE).decode()

def new_id_protocol(client_socket):
    #generates a new id number for client
    id_num = id_generator()
    #sends to client his new id number
    client_socket.send(id_num.encode())
    print(id_num)
    #makes a new folder in the server folder for the files of the client
    os.makedirs(SERVER_FOLDER + id_num)
    folder_path = SERVER_FOLDER + id_num + '/'
    insert_new_folder(folder_path, client_socket)  

def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', 12353))
    server.listen(5)

    while True:
        client_socket, client_address = server.accept()
        data = client_socket.recv(BUFFER_SIZE)
        #new id protocol
        if(data.decode() == DEFAULT_ID):
            new_id_protocol(client_socket)
            
        client_socket.close()

def main():
    run_server()

if __name__ == '__main__':
    main()