# Poker Server
# server_version.py
# Entry point for the club server, its purpose is to register users, authenticate users,
# retreive account statistics, generally connect to the club accounts database, and route 
# traffic onward.

import sys
import socket
import threading
import time
import login_create
import XML_ServerResponse as XH
import navigate as NV
import account
import util
import time

l_ip = socket.gethostbyname(socket.gethostname())
h_ip = ''

IP = l_ip
PORT = int(sys.argv[1])
ADDR = (IP, PORT)

# 5 minute timeout on authentication server
TIMEOUT = 300

# Allow client to login, otherwise they must create an account and then login, or exit
def authenticate_client(conn, addr):
    
    # Login or create account
    while True:
        auth = login_create.authenticate(conn, addr)

        # Client exit
        if auth[0] == None:
            return None

        # Login success
        if auth[1] != None:
            util.s_print(f"[{PORT}]<CLIENT AUTHENTICATED>: {addr}")
            util.respond(conn, auth[0])
            return auth[1]

        # Respond to client with message, if they are gone return None for disconnect
        if util.respond(conn, auth[0]) == False:
            return None

# Use in dedicated thread, given a connection and an address handle all client i/o
def handle_client(conn, addr):

    util.s_print(f"[{PORT}]<NEW CONNECTION>: {addr}")
    acc = authenticate_client(conn, addr)

    # Client exit
    if acc == None:
        util.respond(conn, XH.ServerResponse_Exit().to_string())
        util.s_print(f"[{PORT}]<CLIENT DISCONNECTED>: {addr}")
        conn.close()
        return

    # Attempt to track the connection, disconnect if dangling thread error
    if util.conn_tracker.add(acc.get_player_id(), conn, addr) == False:
            util.client_logout(acc.get_player_id(), conn, addr)
            return
    
    # When a client is logged in successfully, get messages and keep sending them to navigate()
    # When nav returns false->log-client-out->disconnect->close the thread
    while True:
        msg = util.recieve(conn, addr)  #if the client exits the program unsafely the message is set to GOODBYE and a logout and exit will result
        status = NV.nav(conn, acc, msg)

        # ALL execution paths post-login come HERE. If there are dangling threads its because they didnt end HERE
        if status == False:
            util.client_logout(acc.get_player_id(), conn, addr)
            return

# Start listening and accepting client connections
def start():
    login_create.clear_activity()
    server.listen()
    util.s_print(f"[{PORT}]<LISTENING ON>: {ADDR}")

    while True:
        conn, addr = server.accept()
        # set each socket timeout for navigation server
        conn.settimeout(TIMEOUT)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        util.s_print(f"[{PORT}]<ACTIVE THREADS>: {threading.activeCount() - 1}")
        util.s_print(f"<ACTIVE PLAYERS>: {util.conn_tracker.get_active_pids()}")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    server.bind(ADDR)
except:
    print("Error: Club Server: Port in use")
    exit(1)

util.s_print(f"[{PORT}]<STARTING SERVER>:")
start()

#NOTE deuces poker library <---

#NOTE authentication server is in maintenence phase
# the server can do all nescessary tasks
    # authenticate players
    # login / logout
    # establish virtual connections to game servers
    # timeout users and virtually timeout users from game servers
    # handle client crashes and force-disconnects
