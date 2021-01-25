# Poker Server
# super_user.py
# Superuser authentication

import sys
import bcrypt

FORMAT = 'utf-8'
SUPER_PASSWORD = '$2b$12$Wuhol985p8RcevVI1OerVOcWqwVCf1UWSuzUOpBBCLezYLQwZGOfC'
SUPER_PIN = '$2b$12$Se/iQ4upkeQsynecY8rWWOorj3PVCEp0LwPdwne0oQDV3zIgIs20i'

# Authenticate a superuser login attempt against the static hashes
def check_super(password, pin):
    if bcrypt.checkpw(password.encode(FORMAT), SUPER_PASSWORD.encode(FORMAT)) == True:
        if bcrypt.checkpw(pin.encode(FORMAT), SUPER_PIN.encode(FORMAT)) == True:
            return True
    return False
