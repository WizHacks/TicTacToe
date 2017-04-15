from argparse import ArgumentParser
import time
import json
import socket

class Player():
    def __init__(self, username, status=True, gameId=0, timeLoggedIn = None):
        self.username = username  
        self.status = status
        self.gameId = gameId
        if timeLoggedIn != None:
            self.timeLoggedIn = timeLoggedIn  
        else:
            self.timeLoggedIn = time.time()   

    def login(self, clientSocket):
        json_data = json.dumps(self.createPlayerDictionary())        
        message = "LOGIN " + json_data + "\r\n\r\n"
        clientSocket.send(message)
        # TO-DO
        # get 200 or 401 or 400 

    def createPlayerDictionary(self):
        playerDictionary = {}
        playerDictionary['username'] = self.username
        playerDictionary['status'] = self.status
        playerDictionary['gameId'] = self.gameId
        playerDictionary['timeLoggedIn'] = self.timeLoggedIn
        return playerDictionary

    def checkProtocol(self, packet):
        return True

    def printInfo(self):
        print 'username: ', self.username, '\nstatus: ', self.status, '\ngameId: ', self.gameId, '\ntimeLoggedIn: ', self.timeLoggedIn
        
if __name__ == "__main__":    
    # parse commandline arguments
    usage = "%(prog)s serverName serverPort"
    ap = ArgumentParser(usage = usage)

    # Required Arguments
    ap.add_argument("serverName",
                    help="The name of the machine on which the server is running.")
    ap.add_argument("serverPort",
                    help="The port number that the server is listening at.")
    args = ap.parse_args()
    serverName = args.serverName
    serverPort = int(args.serverPort)

    try:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #clientSocket.connect((serverName,serverPort))
        username = raw_input("Input your username: ")
        player = Player(username)
        player.printInfo()
        player.login(clientSocket)    
        # when login is successful
        epoll = select.epoll()
        epoll.register(clientSocket.fileno(), select.EPOLLIN)

    except socket.error:
        print "Error connecting to server. Exiting ..."
    finally:
        clientSocket.close()