from argparse import ArgumentParser
from jaw_enums import JAWMethods, JAWResponses, JAWStatuses, JAWMisc, JAWStatusNum
import time
import json
import socket, select
import sys, os, fcntl

global player
global debug

class Player(object):
	'''
	Player class, used as client when talking to server
	username: username of the player
	status: True (Available), False (Busy)
	gameId: gameid of the game the player is in
	timeLoggedIn: Datetime value of login time
	lastRequestSent: keep track of the last request sent to server
	isLoggedIn: whether the client has logged in successively or nor
	opponent: the opposing player in a game
	'''
	def __init__(self, username, server, status=True, gameId=0, timeLoggedIn = None):
		self.username = username
		self.status = status
		self.gameId = gameId
		self.server = server
		self.lastRequestSent = None
		self.isLoggedIn = False
		self.opponent = None
		self.timeLoggedIn = timeLoggedIn if timeLoggedIn != None else None

	def __str__(self):
		return 'username: '+ self.username + '\nstatus: ' + str(self.status) + '\ngameId: ' + str(self.gameId) + '\ntimeLoggedIn: ' + str(self.timeLoggedIn)

	'''main methods'''
	def login(self):
		'''
		Log the player into the server denoted by server
		'''
		print "Login in progress ..."
		player.timeLoggedIn = time.time()
		json_data = json.dumps(self.createPlayerDictionary())
		message = JAWMisc.JAW + " " + JAWMethods.LOGIN + " " + json_data + " " + JAWMisc.CRNLCRNL
		self.lastRequestSent = JAWMethods.LOGIN
		self.sendMessage(message)

	def play(self, opponent):
		'''
		Send request to server asking to play the specified opponent
		@param opponent the player we wish to versus
		'''
		message = JAWMisc.JAW + " " + JAWMethods.PLAY + " " + opponent +" " + " " + JAWMisc.CRNLCRNL
		self.opponent = opponent
		self.lastRequestSent = JAWMethods.PLAY
		self.sendMessage(message)

	def who(self):
		'''
		Send request to server asking for available users
		'''
		message = JAWMisc.JAW + " " + JAWMethods.WHO + " " + JAWMisc.CRNLCRNL
		self.lastRequestSent = JAWMethods.WHO
		self.sendMessage(message)

	def exit(self):
		'''
		Send break up request to server
		'''
		message = JAWMisc.JAW + " " + JAWMethods.EXIT + " " + JAWMisc.CRNLCRNL
		self.lastRequestSent = JAWMethods.EXIT
		self.sendMessage(message)
		print "Goodbye world, %s ... " %(player.username)

	def place(self, move):
		'''
		Send request to server to place move at given location
		@param move number 1-9 location to place the mark
		'''
		message = JAWMisc.JAW + " " + JAWMethods.PLACE + " " + move + " " + JAWMisc.CRNLCRNL
		self.move = move
		self.lastRequestSent = JAWMethods.PLACE
		self.sendMessage(message)

	def retransmit(self):
		'''
		Send request to server to retransmit last message
		'''
		message = JAWMisc.JAW + " " + JAWMethods.RETRANSMIT + " " + JAWMisc.CRNLCRNL
		self.sendMessage(message)

	def games(self):
		'''
		Send request to server to get the list of ongoing games
		'''
		message = JAWMisc.JAW + " " + JAWMethods.GAMES + " " + JAWMisc.CRNLCRNL
		self.lastRequestSent = JAWMethods.GAMES
		self.sendMessage(message)

	'''Helper methods'''
	def makeRequest(self, request, arg=None):
		'''
		Have the player client make a request
		@param request the request to make
		@param arg for play and place
		'''
		if request == JAWMethods.LOGIN:
			self.login()
		elif request == JAWMethods.PLAY:
			self.play(arg)
		elif request == JAWMethods.WHO:
			self.who()
		elif request == JAWMethods.PLACE:
			self.place(arg)
		elif request == JAWMethods.EXIT:
			self.exit()
		elif request == JAWMethods.RETRANSMIT:
			self.retransmit()
		elif request == JAWMethods.GAMES:
			self.games()
		else:
			print "No such request!"

	def sendMessage(self, message):
		'''
		Send request to client socket with given message
		@param message the message to send to server
		'''
		clientSocket.send(message)
		if debug:
			print "SENT: " + message

	def createPlayerDictionary(self):
		'''
		Create dictionary representing player info
		'''
		playerDictionary = {}
		playerDictionary['username'] = self.username
		playerDictionary['status'] = self.status
		playerDictionary['gameId'] = self.gameId
		playerDictionary['timeLoggedIn'] = self.timeLoggedIn
		return playerDictionary

'''utility functions'''
def processResponse(player, responseList):
	'''
	Process the response message returned by the server and take appropriate action
	@param responseList the list of responses args
	'''
	if responseList[1] == JAWStatusNum.OK_NUM and responseList[2] == JAWStatuses.OK:
		if debug:
			print "Last request: " + player.lastRequestSent
		# LOGIN
		if len(responseList) == 3 and player.lastRequestSent == JAWMethods.LOGIN:
			player.isLoggedIn = True
			print "Hello World,", player.username + "!"
			print "Logged in successfully at time: ", time.strftime("%b %d %Y %H:%M:%S", time.gmtime(player.timeLoggedIn))

		# PRINT
		elif (player.lastRequestSent == JAWMethods.PLACE or player.lastRequestSent == JAWMethods.LOGIN or player.lastRequestSent == JAWMethods.PLAY or player.lastRequestSent == JAWMethods.GAMES or player.lastRequestSent == JAWMethods.WHO) and responseList[3][:responseList[3].find(":")] == JAWResponses.PRINT:
			board = responseList[3][responseList[3].find(":")+1:]
			if board == ".........":
				print "A game has started ~"
			print board[:3] + "\n" + board[3:6] + "\n" + board[6:]
			player.status = False

		# PLAYER
		elif (player.lastRequestSent == JAWMethods.PLACE or player.lastRequestSent == JAWMethods.LOGIN or player.lastRequestSent == JAWMethods.PLAY) and responseList[3][:responseList[3].find(":")] == JAWResponses.PLAYER:
			playerTurn = responseList[3][responseList[3].find(":")+1:]
			if player.username == playerTurn:
				print "Your turn, please place a move: (hint: place [1-9])"
			else:
				if player.opponent == None:
					player.opponent = playerTurn

				print "Waiting for %s's move..." %(player.opponent)

		# PLAYERS
		elif player.lastRequestSent == JAWMethods.WHO and responseList[3][:responseList[3].find(":")] == JAWResponses.PLAYERS:
			playersList = responseList[3][responseList[3].find(":")+1:].split(",")
			if playersList[0] == "":
				print "No available users online!"
			else:
				print "Available users online:"
				for player in playersList:
					print player
		# GAMES
		elif player.lastRequestSent == JAWMethods.GAMES and responseList[3][:responseList[3].find(":")] == JAWResponses.GAMES:
			gamesList = responseList[3][responseList[3].find(":")+1:].split(";")
			if gamesList[0] == "":
				print "No games in progress!"
			else:
				games = ""
				for game in gamesList:
					playerStart = game.find("-")
					print playerStart
					gameid = game[:playerStart]
					playersList = game[playerStart+1:].split(',')
					games += "\nGame ID: " + gameid + "\nPlayers: " + playersList[0] + ", "+ playersList[1] + "\n"
				print "Games in progress:\n" + "-"*25 + "%s" %(games)

	# 400 ERROR
	if responseList[1] == JAWStatusNum.ERROR_NUM and responseList[2] == JAWStatuses.ERROR:
		print "Server sent a 400 ERROR"
		exit(1)

	# 401 USERNAME TAKEN
	if responseList[1] == JAWStatusNum.USERNAME_TAKEN_NUM and responseList[2] == JAWStatuses.USERNAME_TAKEN and player.lastRequestSent == JAWMethods.LOGIN:
		print "Username as been taken, please try again!"

	# 402 USER BUSY
	if responseList[1] == JAWStatusNum.USER_BUSY_NUM and responseList[2] == JAWStatuses.USER_BUSY and player.lastRequestSent == JAWMethods.PLAY:
		print "Opponent %s is busy!" %(player.opponent)
		player.opponent = None

	# 403 USERNAME NOT FOUND
	if responseList[1] == JAWStatusNum.USER_NOT_FOUND_NUM and responseList[2] == JAWStatuses.USER_NOT_FOUND and player.lastRequestSent == JAWMethods.PLAY:
		print "Opponent %s does not exist!" %(player.opponent)
		player.opponent = None

	# 404 INVALID MOVE
	if responseList[1] == JAWStatusNum.INVALID_MOVE_NUM and responseList[2] == JAWStatuses.INVALID_MOVE and player.lastRequestSent == JAWMethods.PLACE:
		print "Invalid move: %s" %(player.move)

	# 201 GAME END
	if responseList[1] == JAWStatusNum.GAME_END_NUM and responseList[2] == JAWStatuses.GAME_END and responseList[3][:responseList[3].find(":")] == JAWResponses.WINNER:
		if responseList[3][responseList[3].find(":") + 1:] == player.username:
			print "Congratulations, you won!"
		elif responseList[3][responseList[3].find(":") + 1:] == "None":
			print "Game is a draw!"
		else:
			print "You lost, better luck next time!"
		player.status = True
		# this means someone won

def processStdin(stdinInput):
	'''
	Process the stdin input and take appropriate action
	@param stdinInput input received from stdin
	'''
	global player
	args = stdinInput.split(" ")
	# print "STDIN ", args
	args[0] = args[0].lower()
	# HELP
	if args[0] == "help":
		help()
	# WHOAMI
	elif args[0] == "whoami" and player.isLoggedIn:
		print "Who is " + player.username
	# EXIT
	elif args[0] == "exit":
		player.makeRequest(JAWMethods.EXIT)
		return True
	# WHO
	elif args[0] == "who" and player.isLoggedIn:
		player.makeRequest(JAWMethods.WHO)
	# PLAY
	elif args[0] == "play" and player.isLoggedIn:
		if player.status == False:
			print "Already in a game!"
		elif args[1] == player.username:
			print "Cannot play yourself!"
		else:
			player.makeRequest(JAWMethods.PLAY, arg=args[1])
	# GAMES
	elif args[0] == "games" and player.isLoggedIn:
		player.makeRequest(JAWMethods.GAMES)
		print "Requesting games from the server ..."
	# PLACE
	elif args[0] == "place" and player.isLoggedIn:
		if not player.status:
			if len(args) == 2 and len(args[1]) == 1 and args[1][0] > '0' and args[1][0] <= '9':
				player.makeRequest(JAWMethods.PLACE, args[1][0])
			else:
				print "Invalid number of arguments"
				print "Expected: place [index]\t [ 1, 2, 3]\n\t\t\t [ 4, 5, 6]\n\t\t\t [ 7, 8, 9]"
				print "\t\t\t\t- place your symbol at the corresponding poisition labeled in grid above"
		else:
			print "Please start a game first!"
	# elif args[0] == "observe":
	# 	print "if len(args) == 2"
	# LOGIN
	elif args[0] == "login" and not player.isLoggedIn:
		if len(args) == 2:
			if checkUsername(args[1]):
				player.username = args[1]
				player.makeRequest(JAWMethods.LOGIN)
			else:
				print "Username must be alphanumeric and not contain any spaces!"
	else:
		if player.isLoggedIn:
			if args[0] == "login":
				print 'Already logged in as %s!' %(player.username)
			else:
				print "Invalid command: ", args[0]
		else:
			print "Please login first!"
	return False

def checkResponseProtocol(packet):
	'''
	Checks to see if response from server is valid protocol
	@param packet the packet
	@return list of extracted protocol details, [] is retransmission
	'''
	statusCodes = [JAWStatuses.OK, JAWStatuses.ERROR, JAWStatuses.USERNAME_TAKEN,
				JAWStatuses.USER_BUSY, JAWStatuses.USER_NOT_FOUND, JAWStatuses.INVALID_MOVE,
				JAWStatuses.GAME_END, JAWStatuses.USER_QUIT]
	statusBodies = [JAWResponses.PRINT, JAWResponses.PLAYER, JAWResponses.WINNER,
				JAWResponses.PLAYERS, JAWResponses.QUIT, JAWResponses.GAMES]

	args = []
	# HAS exactly 1 JAWMisc.CRNLCRNL
	if packet.count(JAWMisc.CRNLCRNL) == 1:
		args = packet.strip().split()
		if debug:
			print "args: ", args
		if args[0] != JAWMisc.JAW:
			print "Invalid format -> required protocol to begin with JAW/1.0"
			return None
		try:
			int(args[1])
		except ValueError:
			print "Invalid status number\nExpected: number\nFound: ", args[1]
			return None
		if args[2] not in statusCodes:
			print "Invalid status code\nExpected:OK,ERROR,USERNAME_TAKEN,USER_BUSY,USER_NOT_FOUND,",
			print "INVALID_MOVE,GAME_END,USER_QUIT\n Found: ", args[2]
			return None
		# HAS RESPONSE BODY
		if packet.count(JAWMisc.CRNL) == 3:
			if len(args) != 4:
				print "Invalid protocol length"
				return None
			else:
				if args[3][0:args[3].find(":")] not in statusBodies:
					print "Invalid protocol format ... ignored"
					return None
		else:
			if len(args) != 3:
				print "Invalid protocol length"
				return None
	if debug:
		print "response protocol: ", args
	return args

def checkUsername(username):
	'''Determine whether the username is alphanumeric and does not contain spaces '''
	if username.isalnum():
		return username.find(" ") == -1 and len(username) != 0
	return 0

def help():
	'''
	Prints the help menu
	'''
	print "login [username] \t- logs into a server with unique id."
	print "place [index]\t [ 1, 2, 3]\n\t\t [ 4, 5, 6]\n\t\t [ 7, 8, 9]"
	print "\t\t\t- place your symbol at the corresponding poisition labeled in grid above"
	print "exit\t\t\t- quits the program at any time"
	print "games\t\t\t- obtains a list of all ongoing games along with their respective gameID and players"
	print "who\t\t\t- obtains a list of all players available to play"
	print "play [player] \t\t- challenges the specified player if s/he is available to play"
	# print "observe [gameID]\t- tunes into the the specified game"
	# print "unobserve [gameID]\t- stops receiving incoming data about particular game\n"

if __name__ == "__main__":
	global debug
	debug = False 				# False-turn off debugging		True- Turn on debugging
	# parse commandline arguments
	usage = "%(prog)s serverName serverPort"
	ap = ArgumentParser(usage = usage)

	# Required Arguments
	ap.add_argument("serverName", help="The name of the machine on which the server is running.")
	ap.add_argument("serverPort", help="The port number that the server is listening at.")
	args = ap.parse_args()
	serverName = args.serverName
	serverPort = int(args.serverPort)

	epoll = select.epoll()
	print "Welcome to TicTacToc!"
	sys.stdout.flush()

	try:
		clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		clientSocket.connect((serverName,serverPort))
		# Default player skeleton
		player = Player("", clientSocket)

		# poll stdin and client socket
		stdinfd = sys.stdin.fileno()
		fcntl.fcntl(stdinfd, fcntl.F_SETFL, fcntl.fcntl(stdinfd, fcntl.F_GETFL) | os.O_NONBLOCK)
		epoll.register(clientSocket.fileno(), select.EPOLLIN | select.EPOLLET)
		epoll.register(stdinfd, select.EPOLLIN)
	except socket.error:
		print "Error connecting to server. Exiting ..."
		exit(1)

	try:
		while True:
			events = epoll.poll(0.01) # file no and event code
			for fileno, event in events:
				if event & select.EPOLLHUP:
					print "Lost connection to server\n Exiting..."
					exit(1)
				if fileno == clientSocket.fileno():
					# print "Received something from the server, process it"
					response = clientSocket.recv(2048)
					# print "RCVD: " + response
					if len(response) == 0:
						print "Lost connection to server\n Exiting..."
						exit(1)
					# Check protocol format
					args = checkResponseProtocol(response)
					if args != None and len(args) != 0:
						# Process response
						processResponse(player, args)
					# Received empty packet from server, ask for retransmission
					else:
						player.makeRequest(JAWMethods.RETRANSMIT)
					print ""
				elif fileno == stdinfd:
					userinput = sys.stdin.read(128).strip()
					quit = processStdin(userinput)
					if quit:
						exit(1)
				else:
					print "Not suppose to print"

	except socket.error:
		print "Error connecting to server. Exiting ..."
	finally:
		# cleanup
		epoll.unregister(clientSocket.fileno())
		epoll.unregister(stdinfd)
		epoll.close()
		clientSocket.close()