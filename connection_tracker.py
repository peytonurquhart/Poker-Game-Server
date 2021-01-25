# Poker Server
# connection_tracker.py
# Keep track of the current state of client connections

import threading
import multiprocessing
from multiprocessing.queues import Queue

# Number of second before a request to access the ConnectionTracker in any way is cancelled
TIMEOUT = 5

# Track actively logged in clients in a list containing:
    # Player ID
    # Connection
    # Address
# Functions with __<>__ may be thread unsafe, only to be called in a locked state
class ConnectionTracker(Queue):
    def __init__(self, max_connections=-1):
        self.lock = threading.Lock()
        self.max = max_connections
        self.connections_list = []
        super().__init__(1, ctx=multiprocessing.get_context())

    # Lock object with timeout safety net
    def __lock__(self):
        return self.lock.acquire(blocking=True, timeout=TIMEOUT)

    # Attempt to lock object immediatly (for reading in a critical thread)
    def __lock_immediate__(self):
        return self.lock.acquire(blocking=False, timeout=-1)
    
    # Unlock object
    def __unlock__(self):
        try:
            self.lock.release()
        except:
            pass

    # Thread unsafe - only to be called in a locked state
    def __rm_entry_with_pid__(self, id):
        for c in self.connections_list:
            if c[0] == id:
                self.connections_list.remove(c)

    # Get the socket connection at pid if they are connected
    # Returns None for any failure
    def get_connection(self, pid):
        t = None
        if self.__lock__():
            for c in self.connections_list:
                if int(c[0]) == int(pid):
                    t = c[1]
                    break
            self.__unlock__()
        return t

    # Get list of active connections (pid, conn, addr)
    # Not for use in critical cases, this method is not prioritized
    def get_active(self):
        if self.__lock_immediate__():
            l = self.connections_list
            self.__unlock__()
            return l
        return [None]
       
    # Get list of active player ids
    # Not for use in critical cases, this method is not prioritized
    def get_active_pids(self):
        if self.__lock_immediate__():
            l = []
            for c in self.connections_list:
                l.append(c[0])
            self.__unlock__()
            return l
        return [None]

    # Add entry to active connections list (pid, conn, addr)
    def add(self, pid, conn, addr):
        if self.__lock__():
            c = (pid, conn, addr)
            self.connections_list.append(c)
            self.__unlock__()
            return True
        return False

    # Remove entry from active connections list (pid, conn, addr)
    def rm(self, pid, conn, addr):
        if self.__lock__():
            c = (pid, conn, addr)
            fid = c[0]
            self.__rm_entry_with_pid__(fid)
            self.__unlock__()
            return True
        return False