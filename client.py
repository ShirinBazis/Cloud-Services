import socket
import time
import sys
import os
import string
import random
import watchdog.observers
import watchdog.events

#finals
BUFFER_SIZE = 2000
END_MARK = '.'
DEFAULT_ID = '0'
LOCAL_ID_LEN = 36
ID_LEN = 128
FOLDER_MARK = '@'
FILE_MARK = 'f'
ACCEPT = 'ok'
CREATED = 'c'
MOVED = 'm'
DELETED = 'd'


try:
    DEST_IP = sys.argv[1]
    DEST_PORT = int(sys.argv[2])
    #FILE_PATH = sys.argv[3]
    #DIRECTORY_PATH = '/home/odin/Desktop/test file'
    DIRECTORY_PATH = '/home/odin/Desktop/new1'
    TIME_INTERVAL = sys.argv[4]
    
except:
    pass

try:
    ID_NUM = sys.argv[5]

except:
    ID_NUM = DEFAULT_ID
DEST_PORT = 12783
DIRECTORY_PATH = '/home/odin/Desktop/new1'

UPDATES_LIST = []

def on_created(event):
    print('created at: ',event.src_path)
    update = CREATED + ',' + event.src_path
    if 'goutputstream' not in event.src_path:
        UPDATES_LIST.append(update)
def on_deleted(event):
    print('deleted at: ' + event.src_path)
    update = DELETED + ',' + event.src_path
    UPDATES_LIST.append(update)
def on_modified(event):
    pass
def on_moved(event):
    print('moved from '+ event.src_path +' to '+ event.dest_path)
    update = MOVED + ',' + event.src_path + ',' + event.dest_path
    UPDATES_LIST.append(update)

def get_file(file_path):
    x = open(file_path, 'rb')
    #reads and sends bytes
    data = x.read(BUFFER_SIZE)
    while(data):
        s.send(data)
        #waits for server acceptance
        s.recv(BUFFER_SIZE)
        data = x.read(BUFFER_SIZE)              
    s.send(str(END_MARK).encode())
            #waits for server acceptance
    s.recv(BUFFER_SIZE)

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

def new_id_protocol(s):
    #gets files in folder
    folder_files = os.listdir(DIRECTORY_PATH)
    #file transer sequence
    get_folder_files(folder_files, s, DIRECTORY_PATH)
    
def make_file(new_file):
    f = open(new_file,'wb')
    #gets file bytes from client
    data = s.recv(BUFFER_SIZE)
    s.send(ACCEPT.encode())
    try:
        end_check = data.decode()
    except:
        end_check = 0
    while(end_check != END_MARK):
        f.write(data)
        data = s.recv(BUFFER_SIZE)
        s.send(ACCEPT.encode())
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

def existing_id_protocol(s):
    folder_path = DIRECTORY_PATH + '/'
    insert_new_folder(folder_path, s)
    
def local_id_generator(size = LOCAL_ID_LEN, chars=string.ascii_uppercase + string.digits):
    new_id = ''.join(random.choice(chars) for _ in range(size))
    return new_id

def send_indication(path):
    file_flag = 1
    if os.path.isdir(path):
            print(path + ' is dir')
            s.send(str(FOLDER_MARK).encode())
            file_flag = 0
    else:
        print(path + ' is not a dir')
        s.send(str(FILE_MARK).encode())
    s.recv(BUFFER_SIZE)
    return file_flag

def updates_protocol():
    #send client's file name for reference
    s.send(str(DIRECTORY_PATH.split('/')[-1]).encode())
    s.recv(BUFFER_SIZE)
    while len(UPDATES_LIST) !=0:
        update_info = UPDATES_LIST.pop(0)
        print(update_info)
        print('stuck 1')
        s.send(str(update_info).encode())
        s.recv(BUFFER_SIZE)
        update_path = update_info.split(',')[1]
        print('up path: ' + update_path)
        file_flag = send_indication(update_path)
        print('stuck 2')
        if update_info[0] == CREATED:
            if file_flag:
                get_file(update_path)
            else:
                #gets files in folder
                folder_files = os.listdir(DIRECTORY_PATH)
                #file transer sequence
                get_folder_files(folder_files, s, DIRECTORY_PATH)

        if update_info[0] == MOVED:
            move_path = update_info.split(',')[2]
            print('move path: ' + move_path)
            if 'goutputstream' in str(update_path):
                get_file(move_path)

        s.recv(BUFFER_SIZE)
        print('finish')

def get_port(cur_port):
    if((cur_port - 12560) == 9):
        return 12560
    return cur_port + 1

def handler():
    event_handler = watchdog.events.PatternMatchingEventHandler()
    event_handler.on_created = on_created
    event_handler.on_deleted = on_deleted
    event_handler.on_modified = on_modified
    event_handler.on_moved = on_moved
    return event_handler

#main
local_id = local_id_generator()  

event_handler = handler()
observer = watchdog.observers.Observer()
observer.schedule(event_handler, DIRECTORY_PATH, recursive = True)
observer.start()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.connect((DEST_IP, DEST_PORT))
s.connect(('127.0.0.1', DEST_PORT))

#sends identification
id = ID_NUM + ',' + local_id
s.send(str(id).encode())
#waits for server's acceptance
s.recv(BUFFER_SIZE)

#new id protocol
if(ID_NUM == DEFAULT_ID):
    #gets an id from server
    ID_NUM = s.recv(ID_LEN).decode()
    id = ID_NUM + ',' + local_id
    new_id_protocol(s)          
else:
    existing_id_protocol(s)
    UPDATES_LIST = []
   
s.close()
while(True):
    flag = 0
    #time.sleep(TIME_INTERVAL)
    time.sleep(3)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.connect((DEST_IP, DEST_PORT))
    s.connect(('127.0.0.1', DEST_PORT))
    s.send(str(id).encode())
    #waits for server's acceptance
    s.recv(BUFFER_SIZE)

    new_data = s.recv(6).decode()
    if new_data == 'update':
        print('update')
    s.close()

    if len(UPDATES_LIST) != 0:
        s.send(str(len(UPDATES_LIST)).encode())
        #waits for server's acceptance
        s.recv(BUFFER_SIZE)
        updates_protocol()

    