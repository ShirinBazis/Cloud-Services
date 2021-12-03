import socket
import time
import random
import string
import os
import sys
import watchdog

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

DEST_IP = 12550

#list of client ids
ID_LIST = []
CONNECTED_USERS = {}
USER_DICT = {}

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

def new_id_protocol(client_socket,client_id, client_pc):

    #enter a new connection of the client
    USER_DICT[client_id] = [client_pc]
    CONNECTED_USERS[client_pc] = []

    #makes a new folder in the server folder for the files of the client
    os.makedirs(SERVER_FOLDER + client_id)
    folder_path = SERVER_FOLDER + client_id + '/'
    insert_new_folder(folder_path, client_socket)

def get_folder_files(folder_files , s, folder_path):
    for file_name in folder_files:
        file_path = folder_path + '/' + file_name
        if os.path.isdir(file_path):
            s.send(str(FOLDER_MARK + file_name).encode())           
            #waits for client's acceptance
            s.recv(BUFFER_SIZE)
            #transfer a new folder inside current folder
            new_folder = os.listdir(file_path)
            get_folder_files(new_folder , s ,file_path)
            #waits for client's acceptance
            s.recv(BUFFER_SIZE)
    
        else:
            s.send(str(FILE_MARK + file_name).encode())
            #waits for client's acceptance
            s.recv(BUFFER_SIZE)
            x = open(file_path, 'rb')
            #reads and sends bytes
            data = x.read(BUFFER_SIZE)
            while(data):
                s.send(data)
                #waits for client's acceptance
                s.recv(BUFFER_SIZE)
                data = x.read(BUFFER_SIZE)              
            s.send(END_MARK.encode())
            #waits for client's acceptance
            s.recv(BUFFER_SIZE)
    s.send(END_MARK.encode())

def existing_id_protocol(client_socket, client_id):   
    client_folder_path = SERVER_FOLDER + client_id + '/'
    folder_files = os.listdir(client_folder_path)
    get_folder_files(folder_files, client_socket, client_folder_path)
        
#main
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', DEST_IP))
server.listen(5)

while True:
    client_socket, client_address = server.accept()     
    print(client_address[1],' connected')
    data = client_socket.recv(BUFFER_SIZE).decode()
    client_info = data.split(',')
    client_id = client_info[0]
    client_pc = client_info[1]  
    client_socket.send(ACCEPT.encode())

    #new id protocol
    if(client_id == DEFAULT_ID):
        #generates a new id number for client
        client_id = id_generator()
        print(client_id)
        #sends to client his new sid number
        client_socket.send(client_id.encode())
        #print(client_address[1],' connected')
        new_id_protocol(client_socket,client_id, client_pc)
        client_socket.close()
        continue
    else:
        print(client_pc)
        if(client_pc not in USER_DICT[client_id]):
            print('new pc')
            #add new client connection
            USER_DICT[client_id].append(client_pc)
            CONNECTED_USERS[client_pc] = []
            existing_id_protocol(client_socket, client_id)
            client_socket.close()
            continue

        new_data = client_socket.recv(BUFFER_SIZE).decode()
        if new_data != '0':
            for pc in USER_DICT[client_id]:
                if pc != client_pc:
                    CONNECTED_USERS[pc].append(new_data)

        #pc operation stack isn't empty
        if len(CONNECTED_USERS[client_pc]) != 0:
            #while len(CONNECTED_USERS[client_pc]) != 0:
            client_socket.send('update'.encode())
            CONNECTED_USERS[client_pc].pop(0)
        else:
            client_socket.send('reg'.encode())

    client_socket.close()
    print(client_address,' disconnected')