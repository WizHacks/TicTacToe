from socket import *
from argparse import ArgumentParser
import time
import json

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
        message = "LOGIN ", json_data, "\r\n\r\n"
        clientSocket.send(message)

        # get 200 or 401 or 400 

    def createPlayerDictionary(self):
        playerDictionary = {}
        playerDictionary['username'] = self.username
        playerDictionary['status'] = self.status
        playerDictionary['gameId'] = self.gameId
        playerDictionary['timeLoggedIn'] = self.timeLoggedIn
        return playerDictionary

    def checkProtocol(self, packet):
        

    def printInfo(self):
        print 'username: ', self.username, '\nstatus: ', self.status, '\ngameId: ', self.gameId, '\ntimeLoggedIn: ', self.timeLoggedIn

    def printHelp(self, single):     # boolean single-is this a single player game? true:single    no:multi
        if single:
            print "help\t\t- Prints this menu, which is a list of supported commands along with their syntax"
        print "login [username] \t- logs into a server with unique id.  Force quits if username is already taken"
        print "place [index]"
        print "\t\t[[ 1, 2, 3]"
        print "\t\t [ 4, 5, 6]"
        print "\t\t [ 7, 8, 9]]"
        print "\t\t\t - place your symbol at the corresponding poisition labeled in grid above"
        print "exit\t\t- quits the program at any time"

        if not single:
            print "games\t\t- obtains a list of all ongoing games along with their respective gameID and players"
            print "who\t\t- obtains a list of all players available to play"
            print "play [player] \t- challenges the specified player if s/he is available to play"
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

    
    clientSocket = socket(AF_INET, SOCK_STREAM)
    #clientSocket.connect((serverName,serverPort))
    username = raw_input("Input your username: ")
    player = Player(username)
    player.printInfo()
    player.login()    
    # #clientSocket.send(message.encode())
    # # client waits to receive data from the server
    # modifiedMessage = clientSocket.recv(2048)
    # print("From server: ", modifiedMessage.decode())
    clientSocket.close()