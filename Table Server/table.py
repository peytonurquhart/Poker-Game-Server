# StateTable class, StateTable_Controller class
# table.py
# Class representing a poker table position-wise
# Describes only the positional state of a poker table

#           Positions
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#           0 - utg
#           1 - utg + 1
#           2 - utg + 2
#             ...+...
#           (last - 2) - button
#           (last - 1) - small blind
#           last - big blind
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import player
import time
import threading
import multiprocessing

TIMEOUT = 5

# Controller for the state table, called as the game advances
class StateTable_Controller:
    def __init__(self, state_table_object):
        self.state_table = state_table_object
        self.b_seatnum = 0
        self.l = threading.Lock()

    # Lock object with timeout safety net
    def lock(self):
        return self.l.acquire(blocking=True, timeout=TIMEOUT)

    # Unlock object
    def unlock(self):
        try:
            self.l.release()
        except:
            pass

    # Advances the table rotation ensuring that the button is on an active player
    # returns
        # true for successful arrangement
        # false for could not start positional round
    def advance_rotation(self):
        i = 0
        while self.state_table.assign_positions(self.b_seatnum) == False:
            self.b_seatnum = self.state_table.__next_seat__(self.b_seatnum)
            if i >= self.state_table.seats + 1:
                return False
            i += 1
        self.b_seatnum = self.state_table.__next_seat__(self.b_seatnum)
        return True

# Describes the positional state of a table
class StateTable:
    def __init__(self, seats=2):
        self.min_players = 2
        self.seats = seats
        self.players_list = []
        self.seats_list = [None] * seats

        self.button_player = None

        self.button_seat_number = 0
        self.sb_seat_number = 0
        self.bb_seat_number = 0

    # get the number of players at the table marked as active
    def __get_num_active__(self):
        a = 0
        for p in self.players_list:
            if p.is_Active():
                a += 1
        return a

    # get a list of all players at the table marked as active
    def __get_active_players_list__(self):
        l = []
        for p in self.players_list:
            if p.is_Active():
                l.append(p)
        return l

    # gets the seat positionally after seat_num
    def __next_seat__(self, seat_num):
        if seat_num == self.seats - 1:
            return 0
        else:
            return seat_num + 1

    # gets the next seat with an active player in it
    def __next_active_seat__(self, seat_num):
        n = self.__next_seat__(seat_num)
        p = self.seats_list[n]
        while p == None or p.is_Active() == False:
            n = self.__next_seat__(n)
            p = self.seats_list[n]
        return n

    # Returns the number of players on the table
    def players_count(self):
        return len(self.players_list)

    # Returns true if the table is full, else false
    def is_Full(self):
        if self.players_count() == self.seats:
            return True
        return False

    # get a list of open seats on the table
    # returns
        # list(open seats)
        # None for full table
    def get_open_seats(self):
        n = range(0, self.seats)
        o = []
        for x in n:
            if self.seats_list(x) == None:
                o.append(x)
        if len(o) == 0:
            return None
        return o

    # try to add a player to the table at the requested seat number
    def add_player(self, player, seat_number):
        if player in self.players_list:
            return False
        if seat_number < 0 or seat_number > (self.seats - 1):
            return False
        if self.seats_list[seat_number] != None:
            return False

        self.seats_list[seat_number] = player
        player.set_seat_num(seat_number)
        self.players_list.append(player)
        return True

    # remove a player from the table and free the seat up
    def remove_player(self, player):
        if player in self.players_list:
            self.players_list.remove(player)
            self.seats_list[player.seat_number] = None
            return True
        return False

    def remove_player_at_id(self, pid):
        a = None
        for x in self.players_list:
            if x.player_id == pid:
                a = x
        if a != None:
            self.remove_player(a)
        return a

    # If there is a player at seat_num, they are made unactive
    def sit_out(self, seat_num):
        p = self.seats_list[seat_num]
        if p == None:
            return False
        else:
            p.make_unactive()
            return True

    # assign positions to each active seat at the table given the small blinds seat number
    # assigns each player object a position
    def assign_positions(self, button_seat_number):

        # Only 1 player on table
        if self.__get_num_active__() < 2:
            return False

        # No player on requested button seat number
        if self.seats_list[button_seat_number] == None:
            return False

        # Player on requested button seat number isn't active
        p = self.seats_list[button_seat_number]
        if p.is_Active() == False:
            return False

        # Give all unactive players a position of -1
        for p in self.players_list:
            if p.is_Active() == False:
                p.position = -1

        self.button_player = self.seats_list[button_seat_number]
        self.button_seat_number = button_seat_number

        # Check for the special heads up case
        if self.__get_num_active__() == 2:
            self.seats_list[button_seat_number].position = 0
            self.sb_seat_number = button_seat_number
            n = self.__next_active_seat__(button_seat_number)
            self.seats_list[n].position = 1
            self.bb_seat_number = n
            return True

        # Set sb, bb, and finally get UTG seat number to start assigning posistions from 0
        fta = self.__next_active_seat__(button_seat_number)
        self.sb_seat_number = fta
        fta = self.__next_active_seat__(fta)
        self.bb_seat_number = fta
        fta = self.__next_active_seat__(fta)

        # Assign positions to active players
        i = 0
        while i < self.__get_num_active__():
            p = self.seats_list[fta]
            p.position = i
            fta = self.__next_active_seat__(fta)
            i += 1

        return True
