# Poker Server
# account.py
# In-memory structure for club accounts

import sys

SUPER_PERMISSIONS = 10000
STANDARD_PERMISSIONS = 100

# User Account class for general login
class ClubAccount:

    def __init__(self, player_id, username, balance):
        self.player_id = player_id
        self.username = username
        self.balance = balance
        self.permissions = STANDARD_PERMISSIONS

    def get_username(self):
        return self.username

    def get_player_id(self):
        return self.player_id

    def get_balance(self):
        return self.balance

    def get_permissions(self):
        return self.permissions

    def add_balance(self, amount):
        self.balance += amount

    def subtract_balance(self, amount):
        self.balance -= amount

    # Gives this user maximum permissions, never to be done except at login
    def make_super(self):
        self.permissions = SUPER_PERMISSIONS

    # Returns true if this user is a superuser
    def is_super(self):
        if self.permissions >= SUPER_PERMISSIONS:
            return True
        return False