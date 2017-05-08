# TicTacToe
Jia Li, Andrew Lam, and Wendy Zheng

## System Dependencies
- Python 2.7

## The Program
An online modified version of the game Tic-Tac-Toe using Internet domain sockets. It includes both a game client program and a game server program; these two programs communicate with each other using self-implemented application-layer protocol, JAW. Two players can each run the client program to login to a game server and to play a game with each other.

## Obtaining the Source Code
To obtain the source code from the code.tar.gz tarball, run the following command
```
tar -xvzf code.tar.gz
```
You should see the following files after the command has been executed
```
board.py
jaw_enums.py
multiServer.py
player.py
singlePlayer.py
singleServer.py
```

### Running the Program
Start the server (either single or multi) on a linux/unix system as depicted below 
```
python singleServer.py
python multiServer.py
```
Start the client on a linux/unix system with arguments corresponding to the host address and port number of the server as depicted below 
```
python singlePlayer.py serverDomain port
python player.py serverDomain port
```
Please note that the default port value is 9347

## Login/Playing instructions
 - Please see "Project Documentation.pdf" in Documentation folder for System, Testing and User Documentation

### References/Tutorials
- [ePoll](http://scotdoyle.com/python-epoll-howto.html)

