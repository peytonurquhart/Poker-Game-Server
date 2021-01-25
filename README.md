# Python Texas Holdem Game Server

The project consists of one Global Server (although you could use more than one) and an undetermined amount of Game Servers.
The client must connect to the Global Server for authentication, then can be routed to a Game Server (each representing one poker table).
The Global Server follows a thread-per-user architecture. All communication client -> Game Server is done virtually through the Global Server.

Server-Client communication follows a REST API:
+ Client->Global Server (CSV)
  + Global Server->Table Server (XML) ?
  + Table Server -> Global Server (XML) ?
+ Global Server->Client (XML)

Global Server Objectives:
+ Accept incoming connections
+ Manage SQLite database holding user account information
+ Allow users to securely create an account and encrypt private information
+ Login with varying degree of permissions
+ Add/Remove game servers from the network
+ Search the network for running game servers
+ Manage game servers on the network
+ Route users to a game server of their choice
+ Respond to misc. client requests
+ Manage unexpected disconnections/client timeouts

Game Server Objectives:
+ Accept incoming connections from the Global Server
+ Allow users to Join/Leave a game
+ Communicate the current state of the game with the client
+ Respond to client requests (decisions) during a game of poker
+ Manage thread-safe objects for shared data between clients "at the table"
