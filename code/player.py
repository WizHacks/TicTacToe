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

    def printHelp(self):     
        
        print "login [username] \t- logs into a server with unique id.  Force quits if username is already taken"
        print "place [index]\t[ 1, 2, 3]"
        print "\t\t [ 4, 5, 6]"
        print "\t\t [ 7, 8, 9]]"
        print "\t\t\t- place your symbol at the corresponding poisition labeled in grid above"
        print "exit\t\t\t- quits the program at any time"
        print "games\t\t\t- obtains a list of all ongoing games along with their respective gameID and players"
        print "who\t\t\t- obtains a list of all players available to play"
        print "play [player] \t\t- challenges the specified player if s/he is available to play"
        print "observe [gameID]\t- tunes into the the specified game"
        print "unobserve [gameID]\t- stops recieving incoming data about particular game"

        
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
        # poll stdin and client socket
        epoll = select.epoll()
        epoll.register(clientSocket.fileno(), select.EPOLLIN)
        # prompt user to log in
        player.login(clientSocket)    
        # when login is successful
        

    except socket.error:
        print "Error connecting to server. Exiting ..."
    finally:
        clientSocket.close()


