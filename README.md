The files contained here are for a simple terminal based chat program I made for school. Me personally, I mainly worked on the server part of this program but the chat is very simple. The PDF displays all the assignment requirements but this is intended to show off the gist of the program. 

To start off, run the server like this.

`./python3 Server.py–port=5555`

And then run the clients in the following format.

Client 1: `python3 client.py--id='student1'--port=3000--server='server_address_here:5555'`

Client 2: `python3 client.py--id='student2'--port=2000--server='server_address_here:5555'`


After that the first client should type `\register` and then `\bridge` in the terminal to register with the server. Then the second client should type `\register`, then `bridge`, then `chat`. After that, the second client can now send a message and it will be sent to the first client and then the first client can respond. Note that this program only works one person at a time so like a walkie talkie. To end the chat, the current active user can type `\quit` to end the chat.
