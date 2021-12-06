import socket
import time
import random
import string
import os
import sys

#finals
BUFFER_SIZE = 2000
END_MARK = '.'
ACCEPT = 'ok'
DEFAULT_ID = '0'
ID_LEN = 128
FOLDER_MARK = '@' 
FILE_MARK = 'f'
CREATED = 'c'
MOVED = 'm'
DELETED = 'd'

try:
    DEST_IP = sys.argv[1]
except:
    DEST_IP = 0
DEST_IP = 12782

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

def make_file(new_file):
    f = open(new_file,'wb')
    #gets file bytes from client
    data = client_socket.recv(BUFFER_SIZE)
    client_socket.send(ACCEPT.encode())
    try:
        end_check = data.decode()
    except:
        end_check = 0
    while(end_check != END_MARK):
        f.write(data)
        data = client_socket.recv(BUFFER_SIZE)
        client_socket.send(ACCEPT.encode())
        try:
            end_check = data.decode()
        except:
            end_check = 0
    f.close()

def insert_new_folder(folder_path, client_socket):
    #file transfer sequence
    file_data = client_socket.recv(BUFFER_SIZE).decode()
    client_socket.send(ACCEPT.encode())
    while(file_data != END_MARK):
        file_name = file_data[1:]
        data_type = file_data[0]     
        if data_type == FOLDER_MARK:
            os.makedirs(folder_path + file_name)
            new_folder_path = folder_path + file_name + '/'        
            #insert file of the new folder
            insert_new_folder(new_folder_path, client_socket)                  
        else:
            #file creation sequence
            new_file = folder_path + file_name
            make_file(new_file)
        #gets new file name
        file_data = client_socket.recv(BUFFER_SIZE).decode()
        client_socket.send(ACCEPT.encode())

def new_id_protocol(client_socket,client_id, client_pc):
    #enter a new connection of the client
    USER_DICT[client_id] = [client_pc]
    CONNECTED_USERS[client_pc] = []
    #makes a new folder in the server folder for the files of the client
    os.makedirs(SERVER_FOLDER + client_id)
    folder_path = SERVER_FOLDER + client_id + '/'
    insert_new_folder(folder_path, client_socket)

def get_file(file_path):
    x = open(file_path, 'rb')
    #reads and sends bytes
    data = x.read(BUFFER_SIZE)
    while(data):
        client_socket.send(data)
        #waits for server acceptance
        client_socket.recv(BUFFER_SIZE)
        data = x.read(BUFFER_SIZE)              
    client_socket.send(str(END_MARK).encode())
            #waits for server acceptance
    client_socket.recv(BUFFER_SIZE)

def get_folder_files(folder_files , s, folder_path):
    for file_name in folder_files:
        file_path = folder_path + '/' + file_name
        if os.path.isdir(file_path):
            s.send(str(FOLDER_MARK + file_name).encode())
            #waits for server acceptance
            s.recv(BUFFER_SIZE)
            #transfer a new folder inside current folder
            new_folder = os.listdir(file_path)
            get_folder_files(new_folder , s ,file_path) 
        else:
            s.send(str(FILE_MARK + file_name).encode())
            #waits for server acceptance
            s.recv(BUFFER_SIZE)        
            get_file(file_path)

    s.send(END_MARK.encode())
    s.recv(BUFFER_SIZE)

def existing_id_protocol(client_socket, client_id):   
    client_folder_path = SERVER_FOLDER + client_id + '/'
    folder_files = os.listdir(client_folder_path)
    get_folder_files(folder_files, client_socket, client_folder_path)

def remove_dir(dir_path):
    folder_files = os.listdir(dir_path)
    for file in folder_files:
        file_path = dir_path + '/' + file
        if os.path.isdir(file_path):
            remove_dir(file_path)
        else:
            os.remove(file_path)
    os.rmdir(dir_path)

def delete_file(path):
    try:
        os.remove(path)
    except:
        remove_dir(path)

def get_indication():
    file_type = client_socket.recv(BUFFER_SIZE).decode()
    client_socket.send(ACCEPT.encode())
    return file_type

def new_updates_protocol(size):
    #gets client's folder name for a specific split that will occur later
    client_folder_name = client_socket.recv(BUFFER_SIZE).decode()
    print('client folder: ' + client_folder_name)
    client_socket.send(ACCEPT.encode())
    #iterations on update notes
    for x in range(int(size)):  
        update = client_socket.recv(BUFFER_SIZE).decode()
        for pc in USER_DICT[client_id]:
            CONNECTED_USERS[pc].append(update)
        update_info = update.split(',')
        client_socket.send(ACCEPT.encode())
        #update type can be c-created m-moved d-deleted
        update_type = update_info[0]
        #the path of the file that will be updated
        update_path = update_info[1]
        #the actuall name of the file
        file_name = update_path.split(client_folder_name)[1]
        #file type can be @-folder f-file
        file_type = get_indication()
        path = SERVER_FOLDER + client_id + file_name
        #file was created
        if update_type == CREATED :
            try:
                if file_type == FOLDER_MARK:
                    os.makedirs(path)
                    folder_path = path + '/'
                    insert_new_folder(folder_path, client_socket)
                else:
                    make_file(path)
            except:
                pass
        #file was deleted
        elif update_type == DELETED :
            try:
                delete_file(path)
            except:
                pass
        #file was moved
        else:
            new_path = update_info[2].split(client_folder_name)[1]
            new_path = SERVER_FOLDER + client_id + new_path
            try:
                os.replace(path,new_path)
            except:
                pass         
            if 'goutputstream' in path:
                delete_file(new_path)
                make_file(new_path)

        client_socket.send(ACCEPT.encode())
            
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
        print('pc: ' + client_pc)
        if(client_pc not in USER_DICT[client_id]):
            #add new client connection
            USER_DICT[client_id].append(client_pc)
            CONNECTED_USERS[client_pc] = []
            existing_id_protocol(client_socket, client_id)
            client_socket.close()
            continue
        #sends new updates to client (if there is any)
        if len(CONNECTED_USERS[client_pc]) != 0:
            print(CONNECTED_USERS[client_pc])
            client_socket.send('update'.encode())
        else:
            client_socket.send('reg'.encode())

        try:
            client_socket.settimeout(0.5)
            update_size = client_socket.recv(BUFFER_SIZE).decode()
            client_socket.send(ACCEPT.encode())
        except:
            update_size = '0'
        if update_size != '0' and update_size != '':
            client_socket.settimeout(None)
            new_updates_protocol(update_size)

        #pc operation stack isn't empty
        
    client_socket.close()
    print(client_address,' disconnected')