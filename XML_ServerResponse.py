# Poker Server
# XML_ServerResponse.py
# Construct server->client response messages in an XML format
    # Development Notes:
    # Derrived classes may be added as needed,
    # however, custom ServerResponses could also be used.

import sys
import xml.etree.ElementTree as ET
from xml.etree import ElementTree
import account

MSG = 'msg'
COMMAND = 'command'
CLIENT_ERROR = 'client_error'
EXIT = 'Exit'

FORMAT = 'utf-8'
METHOD = 'xml'

# return a list of tuples (tag, text) from an XML_ServerResponse
def parse_ServerResponse(xml_msg):
    parser = ET.XMLParser(encoding=FORMAT)
    root = ET.fromstring(xml_msg[2:-1], parser=parser)
    t_list = []

    for child in root:
        t_list.append((str(child.tag), str(child.text)))

    return t_list

# attempts to parse an xml string
# returns the origional string if bad format
def is_ServerResponse(msg):
    try:
        parse_ServerResponse(msg)
        return True
    except:
        return False

# accepts a list of tuples from a parse_ServerResponse
    # returns
        # true if one of them is an exit command
        # false - otherwise
def tlist_contains_ExitCommand(t_list):
    for x in t_list:
        if x[0] == 'command' and x[1] == 'Exit':
            return True
    return False      

# XML ServerResponse base class
    # Any response server->client must be in the form ServerResponse.to_string()
class ServerResponse:
    def __init__(self):
        self.root = ET.Element('ServerResponse')

    def root_child(self, name, data):
        name = ET.SubElement(self.root, name)
        name.text = str(data)

    def to_string(self):
        return str(ElementTree.tostring(self.root, encoding=FORMAT, method=METHOD))

# XML ServerResponse StandardMessage derrived class
    # Appropriate for when the server must display some information to the client
    # Not appropriate for when the client must implicitly act on such information
class ServerResponse_StandardMessage(ServerResponse):
    def __init__(self, message):
        ServerResponse.__init__(self)
        ServerResponse.root_child(self, MSG, message)

    def add_StandardMessage(self, message):
        ServerResponse.root_child(self, MSG, message)

# XML ServerResponse StandardCommand derrived class
    # Appropriate for when the server must send a/some command(s) to the client
    # Not approprate for when the client must be displayed a message
class ServerResponse_StandardCommand(ServerResponse):
    def __init__(self, command):
        ServerResponse.__init__(self)
        ServerResponse.root_child(self, COMMAND, command)

    def add_StandardCommand(self, command):
        ServerResponse.root_child(self, COMMAND, command)

#XML ServerResponse List derrived class
    # Appropriate for holding a simple list of objects
class ServerResponse_List(ServerResponse):
    def __init__(self, _type):
        ServerResponse.__init__(self)
        self._type = str(_type)
        self._count = 0

    def append(self, item):
        ServerResponse.root_child(self, self._type, item)
        self._count += 1

# XML ServerResponse Exit derrived class
    # To be sent to the client as Exit confirmation only
class ServerResponse_Exit(ServerResponse):
    def __init__(self):
        ServerResponse.__init__(self)
        ServerResponse.root_child(self, COMMAND, EXIT)

# XML ServerResponse ClientError derrived class
    # To be returned to the client when a request is recieved that should never have been sent
    # Not for end-users to view
class ServerResponse_ClientError(ServerResponse):
    def __init__(self):
        ServerResponse.__init__(self)
        ServerResponse.root_child(self, CLIENT_ERROR, 'Invalid request found from client. Check <client_error>s for more info.\n')

    def add_ClientError(self, description):
        ServerResponse.root_child(self, CLIENT_ERROR, description)

# XML ServerResponse Account derrived class
    # To be used when transferring account information from club->table server
class ServerResponse_Account(ServerResponse):
    def __init__(self, account):
        ServerResponse.__init__(self)
        ServerResponse.root_child(self, 'username', str(account.get_username()))
        ServerResponse.root_child(self, 'ID', str(account.get_player_id()))
        ServerResponse.root_child(self, 'balance', str(account.get_balance()))

    def add_Command(self, description):
        ServerResponse.root_child(self, COMMAND, description)


