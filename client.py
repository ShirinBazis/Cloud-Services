import socket
import time
import sys
import os
import string
import random
import watchdog.observers
import watchdog.events

#finals
BUFFER_SIZE = 5000
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
    DIRECTORY_PATH = '/home/odin/Desktop/new2'
    TIME_INTERVAL = sys.argv[4]
    
except:
    pass

try:
    ID_NUM = sys.argv[5]

except:
    ID_NUM = DEFAULT_ID
DEST_PORT = 12864
DIRECTORY_PATH = '/home/odin/Desktop/new2'

UPDATES_LIST = []

def on_created(event):
    update = CREATED + ',' + str(event.src_path).split(DIRECTORY_PATH)[1]
    if '.goutputstream' not in event.src_path:
        UPDATES_LIST.append(update)
def on_deleted(event):
    update = DELETED + ',' + str(event.src_path).split(DIRECTORY_PATH)[1]
    UPDATES_LIST.append(update)
def on_modified(event):
    pass
def on_moved(event):
    update = MOVED + ',' + str(event.src_path).split(DIRECTORY_PATH)[1] + ',' + str(event.dest_path).split(DIRECTORY_PATH)[1]
    UPDATES_LIST.append(update)

def get_file(file_path):
    x = open(file_path, 'rb')
    data = x.read(BUFFER_SIZE)
    while(data):
        s.send(data)
        data = x.read(BUFFER_SIZE)
    s.recv(BUFFER_SIZE)
    x.close()

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
    while True:
        try:
            s.settimeout(0.08)
            data = s.recv(BUFFER_SIZE)
            f.write(data)
        except:
            break
    s.settimeout(None)
    s.send(ACCEPT.encode())
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

def get_indication():
    file_type = s.recv(BUFFER_SIZE).decode()
    s.send(ACCEPT.encode())
    return file_type

def send_indication(path):
    file_flag = 1
    if os.path.isdir(path):
            s.send(str(FOLDER_MARK).encode())
            file_flag = 0
    else:
        s.send(str(FILE_MARK).encode())
    s.recv(BUFFER_SIZE)
    return file_flag

def send_updates_protocol():
    while len(UPDATES_LIST) !=0:
        update_info = UPDATES_LIST.pop(0)
        s.send(str(update_info).encode())
        s.recv(BUFFER_SIZE)
        update_file_name = update_info.split(',')[1]
        update_path = DIRECTORY_PATH + update_file_name
        file_flag = send_indication(update_path)
        if update_info[0] == CREATED:
            if file_flag:
                get_file(update_path)
            else:
                #gets files in folder
                folder_files = os.listdir(update_path)
                #file transer sequence
                indicator = s.recv(BUFFER_SIZE).decode()
                if indicator == 'continue':
                    get_folder_files(folder_files, s, update_path)

        if update_info[0] == MOVED:
            move_file_name = update_info.split(',')[2]
            move_path = DIRECTORY_PATH + move_file_name
            if '.goutputstream' in str(update_path):
                get_file(move_path)
        try:
            s.settimeout(0.5)
            s.recv(BUFFER_SIZE)
        except Exception:         
            pass
        s.settimeout(None)

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
    except Exception:
        remove_dir(path)

def get_updates_protocol(size):
    try:
        index = int(size)
    except:
        return 0
    for x in range(index):
        update = s.recv(BUFFER_SIZE).decode()
        s.send(ACCEPT.encode())    
        update_info = update.split(',')
        #update type can be c-created m-moved d-deleted
        update_type = update_info[0]
        #the path of the file that will be updated
        update_path = update_info[1]
        #file type can be @-folder f-file
        file_type = get_indication()
        path = DIRECTORY_PATH + update_path
        #file was created
        if update_type == CREATED :
            try:
                if file_type == FOLDER_MARK:
                    os.makedirs(path)
                    folder_path = path + '/'
                    s.send(b'continue')
                    insert_new_folder(folder_path, s)
                else:
                    make_file(path)
            except Exception:
                s.send(b'pass')
                pass
        #file was deleted
        elif update_type == DELETED :
            try:
                delete_file(path)
            except Exception:
                s.send(ACCEPT.encode())
                continue
        #file was moved
        else:
            new_path = update_info[2]
            new_path = DIRECTORY_PATH + new_path
            if '.goutputstream' in path:
                delete_file(new_path)
                make_file(new_path)
            else:
                try:
                    os.replace(path,new_path)
                except Exception:
                    s.send(ACCEPT.encode())
                    continue
            
        s.send(ACCEPT.encode())

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

    if len(UPDATES_LIST) != 0:
        s.send(str(len(UPDATES_LIST)).encode())
        #waits for server's acceptance
        s.recv(BUFFER_SIZE)
        send_updates_protocol()

    update_size = s.recv(BUFFER_SIZE).decode()
    if update_size != '0' and update_size != '':
        s.send(ACCEPT.encode())
        get_updates_protocol(update_size)
        UPDATES_LIST = []



    