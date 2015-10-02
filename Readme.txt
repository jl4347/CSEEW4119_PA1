CSEE W4119 Computer Networks
Programming Assignment #1: Socket Programming

=====================================================================
Description
=====================================================================
This is a simple server client chat program, which the connection
between server and client is permanent until client logs out. The 
communication is done via TCP socket.

It supports all the basic commands required by the assignment, including
broadcast, private message, whoelse and wholast, etc.

In the Client.py program, class Client is one that does the real work,
meaning sending all client's requests to the server, whereas the class
ClientCLI is indeed a command line interface for users.

All the messaging between clients is done via the server.

Both the server and the client would logout on Ctrl-c.

=====================================================================
Development Environment
=====================================================================
This program is written in Python 2.7.6, I have done tests on CLIC
machine to make sure it won't fail.

=====================================================================
Run
=====================================================================
In order to use the program, first start the server:
python Server.py <port>

Then start the client:
python Client.py <host> <port>

Make sure the 'user_pass.txt' is in the same directory as Server.py, as
it contains all the credentials for the server to start with.

=====================================================================
Sample commands
=====================================================================
whoelse:
Displays name of other connected users

wholast <number>:
Displays name of those users connected within the last <number> minutes. 
The client CLI would ensure 0 < number < 60

broadcast message <message>:
Broadcasts <message> to all connected users

broadcast user <user> <user> ... <user> message <message>:
Broadcasts <message> to the list of users, it could broadcast to the user
himself if included in the list

message <user> <message>:
Private <message> to a <user>, including sending message to oneself.

logout:
Log out this user.