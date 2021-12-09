import socket
import time
import random
import string
import os
import sys

#finals
BUFFER_SIZE = 2048
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
    SERVER_PORT = int(sys.argv[1])
except:
    sys.exit()

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
    while True:
        data = client_socket.recv(BUFFER_SIZE)
        client_socket.send(ACCEPT.encode())
        try:
            mark = data.decode()
        except:
            mark = 0

        if(mark == '.'):     
            break
        f.write(data)
    f.close()

def helper(folder_path):
    server_files = os.listdir(folder_path)
    for file in server_files:    
        client_socket.send(file.encode())
        client_socket.recv(BUFFER_SIZE)
        file_path = folder_path + file + '/'
        if os.path.isdir(file_path):
            send_server_file_names(file_path)

def send_server_file_names(folder_path):
    helper(folder_path)
    client_socket.send(END_MARK.encode())
            

def insert_new_folder(folder_path, client_socket):
    #file transfer sequence
    print('getting file')
    file_data = client_socket.recv(BUFFER_SIZE).decode()
    client_socket.send(ACCEPT.encode())
    while(file_data != END_MARK):
        file_name = file_data[1:]
        data_type = file_data[0]     
        if data_type == FOLDER_MARK:
            os.makedirs(folder_path + file_name)
            new_folder_path = folder_path + file_name + '/'        
            #insert file of the new folder
            print('make new folder')
            insert_new_folder(new_folder_path, client_socket)                  
        else:
            #file creation sequence
            new_file = folder_path + file_name
            print('make new file at: ' + new_file)
            make_file(new_file)
        #gets new file name
        print('waiting nex file')
        file_data = client_socket.recv(BUFFER_SIZE).decode()
        print('got nex file')
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
    data = x.read(BUFFER_SIZE)
    while(data):
        client_socket.send(data)
        client_socket.recv(BUFFER_SIZE)
        data = x.read(BUFFER_SIZE)
    client_socket.send(END_MARK.encode())
    client_socket.recv(BUFFER_SIZE)   
    x.close()

def get_folder_files(folder_files , s, folder_path):
    for file_name in folder_files:
        print('new file')
        file_path = folder_path + '/' + file_name
        if os.path.isdir(file_path):
            client_socket.send(str(FOLDER_MARK + file_name).encode())
            #waits for server acceptance
            print('waiting 1')
            client_socket.recv(BUFFER_SIZE)
            #transfer a new folder inside current folder
            new_folder = os.listdir(file_path)
            get_folder_files(new_folder , s ,file_path) 
        else:
            client_socket.send(str(FILE_MARK + file_name).encode())
            #waits for server acceptance
            print('waiting 2')
            client_socket.recv(BUFFER_SIZE)        
            get_file(file_path)

    client_socket.send(END_MARK.encode())
    client_socket.recv(BUFFER_SIZE)

def existing_id_protocol(client_socket, client_id):   
    client_folder_path = SERVER_FOLDER + client_id + '/'
    folder_files = os.listdir(client_folder_path)
    print('getting files for server dir')
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

def send_indication(path):
    file_flag = 1
    if os.path.isdir(path):
            client_socket.send(str(FOLDER_MARK).encode())
            file_flag = 0
    else:
        client_socket.send(str(FILE_MARK).encode())
    client_socket.recv(BUFFER_SIZE)
    return file_flag

def send_update_list_protocol():
    for update in CONNECTED_USERS[client_pc]:
        print(update)
        client_socket.send(str(update).encode())
        client_socket.recv(BUFFER_SIZE)
    client_socket.send(END_MARK.encode())

def send_updates_protocol():
    while len(CONNECTED_USERS[client_pc]) !=0:
        update_info = CONNECTED_USERS[client_pc].pop(0)
        client_socket.send(str(update_info).encode())
        print('stuck 1')
        client_socket.recv(BUFFER_SIZE)
        update_file_name = update_info.split(',')[1]
        update_path = SERVER_FOLDER + client_id + update_file_name
        print('getting indication')
        file_flag = send_indication(update_path)
        if update_info[0] == CREATED:
            if file_flag:
                get_file(update_path)
            else:
                #gets files in folder
                folder_files = os.listdir(update_path)
                #file transer sequence
                print('stuck 2')
                indicator = client_socket.recv(BUFFER_SIZE).decode()
                if indicator == 'continue':
                    get_folder_files(folder_files, client_socket, update_path)

        if update_info[0] == MOVED:
            move_file_name = update_info.split(',')[2]
            move_path = SERVER_FOLDER + client_id + move_file_name
            if '.goutputstream' in str(update_path):
                get_file(move_path)
        try:
            client_socket.settimeout(0.5)
            client_socket.recv(BUFFER_SIZE)
        except Exception:
            pass
        client_socket.settimeout(None)

def get_updates_protocol(size):
    try:
        index = int(size)
    except:
        return 0
    #iterations on update notes
    for x in range(index):  
        print('new update')
        update = client_socket.recv(BUFFER_SIZE).decode()
        client_socket.send(ACCEPT.encode())
        for pc in USER_DICT[client_id]:
            if pc != client_pc:
                CONNECTED_USERS[pc].append(update)
        update_info = update.split(',')
        #update type can be c-created m-moved d-deleted
        update_type = update_info[0]
        #the path of the file that will be updated
        update_path = update_info[1]
        #file type can be @-folder f-file
        file_type = get_indication()
        path = SERVER_FOLDER + client_id + update_path
        print(path)
        #file was created
        if update_type == CREATED :
            try:
                if file_type == FOLDER_MARK:
                    os.makedirs(path)
                    folder_path = path + '/'
                    client_socket.send(b'continue')
                    insert_new_folder(folder_path, client_socket)
                else:
                    make_file(path)
            except Exception:
                client_socket.send(b'pass')
                continue
        #file was deleted
        elif update_type == DELETED :
            try:
                delete_file(path)
            except Exception:
                client_socket.send(ACCEPT.encode())
                continue
        #file was moved
        else:
            new_path = update_info[2]
            new_path = SERVER_FOLDER + '/' + client_id + new_path
            if '.goutputstream' in path:
                delete_file(new_path)
                make_file(new_path)
            else:
                try:
                    os.replace(path,new_path)
                except Exception:
                    client_socket.send(ACCEPT.encode())
                    pass
        client_socket.send(ACCEPT.encode())
            
#main
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', SERVER_PORT))
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
    else:
        if(client_pc not in USER_DICT[client_id]):
            #add new client connection
            USER_DICT[client_id].append(client_pc)
            CONNECTED_USERS[client_pc] = []
            print('sending update list')
            path = SERVER_FOLDER + client_id + '/'
            send_server_file_names(path)
            print('entering ex id prot')
            existing_id_protocol(client_socket, client_id)
            print('finished ex id prot')

        try:
            client_socket.settimeout(0.5)
            update_size = client_socket.recv(BUFFER_SIZE).decode()
            print('got updates')
            client_socket.send(ACCEPT.encode())
        except:
            update_size = '0'

        client_socket.settimeout(None)
        if update_size != '0' and update_size != '':
            print('getting updates')
            get_updates_protocol(update_size)    

        #sends new updates to client (if there is any)
        if len(CONNECTED_USERS[client_pc]) != 0:
            client_socket.send(str(len(CONNECTED_USERS[client_pc])).encode())
            client_socket.recv(BUFFER_SIZE)
            print('sending update list')
            send_update_list_protocol()
            print('sending updates')
            send_updates_protocol()
            print('finished sending uppdates')
        else:
            client_socket.send(b'0')   

        #pc operation stack isn't empty
        
    client_socket.close()
    print(client_address,' disconnected')