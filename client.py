import socket
import time
import sys
import os
import string
import random
import watchdog

#finals
BUFFER_SIZE = 2300
END_MARK = '.'
DEFAULT_ID = '0'
LOCAL_ID_LEN = 36
ID_LEN = 128
FOLDER_MARK = '@'
FILE_MARK = 'f'
ACCEPT = 'ok'

try:
    DEST_IP = sys.argv[1]
    DEST_PORT = int(sys.argv[2])
    #FILE_PATH = sys.argv[3]
    #DIRECTORY_PATH = '/home/odin/Desktop/test file'
    DIRECTORY_PATH = '/home/odin/Desktop/new1'
    TIME_INTERVAL = sys.argv[4]
    
except:
    print()

try:
    ID_NUM = sys.argv[5]

except:
    ID_NUM = DEFAULT_ID
DEST_PORT = 12550
DIRECTORY_PATH = '/home/odin/Desktop/new1'


class Handler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self):
        watchdog.events.PatternMatchingEventHandler(self, Pattern=['*.*'], ignore_patterns = None,
         ignore_directories = False, cade_sensitive = True)
    def on_created(self, event):
        print('File was created at {event.src_path}')
    def on_deleted(self, event):
        print('File was deleted at {event.src_path}')


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
            #waits for server acceptance
            s.recv(BUFFER_SIZE)
    
        else:
            s.send(str(FILE_MARK + file_name).encode())
            #waits for server acceptance
            s.recv(BUFFER_SIZE)
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
    s.send(END_MARK.encode())

def new_id_protocol(s):
    #gets files in folder
    folder_files = os.listdir(DIRECTORY_PATH)
    #file transer sequence
    get_folder_files(folder_files, s, DIRECTORY_PATH)

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


def existing_id_protocol(s):
    folder_path = DIRECTORY_PATH + '/'
    insert_new_folder(folder_path, s)
    
def local_id_generator(size = LOCAL_ID_LEN, chars=string.ascii_uppercase + string.digits):
    new_id = ''.join(random.choice(chars) for _ in range(size))
    return new_id


#main

local_id = local_id_generator()   
#event_handler = Handler()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.connect((DEST_IP, DEST_PORT))
s.connect(('10.0.2.5', DEST_PORT))
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
   
s.close()
while(True):

    #time.sleep(TIME_INTERVAL)
    time.sleep(3)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.connect((DEST_IP, DEST_PORT))
    s.connect(('10.0.2.5', DEST_PORT))
    s.send(str(id).encode())
    #waits for server's acceptance
    s.recv(BUFFER_SIZE)

    #imitates a regular state
    s.send('0'.encode())

    #imitates a change state
    #s.send('1'.encode())

    new_data = s.recv(6).decode()
    if new_data == 'update':
        print('update')
    s.close()