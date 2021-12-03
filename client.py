import socket
import time
import sys
import os
import string

#finals
BUFFER_SIZE = 2300
END_MARK = '.'
DEFAULT_ID = '0'
ID_LEN = 128
FOLDER_MARK = '@'
FILE_MARK = 'f'

try:
    DEST_IP = sys.argv[1]
    DEST_PORT = int(sys.argv[2])
    #FILE_PATH = sys.argv[3]
    DIRECTORY_PATH = '/home/odin/Desktop/test file'
    #DIRECTORY_PATH = '/home/odin/Desktop/new'
    TIME_INTERVAL = sys.argv[4]
except:
    sys.exit()

try:
    ID_NUM = sys.argv[5]

except:
    ID_NUM = DEFAULT_ID

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
            s.send(END_MARK.encode())
            #waits for server acceptance
            s.recv(BUFFER_SIZE)
    s.send(END_MARK.encode())

def new_id_protocol(s):
    #gets files in folder
    folder_files = os.listdir(DIRECTORY_PATH)
    #file transer sequence
    get_folder_files(folder_files, s, DIRECTORY_PATH)

def existing_id_protocol(s):
    print(
        
    )

def run_client(ID_NUM):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #s.connect((DEST_IP, DEST_PORT))
    s.connect(('10.0.2.5', 12353))
    #sends identification
    s.send(ID_NUM.encode())

    #new id protocol
    if(ID_NUM == DEFAULT_ID):
        #gets an id from server
        ID_NUM = s.recv(ID_LEN).decode()
        new_id_protocol(s)
    s.close()

def main():
    run_client(ID_NUM)

if __name__ == '__main__':
    main()