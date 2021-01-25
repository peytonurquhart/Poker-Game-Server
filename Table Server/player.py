# Player class
# player.py
# Class representing a player at a poker table

class Player:
    def __init__(self, username, pid):
        self.username = username
        self.player_id = pid
        self.seat_number = -1
        self.position = -1
        self.active = False

    def set_seat_num(self, n):
        self.seat_number = n

    def make_active(self):
        self.active = True

    def make_unactive(self):
        self.active = False

    def is_Active(self):
        return self.active