import socket
import bcrypt
import xml.etree.ElementTree as ET
from xml.etree import ElementTree
import XML_ServerResponse as XH

HEADER = 128
FORMAT = 'utf-8'
GOODBYE_MSG = '!GOODBYE'
PORT = 5050

# local
SERVER = socket.gethostbyname(socket.gethostname())

# hosted
#SERVER = '173.255.248.17'

ADDR = (SERVER, PORT)

# send
def send(msg):
    message = msg.encode(FORMAT)
    msg_len = len(message)
    
    header = str(msg_len).encode(FORMAT)

    # pad with bytes
    header += b' ' * (HEADER - len(header))

    client.send(header)
    client.send(message)

# revieve
def recieve():

    msg_len = client.recv(HEADER).decode(FORMAT)

    if msg_len:

        msg_len = int(msg_len)

        msg = client.recv(msg_len).decode(FORMAT)

    return msg

# build etree from XML string recieved and print 
def parse_print(msg):

    parser = ET.XMLParser(encoding=FORMAT)

    root = ET.fromstring(msg[2:-1], parser=parser)

    for child in root:

        print(f'[{child.tag}]')
        s = str(child.text)
        s += ' '
        i = 0
        while i < len(s) - 1:
            if s[i] == '\\' and s[i + 1] == 'n':
                i += 2
                print("")
            else:
                print(s[i], end="")
                i += 1
        print("")
            
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

while True:
    message = input("<>: ")
    send(message)
    resp = recieve()

    t_list = XH.parse_ServerResponse(resp)
    if t_list:
        if t_list[0][0] == 'command' and t_list[0][1] == 'Exit':
            exit()

    parse_print(resp)


