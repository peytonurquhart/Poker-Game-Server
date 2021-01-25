# Poker Server
# naviagte.py
# routes client requests post authentication

import sys
import os
import util
import socket
import threading
import supernavigate as SN
import XML_ServerResponse as XH

l_tableip = socket.gethostbyname(socket.gethostname())
h_tableip = sys.argv[2]

MAXARGS = 5
_tableip = l_tableip
_tableportmin = 5051
_tableportmax = 5101

LOBBY_TIMEOUT = 300 # navigate timeout
INGAME_TIMEOUT = 60*60 # on-table timeout

GOODBYE = '!GOODBYE'
LIVEPORTSLIST = '!LIVEPORTSLIST'
LIVETABLEIP = '!LIVEIP'
STARTTABLE = '!TABLESTART'
CONNECT = '!JOINTABLE'
PIDS = '!PIDS'
PMSG = '!PMSG'

# super_nav - superuser command options
    # returns
        # false - no superuser command given
        # true - superuser command given and executed
def super_nav(conn, account, args):
    if account.is_super() == False:
        return False

    # superuser - start a new table server on port:args[1]
    if args[0] == STARTTABLE and args[1] and args[2] and args[3]:
        lp = list_live_table_ports_local()
        # ensure that the requested table is not already running
        if int(args[1]) not in lp:
            return SN.super_start_table(conn, args[1], _tableip, _tableportmin, _tableportmax, args[2], args[3])

    return False

# nav (navigate club server) main function
# Only responds to client for an invalid request, otherwise the helper functions respond
    # paramaters
        # conn = a client connection from a thread of main
        # account = a GlobalAccount object generated from authenticate()
        # msg = a client request retrieved in main
    # returns
        # False - for client disconnect
        # True - otherwise
def nav(conn, account, msg):
    # Ensure client is still authenticated before a command
    cl = util.conn_tracker.get_active_pids()
    if account.player_id not in cl:
        return util.respond(conn, XH.ServerResponse_StandardMessage("An error occured with your connection. Please exit and re-login\n"))

    args = util.parse_arguments(msg, MAXARGS)
    msg = args[0]

    # Give superusers super command options
    if account.is_super():
        sn = super_nav(conn, account, args)
        if sn == True:
            return True

    if msg == GOODBYE:
        return client_exit(conn)

    if msg == LIVEPORTSLIST:
        return list_live_table_ports(conn)

    if msg == LIVETABLEIP:
        return live_table_ip(conn)

    if msg == PMSG and args[1]:
        return pmsg(conn, account, args[1])

    if msg == CONNECT and args[1]:
        return connect_to_table(conn, args[1], account)

    if msg == PIDS:
        return get_active_pids(conn)


    # No valid request has been recognized, throw an error back to the client but dont exit.
    ce = XH.ServerResponse_ClientError()
    ce.add_ClientError(f'Invalid request: [{msg}] recieved in navigate()\n')
    return util.respond(conn, ce.to_string())

# respond to a request for an integer list of the player ids of actively logged in users
def get_active_pids(conn):
    l = util.conn_tracker.get_active_pids()
    cr = XH.ServerResponse_List('int')
    for x in l:
        cr.append(int(x))
    return util.respond(conn, cr.to_string())

# connect to table
# establish a virtual connection to a table server with the club acting as a middleman
# between all comminications. user->club->table and table->club->user
    # control returns to club->user and user->club iff:
        # the table responds with a ServerResponse_Exit command
def connect_to_table(conn, port, account):
    port = int(port)
    addr = (_tableip, port)
    table = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        table.connect(addr)     
    except:
        return util.respond(conn, XH.ServerResponse_StandardMessage('Could not connect.').to_string())

    # players may sit on a table and not interact for one a specified INGAME_TIMEOUT
    conn.settimeout(INGAME_TIMEOUT)
    util.respond(conn, XH.ServerResponse_StandardMessage(f'Joined table. [{addr}]').to_string())
    
    while True:
        # Catch client timeouts and force disconnects, say goodbye to table and exit
        try:
            from_player = util.recieve_unsafe(conn, None) # player->club
        except:
            cr = XH.ServerResponse_Account(account) # append account information
            cr.add_Command(GOODBYE)
            util.respond(table, cr.to_string())   # club->table
            return False            

        cr = XH.ServerResponse_Account(account) # append account information
        cr.add_Command(from_player)
        util.respond(table, cr.to_string())   # club->table

        from_table = util.recieve(table, None)  # table->club

        t_list = XH.parse_ServerResponse(from_table)
        if XH.tlist_contains_ExitCommand(t_list):
            conn.settimeout(LOBBY_TIMEOUT)
            return util.respond(conn, XH.ServerResponse_StandardMessage('Left table.').to_string())

        util.respond(conn, from_table)   # club->player

# list live table ports
    # test connection to each of the dedicated table servers.
    # the ip is the same as the main server, the port range is
    # defined as _tableportmin and _tableportmax
    # respond to the client at connection: conn with a StandardMessage
    # listing each tuple (ip, port) which is open, as its own </msg> in the
    # XML response.
def list_live_table_ports(conn):
    plist = XH.ServerResponse_List('port')
    for port in range(_tableportmin, _tableportmax + 1):
        addr = (_tableip, port)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # try to connect, send exit message to server to disconnect
        # after saying GOODBYE, we must read a reply per the protocal
        # after a connection has been extablished, we can add it to the live ports list
        try:
            client.connect(addr)
            util.respond(client, GOODBYE)
            util.recieve(client, addr)
            plist.append(str(port))
        except:
            pass

        client.close()

    return util.respond(conn, plist.to_string())

# list the working ip for the poker tables
    # right now they must all be on the same ip (running on same virtual machine)
def live_table_ip(conn):
    return util.respond(conn, XH.ServerResponse_StandardCommand(_tableip).to_string())

# client requested to exit, respond accordingly and return False (False for exit)
def client_exit(conn):
    util.respond(conn, XH.ServerResponse_Exit().to_string())
    return False   

# sends a message which appears in the servers log
def pmsg(conn, acc, msg):
    msg = f'<{acc.get_username()}>: {str(msg)}\n'
    util.s_print(msg)
    return util.respond(conn, XH.ServerResponse_StandardCommand('Ok').to_string())

# list live table ports
    # returns
        # int list of running table ports
def list_live_table_ports_local():
    plist = []
    for port in range(_tableportmin, _tableportmax + 1):
        addr = (_tableip, port)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # try to connect, send exit message to server to disconnect
        # after saying GOODBYE, we must read a reply per the protocal
        # after a connection has been extablished, we can add it to the live ports list
        try:
            client.connect(addr)
            util.respond(client, GOODBYE)
            util.recieve(client, addr)
            plist.append(int(port))
        except:
            pass

        client.close()

    return plist