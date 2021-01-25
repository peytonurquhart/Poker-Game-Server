# Poker Server
# supernaviagte.py
# handles superuser administrative requests

import sys
import os
import util
import socket
import threading
import XML_ServerResponse as XH

# super start table - UNSAFE
# creates a new thread to run a server (ip, port) on that thread.
# responds to the superuser regarding the results
    # returns
        # true - this function should complete and wait for more requests, not close the client
    # unsafe
        # can start an instance of a table (port) which is already running, this must be handled
        # ahead of time
def super_start_table(conn, port, ip, minport, maxport, smallblind, num_handed):
    sh_starttable = (f'sh mkt {str(port)} {str(ip)} {str(smallblind)} {str(num_handed)}',)

    if port and ip:
        port = int(port)
        ip = str(ip)
        if (port >= minport) and (port <= maxport):
            t_thread = threading.Thread(target=sh_run_table, args=sh_starttable)
            t_thread.start()
            return util.respond(conn, XH.ServerResponse_StandardMessage(f'Table started on [{ip}, {port}]\n').to_string())

    e = XH.ServerResponse_ClientError()
    e.add_ClientError(f'Failed to start table. super_start_table() args={sh_starttable}\n')
    return util.respond(conn, e.to_string())

# async function called by a dedicated thread, execute shell script to start new table server
def sh_run_table(sh_run):
    # thread waits on this function to finish, then exits
    os.system(sh_run)
    exit(1)
