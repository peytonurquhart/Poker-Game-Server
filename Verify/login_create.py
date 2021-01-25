# Poker Server
# login_create.py
# Connect to SQLite database in order to login-to, or create an account in the database
# provide ServerResponse messages to back to server_version.py per each request to authenticate()

import socket
import sqlite3
import bcrypt
import account
import util
import XML_ServerResponse as XH
import password_verify as PV
import super_user as SU

FORMAT = 'utf-8'
DATABASE_NAME = 'user_accounts.db'
ACCOUNT_IDENTIFIER = 'ClubAccounts'
PLAYER_ID_IDENTIFIER = 'PlayerIDs'

# Client requests
LOGIN = '!LOGIN'
CREATE = '!CREATE'
STAT = '!STAT'
GOODBYE = '!GOODBYE'
SUPER = '!SUPER'

# Sets a players active to 0 in the database, meaning they can now login elsewhere
def logout(player_id):
    sql_conn = sqlite3.connect(DATABASE_NAME)
    c = sql_conn.cursor()

    id = (f"{player_id}",)            
    c.execute(f'''UPDATE {ACCOUNT_IDENTIFIER} SET active = '0' WHERE player_id = ?''', id)
    sql_conn.commit()
    c.close()

# Increment running unique playerID count by 1
def incr_playerIDs(sql_conn):
    c = sql_conn.cursor()   
    c.execute(f"SELECT * FROM {PLAYER_ID_IDENTIFIER}")
    idt = c.fetchone()

    # if no player has registered yet
    if idt == None:
        c.execute(f"INSERT INTO {PLAYER_ID_IDENTIFIER} VALUES ('100')")
        return

    cid = idt[0]
    cid = int(cid)
    cid += 1

    # delete the previous entry
    c.execute(f"DELETE FROM {PLAYER_ID_IDENTIFIER}")

    t = (f'{str(cid)}',)
    c.execute(f"INSERT INTO {PLAYER_ID_IDENTIFIER} VALUES (?)", t)

# Create new unique player ID, update the database
def create_playerID(sql_conn):
    incr_playerIDs(sql_conn)
    c = sql_conn.cursor()
    c.execute(f"SELECT * FROM {PLAYER_ID_IDENTIFIER}")
    idt = c.fetchone()
    return idt[0]

# Stat an account on server, should never actually be used but for testing
def get_account_stat(db_row):
    s = "--------------- STAT ---------------\n"
    s += f"Player ID: {db_row[0]}\n"
    s += f"Username: {db_row[1]}\n"
    s += f"Password: {db_row[2]}\n"
    s += f"Balance: {db_row[3]}\n"
    s += "------------------------------------\n"

    return s

# Get account into an object to return to server (without the password)
def init_account(db_row):
    return account.ClubAccount(int(db_row[0]), str(db_row[1]), float(db_row[3]))

# Check to ensure connection to databases is okay, otherwise create them
def init_database(sql_conn):
    c = sql_conn.cursor()

    c.execute(f'''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{ACCOUNT_IDENTIFIER}' ''')
    tab = c.fetchone()
    if tab[0] == 0:
        c.execute(f'''CREATE TABLE {ACCOUNT_IDENTIFIER} (player_id integer, username text, password text, balance real, active integer)''')
        sql_conn.commit()
        util.s_print(f"<DATABASE CREATED>: {ACCOUNT_IDENTIFIER}")

    c.execute(f'''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{PLAYER_ID_IDENTIFIER}' ''')
    tab = c.fetchone()
    if tab[0] == 0:
        c.execute(f'''CREATE TABLE {PLAYER_ID_IDENTIFIER} (current_id integer)''')
        sql_conn.commit()
        util.s_print(f"<DATABASE CREATED>: {PLAYER_ID_IDENTIFIER}")

# Set each account in the database to inactive
# To be done for each server restart (just in case)
def clear_activity():
    sql_conn = sqlite3.connect(DATABASE_NAME)
    c = sql_conn.cursor()
    c.execute(f'''UPDATE {ACCOUNT_IDENTIFIER} SET active = '0' WHERE active = 1''')
    sql_conn.commit()
    c.close()

# User authenticate login information
    # returns
        # (ServerResponse_StandardMessage, ClubAccount) - successful login
        # (ServerResponse_StandardMessage, None) - unsuccessful login
def authenticate_login(sql_conn, addr, args):

    c = sql_conn.cursor()
    t = (f"{args[1]}",)
    c.execute(f"SELECT * FROM {ACCOUNT_IDENTIFIER} WHERE username=?", t)             
    act = c.fetchone()

    # Username Invalid
    if act == None:
        util.s_print(f"<FAILED LOGIN>: {addr} username does not exist")
        c.close()
        return(XH.ServerResponse_StandardMessage('That username does not exist.\n').to_string(), None)

    # Already logged in
    if int(act[4]) == 1:
        util.s_print(f"<FAILED LOGIN>: {addr} already logged in")
        c.close()
        return (XH.ServerResponse_StandardMessage('You are already logged in somewhere.\n').to_string(), None)

    # Password Invalid
    if bcrypt.checkpw(args[2].encode(FORMAT), act[2].encode(FORMAT)) == False:
        util.s_print(f"<FAILED LOGIN>: {addr} incorrect password")
        c.close()
        return (XH.ServerResponse_StandardMessage('Invalid password.\n').to_string(), None)

    # Login Success
    util.s_print(f"<LOGIN SUCCESS>: {addr}")
    id = (f"{act[0]}",)            
    c.execute(f'''UPDATE {ACCOUNT_IDENTIFIER} SET active = '1' WHERE player_id = ?''', id)
    sql_conn.commit()
    c.close()
    return (XH.ServerResponse_StandardMessage(f'Welcome {args[1]}!\n').to_string(), init_account(act))

# Superuser authenticate login information
    # arguments
        # [1] username
        # [2] account password
        # [3] superuser password
        # [4] superuser PIN
    # returns
        # (ServerResponse_StandardMessage, ClubAccount with superuser permissions) - all passwords match
        # (ServerResponse_StandardMessage, None) - unsuccessful
def authenticate_super(sql_conn, addr, args):
    c = authenticate_login(sql_conn, addr, args)
    account = c[1]
    msg = c[0]

    if account == None:    
        return c
    else:
        status = SU.check_super(args[3], args[4])

    if status == True:
        account.make_super()
        util.s_print(f'<SUPERUSER ACCESS GRANTED>: for "{account.username}"')
        return (XH.ServerResponse_StandardMessage(f'Login successful, superuser access granted.\n').to_string(), account)
    else:
        logout(account.player_id)
        util.s_print(f'<SUPERUSER ACCESS DENIED>: for "{account.username}"')
        return (XH.ServerResponse_StandardMessage(f'Failed to login with superuser access.\n').to_string(), None)

# User authenticate create account information
    # returns
        # (ServerResponse_StandardMessage, None) - information on account creation, never logs in
def authenticate_create_account(sql_conn, addr, args):

    c = sql_conn.cursor()
    t = (f"{args[1]}",)
    c.execute(f"SELECT * FROM {ACCOUNT_IDENTIFIER} WHERE username=?", t)            
    act = c.fetchone()

    # Username Available
    if act == None:

        # Check if the password is acceptable
        if PV.is_acceptable_password(args[2]) == False:
            util.s_print(f"<FAILED REGISTRATION>: {addr} password unacceptable")
            c.close()

            r = XH.ServerResponse_StandardMessage('Invalid password.\n')
            r.add_StandardMessage(PV.get_password_requirements_msg())
            return (r.to_string(), None)

        # Encrypt password, push to DB, commit changes, return ServerResponse. (Account not loaded to RAM)
        idt = create_playerID(sql_conn)
        hp = bcrypt.hashpw(args[2].encode(FORMAT), bcrypt.gensalt())
        args[2] = hp.decode(FORMAT)
        t = (f"{idt}", f"{args[1]}", f"{args[2]}",)
        c.execute(f"INSERT INTO {ACCOUNT_IDENTIFIER} VALUES (?, ?, ?, '0', '0')", t)
        util.s_print(f"<REGISTRATION SUCCESS>: {addr} username={args[1]} player_id={idt}")
        sql_conn.commit()
        c.close()
        return (XH.ServerResponse_StandardMessage(f'Account creation for "{args[1]}" successful.\n').to_string(), None)

    else:
        # Username NOT Available
        util.s_print(f"<FAILED REGISTRATION>: {addr} username was taken")
        c.close()
        return (XH.ServerResponse_StandardMessage('That username is already taken.\n').to_string(), None)

# User authenticate login information for account stat
    # returns
        # (ServerResponse_StandardMessage, None) - only retreieves information, never logs in
def authenticate_stat(sql_conn, addr, args):
    c = sql_conn.cursor()
    t = (f"{args[1]}",)
    c.execute(f"SELECT * FROM {ACCOUNT_IDENTIFIER} WHERE username=?", t)       
    act = c.fetchone()

    # Invalid username
    if act == None:
        util.s_print(f"<STAT>: {addr} username does not exist")
        c.close()
        return (XH.ServerResponse_StandardMessage('That username does not exist.\n').to_string(), None)

    # Invalid password
    if bcrypt.checkpw(args[2].encode(FORMAT), act[2].encode(FORMAT)) == False:
        util.s_print(f"<STAT>: {addr} incorrect password")
        c.close()
        return (XH.ServerResponse_StandardMessage('Invalid password.\n').to_string(), None)
 
    # Stat Successful
    c.close()
    return(XH.ServerResponse_StandardMessage(f'{get_account_stat(act)}').to_string(), None)

# Authenticate a connection at addr
    # returns
        # (ServerResponse_StandardMessage, ClubAccount) - for client login successful     
        # (ServerResponse_StandardMessage, None) - for a number of execution paths other than login success
        # (ServerResponse_ClientError, None) - for a non-recognized request from the client
        # (None, None) - for client Exit
def authenticate(conn, addr):

    # Connect to DB, ensure set-up, create cursor
    sql_conn = sqlite3.connect(DATABASE_NAME)
    init_database(sql_conn)
    c = sql_conn.cursor()

    msg = util.recieve(conn, addr)
    args = util.parse_arguments(msg, 5)

    # authentication with 3 arguments
    if args[0] and args[1] and args[2]:
        # Logging In
        if args[0] == LOGIN:
            return authenticate_login(sql_conn, addr, args)
        # Create new account
        if args[0] == CREATE:
            return authenticate_create_account(sql_conn, addr, args)
        # Stat account
        if args[0] == STAT:
            return authenticate_stat(sql_conn, addr, args)
        # Login as superuser
        if args[0] == SUPER and args[3] and args[4]:
            return authenticate_super(sql_conn, addr, args)

    c.close()

    # Exit
    if args[0] == GOODBYE:
        return (None, None)
            
    # Invalid request
    ce = XH.ServerResponse_ClientError()
    ce.add_ClientError(f'Invalid request=[{args[0]},{args[1]},{args[2]}] found in authenticate()\n')
    return (ce.to_string(), None) 