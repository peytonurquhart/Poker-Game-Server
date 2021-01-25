# Poker Server
# util.py
# Utility functions for server-only operations

import socket
import navigate as NV
import connection_tracker as CT
import login_create

HEADER = 128
FORMAT = 'utf-8'
GOODBYE = '!GOODBYE'

# Tracks actively logged in users, also to be accessed by main. Thread safe.
conn_tracker = CT.ConnectionTracker()

# Print data to terminal: msg=prefix:data
def s_print(msg):
    toks = msg.split(':', 2)
    print(toks[0], end=':')
    print(' ' * (30 - len(toks[0])), end='')
    print(toks[1])

# Recieve a valid message from the client
# returns
    # client message - for success
    # GOODBYE message - for failure
def recieve(conn, addr):   
    while True:
        try:
            msg_len = conn.recv(HEADER).decode(FORMAT)
        except:
           return GOODBYE

        if msg_len:
            msg_len = int(msg_len)
            msg = conn.recv(msg_len).decode(FORMAT)
            return msg
        else:
            return GOODBYE

# A version of recieve that will throw an Exeption
# when a client disconnects or times out, as opposed to the exit message
def recieve_unsafe(conn, addr):   
    while True:
        try:
            msg_len = conn.recv(HEADER).decode(FORMAT)
        except:
           raise Exception('Client timed out')

        if msg_len:
            msg_len = int(msg_len)
            msg = conn.recv(msg_len).decode(FORMAT)
            return msg
        else:
            raise Exception('Client force disconnect')

# Respond to client given conn and a message
# returns
    # true - success
    # false - assumed client disconnect
def respond(conn, msg):
    message = msg.encode(FORMAT)
    msg_len = len(message) 
    header = str(msg_len).encode(FORMAT)
    header += b' ' * (HEADER - len(header))
    try:
        conn.send(header)
        conn.send(message)
        return True
    except:
        s_print("<Warning in respond()>: Bad Disconnect - Client crash?")
        return False

# Parse a message from the client into up to max arguments delimited by ','
def parse_arguments(client_message, max):
    args = [None] * max
    spl = client_message.split(',')
    i = 0
    for x in spl:
        if i > max - 1:
            break
        args[i] = x
        i += 1
    return args

# To be called whenever an authenticated client disconnects
def client_logout(player_id, conn, addr):
    conn_tracker.rm(player_id, conn, addr)
    login_create.logout(player_id)
    s_print(f"<PLAYER {player_id} LOGOUT>: {addr}")
    conn.close()
