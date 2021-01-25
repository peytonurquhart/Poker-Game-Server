# Holdem Table Server
# holdem_server.py
# A server to connect to which plays one table of texas holdem
# This server should only be connected to by the Club Server

import socket
import sys
import threading
import util
import account
import player
import hs_gamethread as game
import XML_ServerResponse as XH

GOODBYE = '!GOODBYE'
SIT = '!SIT'

IP = str(sys.argv[2])
PORT = int(sys.argv[1])
ADDR = (IP, PORT)

# Parses a message to the server
# returns
    # (account, message) iff the client has established a virtual connection
    # (None, message) if the client has connected in some other fashion (pinging table)
def account_from_ServerResponse(xml_response):
    if XH.is_ServerResponse(xml_response):
        t_list = XH.parse_ServerResponse(xml_response)
        for x in t_list:
            if x[0] == 'username':
                username = str(x[1])
            if x[0] == 'ID':
                pid = int(x[1])
            if x[0] == 'balance':
                balance = x[1]
            if x[0] == 'command':
                msg = x[1]

        acc = account.ClubAccount(pid, username, balance)
        return acc, msg
    return None, xml_response

# Disconnect client with no virtual connection (no account)
def disconnect_unauth_client(conn):
    util.respond(conn, XH.ServerResponse_Exit().to_string())
    util.s_print(f"[table {PORT}]: disconnected unauthorized client")
    conn.close()
    return

# Disconnect client with virtual connection (account prefix)
def disconnect_auth_client(conn, username, id):
    util.respond(conn, XH.ServerResponse_Exit().to_string())
    util.s_print(f"[table {PORT}]: {username}-{id} left the table")
    conn.close()
    return

# Attempt to take seat at the table at a certain seat
def try_sit(conn, addr, acc, seat_num):
    p = player.Player(acc.username, acc.player_id)
    p.make_unactive()
    if game.stc.lock():
        if game.stc.state_table.is_Full():
            game.stc.unlock()
            util.respond(conn, XH.ServerResponse_StandardMessage("This table is now full.\n").to_string())
            return False
        if game.stc.state_table.add_player(p, seat_num) == True:
            game.stc.unlock()
            game.conn_tracker.add(acc.get_player_id(), conn, addr)
            util.respond(conn, XH.ServerResponse_StandardMessage(f'Success, you sat at seat {seat_num}.\n').to_string())
            return True

    game.stc.unlock()
    util.respond(conn, XH.ServerResponse_StandardMessage(f"Failed, please try again.\n").to_string())
    return False    

# Return once client leaves the table
# Once this function returns the client is redirected back to the lobby
# NOTE the client will request tablestate messages from here
def play_game(conn, addr, acc):
    while True:
        msg = util.recieve(conn, addr)
        acc, msg = account_from_ServerResponse(msg)

        # Exit and save
        if msg == GOODBYE or acc == None:
            return

        util.respond(conn, XH.ServerResponse_StandardMessage("at the table.").to_string())       

# Use in dedicated thread, given a connection and an address handle all client i/o
def handle_client(conn, addr):

    util.s_print(f"[table {PORT}]: <new connection> {addr}")   
    acc = None
    
    while True:
        msg = util.recieve(conn, addr)
        acc, msg = account_from_ServerResponse(msg)

        args = util.parse_arguments(msg, 5)
        msg = args[0]

        # If the client has no virtual connection, all they may do is ping the server
        if acc == None:
            disconnect_unauth_client(conn)
            return

        # Client with virtual connection request disconnect
        if msg == GOODBYE:
            game.conn_tracker.rm(acc.get_player_id(), conn, addr)
            disconnect_auth_client(conn, acc.get_username(), acc.get_player_id())
            return

        # Take seat at table, once the player leaves the table they are logged and disconnected
        if msg == SIT and args[1]:
            if try_sit(conn, addr, acc, int(args[1])):
                play_game(conn, addr, acc) #await til exit...
                game.conn_tracker.rm(acc.get_player_id(), conn, addr)
                game.stc.lock()
                game.stc.state_table.remove_player_at_id(acc.get_player_id())
                game.stc.unlock()
                disconnect_auth_client(conn, acc.get_username(), acc.get_player_id())
                return
        else:
            ce = XH.ServerResponse_ClientError()
            ce.add_ClientError(f"Unacceptable input <{args}> found in tableserver.handle_client\n")
            util.respond(conn, ce.to_string())

# Start listening and accepting client connections
def start():
    server.listen()
    util.s_print(f"[table {PORT}]<listening on>: {ADDR}")

    # Main game loop in this thread
    gt = threading.Thread(target=game.start_table)
    gt.start()

    while True:
        conn, addr = server.accept()        
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        util.s_print(f"[table {PORT}]<active connections>: {threading.activeCount() - 1}")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server.bind(ADDR)
except:
    print("Error: Holdem Server: Port in use")
    exit(1)
util.s_print(f"[table {PORT}]<starting table>:")
start()
exit(1)