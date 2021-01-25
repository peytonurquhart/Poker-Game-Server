# Holdem server game thread heads up.
# hs_gamethread.py
# Contains the main game thread loop for heads up holdem
#   start()-|
#           ----main thread---  <listen()>
#           |                |
#           |                ----player thread
#           |                |
#           |                ----player thread
#           ----game thread

import sys
import socket
import threading
import time
import account
import connection_tracker as CT
import table as ST

TABLE_SIZE = int(sys.argv[4])
SMALL_BLIND = int(sys.argv[3])
TIME_BETWEEN_HANDS = 3 #seconds

# Keeps track of players actively sitting at the table
conn_tracker = CT.ConnectionTracker()
__state_table__ = ST.StateTable(TABLE_SIZE)
stc = ST.StateTable_Controller(__state_table__)

def start_table():
    while True:
        # Time between each hand in the game, then check for a live table
        time.sleep(TIME_BETWEEN_HANDS)

        # If the rotation can advance then it is time to start a new hand
        if stc.advance_rotation() == True:
            play_hand()
        else:
            print(f'sleeping: {TABLE_SIZE} handed, {SMALL_BLIND}/{SMALL_BLIND*2}')

def play_hand():
        ap = stc.state_table.players_list
        for x in ap:
            print(x.username)