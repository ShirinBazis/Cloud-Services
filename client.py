import socket
import time
import sys
import os
import string
import random
import watchdog.observers
import watchdog.events

UPDATE_FLAG = 0

#finals
BUFFER_SIZE = 2048
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
    FILE_PATH = sys.argv[3]  
    TIME_INTERVAL = int(sys.argv[4])
except:
    sys.exit()
    
try:
    ID_NUM = sys.argv[5]
    os.makedirs(FILE_PATH)

except: 
    ID_NUM = DEFAULT_ID

if not (0 < DEST_PORT and DEST_PORT <= 65535):
    sys.exit()

test_ip = DEST_IP.split('.')
if len(test_ip) != 4:
    sys.exit()
for seg in test_ip:
    if not ('0' <= seg and seg <= '255'):
        sys.exit()

UPDATES_LIST = []
INCOMING_UPDATES = []
SERVER_FILES = []

def on_created(event):
    print('path at: '+ event.src_path)
    file_path = str(event.src_path).split(FILE_PATH)[1]
    print('modified path: '+ file_path)
    file_Name = file_path.split('/')[-1]
    print('file name: '+ file_Name)
    update = CREATED + ',' + file_path
    if '.goutputstream' not in event.src_path:
        print(UPDATE_FLAG)
        if UPDATE_FLAG == 0:
            print('created')
            print('flag is 0')
            UPDATES_LIST.append(update)
        elif UPDATE_FLAG == 1:
            print('flag is 1')
            if update not in INCOMING_UPDATES:
                UPDATES_LIST.append(update)
        else:
            if file_Name not in SERVER_FILES:
                UPDATES_LIST.append(update)

def on_deleted(event):
    file_path = str(event.src_path).split(FILE_PATH)[1]
    file_Name = file_path.split('/')[-1]
    update = DELETED + ',' + file_path
    print(UPDATE_FLAG)
    if UPDATE_FLAG == 0:
        print('deleted')
        UPDATES_LIST.append(update)
    elif UPDATE_FLAG == 1:
        print('flag is 1')
        if update not in INCOMING_UPDATES:
            UPDATES_LIST.append(update)
    else:
        if file_Name not in SERVER_FILES:
            UPDATES_LIST.append(update)

def on_modified(event):
    pass

def on_moved(event):
    file_path = str(event.dest_path).split(FILE_PATH)[1]
    file_Name = file_path.split('/')[-1]
    update = MOVED + ',' + str(event.src_path).split(FILE_PATH)[1] + ',' + file_path
    print(UPDATE_FLAG)
    if UPDATE_FLAG == 0:
        print('moved')
        UPDATES_LIST.append(update)
    elif UPDATE_FLAG == 1:
        print('flag is 1')
        if update not in INCOMING_UPDATES:
            UPDATES_LIST.append(update)
    else:
        if file_Name not in SERVER_FILES:
            UPDATES_LIST.append(update)
            

def get_file(file_path):
    x = open(file_path, 'rb')
    data = x.read(BUFFER_SIZE)
    while(data):
        s.send(data)
        s.recv(BUFFER_SIZE)
        data = x.read(BUFFER_SIZE)
    s.send(END_MARK.encode())
    s.recv(BUFFER_SIZE)
    x.close()

def get_folder_files(folder_files , s, folder_path):
    for file_name in folder_files:
        file_path = folder_path + '/' + file_name
        if os.path.isdir(file_path):
            print('send mark+name')
            s.send(str(FOLDER_MARK + file_name).encode())
            #waits for server acceptance
            s.recv(BUFFER_SIZE)
            #transfer a new folder inside current folder
            new_folder = os.listdir(file_path)
            print('sending dir')
            new_path = file_path + '/'
            get_folder_files(new_folder , s ,new_path)
    
        else:
            print('send mark+name')
            s.send(str(FILE_MARK + file_name).encode())
            #waits for server acceptance
            s.recv(BUFFER_SIZE)
            print('sending file')
            get_file(file_path)

    s.send(END_MARK.encode())
    s.recv(BUFFER_SIZE)

def new_id_protocol(s):
    #gets files in folder
    folder_files = os.listdir(FILE_PATH)
    #file transer sequence
    get_folder_files(folder_files, s, FILE_PATH)

def make_file(new_file):
    f = open(new_file,'wb')
    while True:
        data = s.recv(BUFFER_SIZE)
        s.send(ACCEPT.encode())
        try:
            mark = data.decode()
        except:
            mark = 0
        if(mark == '.'):     
            break
        f.write(data)
    f.close()
    print('finished making file')

def get_update_list_protocol():
    list = []
    while True:
        update = s.recv(BUFFER_SIZE).decode()
        if update != END_MARK:
            print(update)
            list.append(update)
            s.send(ACCEPT.encode())
        else:
            break
    return list

def get_server_file_names():
    list = []
    while True:
        print('stuck')
        try:
            s.settimeout(0.1)
            file_name = s.recv(BUFFER_SIZE).decode()
        except:
            s.settimeout(None)
            s.send(ACCEPT.encode())
            file_name = s.recv(BUFFER_SIZE).decode()
        print(file_name)
        if file_name != END_MARK:
            print(file_name)
            list.append(file_name)
            s.send(ACCEPT.encode())
        else:
            break
    return list
        

def insert_new_folder(folder_path, client_socket):
    #file transfer sequence
    print('stuck 1')
    file_data = client_socket.recv(BUFFER_SIZE).decode()
    client_socket.send(ACCEPT.encode())
    while(file_data != END_MARK):
        print(file_data)
        file_name = file_data[1:]
        data_type = file_data[0]
        print('type is: ' +data_type)
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
        print('stuck 2')
        file_data = client_socket.recv(BUFFER_SIZE)
        print(file_data)
        file_data = file_data.decode()
        client_socket.send(ACCEPT.encode())

def existing_id_protocol(s):
    folder_path = FILE_PATH + '/'
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
        print('sending update')
        update_info = UPDATES_LIST.pop(0)
        s.send(str(update_info).encode())
        print('stcuk 1')
        slip = s.recv(BUFFER_SIZE).decode()
        print('first rec need ack: ' + slip)
        update_file_name = update_info.split(',')[1]
        update_path = FILE_PATH + update_file_name
        print('sending indi')
        file_flag = send_indication(update_path)
        print('sent indi')
        if update_info[0] == CREATED:
            if file_flag:
                get_file(update_path)
            else:
                #gets files in folder
                folder_files = os.listdir(update_path)
                #file transer sequence
                print('stcuk 2')
                if slip == 'continue' or slip == 'pass':
                    get_folder_files(folder_files, s, update_path)
                else:
                    indicator = s.recv(BUFFER_SIZE).decode()
                    print('indi: ' + indicator)
                    if indicator == 'continue':
                        get_folder_files(folder_files, s, update_path)

        if update_info[0] == MOVED:
            move_file_name = update_info.split(',')[2]
            move_path = FILE_PATH + move_file_name
            if '.goutputstream' in str(update_path):
                get_file(move_path)
        try:
            s.settimeout(0.5)
            test = s.recv(BUFFER_SIZE)
            print('needs to be ack: ' + test)
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
        print('new update stuck 1')
        update = s.recv(BUFFER_SIZE).decode()
        s.send(ACCEPT.encode())    
        update_info = update.split(',')
        #update type can be c-created m-moved d-deleted
        update_type = update_info[0]
        #the path of the file that will be updated
        update_path = update_info[1]
        #file type can be @-folder f-file
        print('geting indication')
        file_type = get_indication()
        path = FILE_PATH + update_path
        #file was created
        if update_type == CREATED :
            try:
                if file_type == FOLDER_MARK:
                    os.makedirs(path)
                    folder_path = path + '/'
                    s.send(b'continue')
                    print('geting new dir')
                    insert_new_folder(folder_path, s)
                else:
                    print('geting new file')
                    make_file(path)
            except Exception:
                print('pass')
                s.send(b'pass')
                continue
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
            new_path = FILE_PATH + new_path
            if '.goutputstream' in path:
                delete_file(new_path)
                make_file(new_path)
            else:
                try:
                    os.replace(path,new_path)
                except Exception:
                    s.send(ACCEPT.encode())
                    continue
            

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
observer.schedule(event_handler, FILE_PATH, recursive = True)
observer.start()
initial_flag = 1

while(True):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((DEST_IP, DEST_PORT))

    #sends identification
    id = ID_NUM + ',' + local_id
    s.send(str(id).encode())
    #waits for server's acceptance
    print('stuck at id')
    s.recv(BUFFER_SIZE)

    #new id protocol
    if(ID_NUM == DEFAULT_ID): 
        #gets an id from server
        ID_NUM = s.recv(ID_LEN).decode()
        id = ID_NUM + ',' + local_id
        new_id_protocol(s)
        initial_flag = 0
        s.close()
        time.sleep(TIME_INTERVAL)
        continue

    elif initial_flag:
        initial_flag = 0
        #entering update mode
        UPDATE_FLAG = 2
        print('getting update list')
        SERVER_FILES = get_server_file_names()
        print('server updates are: ')
        print(SERVER_FILES)
        existing_id_protocol(s)
        print('my true updates are: ')
        print(UPDATES_LIST)
        #reset UPDATES_LIST
        SERVER_FILES = []
        #exiting update mode
        UPDATE_FLAG = 0

    if len(UPDATES_LIST) != 0:
        s.send(str(len(UPDATES_LIST)).encode())
        #waits for server's acceptance
        s.recv(BUFFER_SIZE)
        print('sending updates')
        send_updates_protocol()
        print('finished updating')

    update_size = s.recv(BUFFER_SIZE).decode()
    try:
        size = int(update_size)
    except:
        time.sleep(TIME_INTERVAL)
        continue
    print('update size: ' + update_size)
    if update_size != '0' and update_size != '':
        s.send(ACCEPT.encode())
        #entering update mode
        UPDATE_FLAG = 1
        INCOMING_UPDATES = get_update_list_protocol()
        get_updates_protocol(update_size)
        #reset UPDATES_LIST
        INCOMING_UPDATES = []
        #exiting update mode
        UPDATE_FLAG = 0

    time.sleep(TIME_INTERVAL)
    