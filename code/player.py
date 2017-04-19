from argparse import ArgumentParser
import time
import json
import socket

class Player():
    def __init__(self, username, server, status=True, gameId=0, timeLoggedIn = None):
        self.username = username  
        self.status = status
        self.gameId = gameId
        self.server = server
        if timeLoggedIn != None:
            self.timeLoggedIn = timeLoggedIn  
        else:
            self.timeLoggedIn = time.time()   

    '''main methods'''        
    def login(self):
        '''
        Log the player into the server denoted by server
        @return true if successful, false otherwise

        '''
        print 'Login in progress ...'
        json_data = json.dumps(self.createPlayerDictionary())        
        message = "LOGIN " + json_data + "\r\n\r\n"
        clientSocket.send(message)
        # TO-DO
        # get 200 or 401 or 400 

    def play(self, opponent):
        '''
        Send request to server asking to play the specified opponent
        @param opponent the player we wish to versus
        @return true if successful, false otherwise

        '''
        return

    def who(self):
        '''
        Send request to server asking for available users         
        @return true if successful, false otherwise
        '''
        return   
        
    def exit(self):
        '''
        Send break up request to server 
        @return true if successful, false otherwise     
        '''
        return

    def place(self, move):
        '''
        Send request to server to place move at given location         
        @return true if successful, false otherwise
        '''
        return

    def printBoard(self, board):
        '''
        Display the current game board state
        '''
        print "board"  

    def sendMessage(self, message):
        '''
        Send request to client socket with given message
        @param message the message to send to server
        '''
        return  

    def help(self):    
        '''
        Prints the help menu
        '''         
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

    '''Helper methods'''
    def processResponse(self, response):
        '''
        Process the response message returned by the server
        @return true if successful, false otherwise
        '''
        return



    def checkProtocol(self, packet):
        '''
        Checks to see if response from server is valid protocol
        Raise an exception if it does not
        '''
        return True    

    def createPlayerDictionary(self):
        playerDictionary = {}
        playerDictionary['username'] = self.username
        playerDictionary['status'] = self.status
        playerDictionary['gameId'] = self.gameId
        playerDictionary['timeLoggedIn'] = self.timeLoggedIn
        return playerDictionary

    def printInfo(self):
        print 'username: ', self.username, '\nstatus: ', self.status, '\ngameId: ', self.gameId, '\ntimeLoggedIn: ', self.timeLoggedIn
    
'''utility functions'''
def checkUsername(username):
    '''Determine whether the username is valid or not'''
    if username.find(" ") == -1:
        return True
    return False
        
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
        while True:
            username = raw_input("Input your username: ")
            if checkUsername(username):
                break
            print "Username must not contain any spaces!"
        player = Player(username, clientSocket)
        player.printInfo()

        # prompt user to log in
        player.login(clientSocket)    
        # when login is successful
        # while loop here
        # poll stdin and client socket
        epoll = select.epoll()
        epoll.register(clientSocket.fileno(), select.EPOLLIN)
        

    except socket.error:
        print "Error connecting to server. Exiting ..."
    finally:
        clientSocket.close()


