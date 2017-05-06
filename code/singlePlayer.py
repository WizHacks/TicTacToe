from argparse import ArgumentParser
from jaw_enums import JAWMethods, JAWResponses, JAWStatuses, JAWMisc, JAWStatusNum
import time
import json
import socket, select
import sys, os, fcntl

global player
global debug


class Player(object):
	def __init__(self, username, server, status=True, gameId=0, timeLoggedIn = None):
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
		self.username = username
		self.status = status
		self.gameId = gameId
		self.server = server
		self.lastRequestSent = None
		self.isLoggedIn = False
		self.opponent = None
		self.timeLoggedIn = timeLoggedIn if timeLoggedIn != None else None

	def __str__(self):
		return 'username: '+ self.username + '\nstatus: ' + str(self.status) + '\ngameId: ' + str(self.gameId) + '\ntimeLoggedIn: ' + self.timeLoggedIn

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
		'''
		message = JAWMisc.JAW + " " + JAWMethods.PLACE + " " + move + " " + JAWMisc.CRNLCRNL
		self.move = move
		self.lastRequestSent = JAWMethods.PLACE
		self.sendMessage(message)
		#print "From place(" + move+ ")"

	def retransmit(self):
		'''
		Send request to server to place move at given location
		'''
		message = JAWMisc.JAW + " " + JAWMethods.RETRANSMIT + " " + JAWMisc.CRNLCRNL
		self.sendMessage(message)

	'''Helper methods'''
	def makeRequest(self, request, arg=None):
		if request == JAWMethods.LOGIN:
			self.login()
		elif request == JAWMethods.PLACE:
			self.place(arg)
		elif request == JAWMethods.EXIT:
			self.exit()
		elif request == JAWMethods.RETRANSMIT:
			self.retransmit()
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
		# OTHER PLAYER
		if len(responseList) != 4:
			print "You have connected a multiPlayer server, please play on a singleServer\n SYSTEM DOWN"
			exit(1)
		if (player.lastRequestSent == JAWMethods.LOGIN or player.lastRequestSent == JAWMethods.PLACE) and responseList[3][:responseList[3].find(":")] == JAWResponses.OTHER_PLAYER:
			opponent = responseList[3][responseList[3].find(":")+1:]
			if player.isLoggedIn == False:
				player.isLoggedIn = True
				print "Logged in successfully at time: ", time.strftime("%b %d %Y %H:%M:%S", time.gmtime(player.timeLoggedIn))
			print "\nYour opponent is: " + opponent
			player.opponent = opponent
			player.status = False

		# PRINT
		elif (player.lastRequestSent == JAWMethods.PLACE or player.lastRequestSent == JAWMethods.LOGIN) and responseList[3][:responseList[3].find(":")] == JAWResponses.PRINT:
			board = responseList[3][responseList[3].find(":")+1:]
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

	# 400 ERROR
	if responseList[1] == JAWStatusNum.ERROR_NUM and responseList[2] == JAWStatuses.ERROR:
		print "Server sent a 400 ERROR"
		print "Please try again later!"
		exit(1)

	# 406 PLEASE WAIT
	if responseList[1] == JAWStatusNum.PLEASE_WAIT_NUM and responseList[2] == JAWStatuses.PLEASE_WAIT:
		print "Please wait ... searching for opponent"

	# 402 USERNAME TAKEN
	if responseList[1] == JAWStatusNum.USERNAME_TAKEN_NUM and responseList[2] == JAWStatuses.USERNAME_TAKEN and player.lastRequestSent == JAWMethods.LOGIN:
		print "Username has been taken, please enter another name:"
		return JAWMethods.LOGIN.lower()

	# 405 INVALID MOVE NUMBER
	if responseList[1] == JAWStatusNum.INVALID_MOVE_NUM and responseList[2] == JAWStatuses.INVALID_MOVE and player.lastRequestSent == JAWMethods.PLACE:
		print "Invalid move: %s" %(player.move)
		return None

	# 405 GAME END
	if responseList[1] == JAWStatusNum.GAME_END_NUM and responseList[2] == JAWStatuses.GAME_END and responseList[3][:responseList[3].find(":")] == JAWResponses.WINNER:
		if responseList[3][responseList[3].find(":") + 1:] == player.username:
			print "Congratulations, you won!"
			print "Please wait ... searching for opponent"
		elif responseList[3][responseList[3].find(":") + 1:] == "None":
			print "Game is a draw!"
			print "Please wait ... searching for opponent"
		else:
			print "You lost, better luck next time!"
			print "Please wait ... searching for opponent"
		player.status = True
		return None	# this means someone won

	# 202 USER QUIT
	if responseList[1] == JAWStatusNum.USER_QUIT_NUM and responseList[2] == JAWStatuses.USER_QUIT and player.lastRequestSent == JAWMethods.EXIT:
		if responseList[3][responseList[3].find(":") + 1:] == player.username:
			print player.username + " Logging off ..."
			exit(1)

def processStdin(stdinInput):
	'''
	Process the stdin input and take appropriate action
	@param stdinInput input received from stdin
	'''
	global player
	args = stdinInput.split(" ")
	args[0] = args[0].lower()
	if args[0] == "help":
		help()
	elif args[0] == "exit":
		player.makeRequest(JAWMethods.EXIT)
		return True
	elif args[0] == "place" and player.isLoggedIn:
		if not player.status:
			if len(args) == 2 and len(args[1]) == 1 and args[1][0] > '0' and args[1][0] <= '9':
				player.makeRequest(JAWMethods.PLACE, args[1][0])
			else:
				print "Invalid number of arguments"
				print "Expected: place [index]\t [ 1, 2, 3]\n\t\t\t [ 4, 5, 6]\n\t\t\t [ 7, 8, 9]"
				print "\tPlace your symbol at the corresponding poisition labeled in grid above"
	# elif args[0] == "observe":
	# 	print "if len(args) == 2"
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
	@return list of extracted protocol details, [1],[1] is a failure, [],[] is retransmit
	@note can handle two messages in a row, returns them as a tuple
	'''
	statusCodes = [JAWStatuses.OK, JAWStatuses.ERROR, JAWStatuses.USERNAME_TAKEN,
				JAWStatuses.INVALID_MOVE, JAWStatuses.PLEASE_WAIT,
				JAWStatuses.GAME_END, JAWStatuses.USER_QUIT]
	statusBodies = [JAWResponses.PRINT, JAWResponses.PLAYER, JAWResponses.WINNER,
				JAWResponses.QUIT, JAWResponses.OTHER_PLAYER]

	args = []
	if debug:
		print packet
		print packet.count(JAWMisc.CRNLCRNL)
	# HAS exactly 1 JAWMisc.CRNLCRNL
	if packet.count(JAWMisc.CRNLCRNL) == 1:
		args = packet.strip().split()
		if debug:
			print "args: ", args
		if args[0] != JAWMisc.JAW:
			print "Invalid format -> required protocol to begin with JAW/1.0"
			return [1], [1]
		try:
			int(args[1])
		except ValueError:
			print "Invalid status number\nExpected: number\nFound: ", args[1]
			return [1], [1]
		if args[2] not in statusCodes:
			print "Invalid status code\nExpected:OK,ERROR,USERNAME_TAKEN,",
			print "INVALID_MOVE,GAME_END,USER_QUIT,PLEASE_WAIT\nFound: ", args[2]

			return [1], [1]
		# HAS RESPONSE BODY
		if packet.count(JAWMisc.CRNL) == 3:
			if len(args) != 4:
				print "Invalid protocol length"
				return [1], [1]
			else:
				if args[3][0:args[3].find(":")] not in statusBodies:
					print "Invalid protocol format ... ignored"
					return [1], [1]
				else:
					if debug:
						print "response protocol: ", args
					return args, []
		elif len(args) != 3:
				print "Invalid protocol length"
				return [1], [1]
		else:
			if debug:
				print "response protocol: ", args
			return args, []
	# TWO MESSAGES
	if packet.count(JAWMisc.CRNLCRNL) == 2:
		args = packet.strip().split()
		if debug:
			print "args: ", args
		if args[0] != JAWMisc.JAW and args[4] != JAWMisc.JAW:
			print "Invalid format -> required protocol to begin with JAW/1.0"
			return [1], [1]
		try:
			int(args[1])
			int(args[5])
		except ValueError:
			print "Invalid status number\nExpected: number\nFound: ", args[1], args[5]
			return [1], [1]
		if args[2] not in statusCodes and args[6] not in statusCodes:
			print "Invalid status code\nExpected:OK,ERROR,USERNAME_TAKEN,",
			print "INVALID_MOVE,GAME_END,USER_QUIT,PLEASE_WAIT\nFound: ", args[2]
			return [1], [1]
		# TWO BODIES
		if packet.count(JAWMisc.CRNL) == 6:
			if len(args) != 8:
				print "Invalid protocol length"
				return [1], [1]
			else:
				if args[3][0:args[3].find(":")] not in statusBodies:
					print "Invalid protocol format ... ignored"
					return [1], [1]
				if args[7][0:args[7].find(":")] not in statusBodies:
					print "Invalid protocol format ... ignored"
					return [1], [1]
				if debug:
					print "response protocol: ", args
				return args[0:4], args[4:]
		elif len(args) != 6:
			print "Invalid protocol length"
			return [1], [1]
		else:
			if debug:
				print "response protocol: ", args
			return args[0:4], args[4:]
	return [], []

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

if __name__ == "__main__":
	debug = True
	# parse commandline arguments
	usage = "%(prog)s serverName serverPort"
	ap = ArgumentParser(usage = usage)

	# Required Arguments
	ap.add_argument("serverName", help="The name of the machine on which the server is running.")
	ap.add_argument("serverPort", help="The port number that the server is listening at.")
	args = ap.parse_args()
	serverName = args.serverName	

	try:
		serverPort = int(args.serverPort)
	except ValueError:
		print "Please check your arguments!"
		exit(1)

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
		fl = fcntl.fcntl(stdinfd, fcntl.F_GETFL)
		fcntl.fcntl(stdinfd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
		epoll.register(clientSocket.fileno(), select.EPOLLIN | select.EPOLLET)
		epoll.register(stdinfd, select.EPOLLIN)
	except socket.error:
		print "Error connecting to server. Exiting ..."
		exit(1)

	try:
		while True:
			events = epoll.poll(0.1) # file no and event code
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
					args1, args2 = checkResponseProtocol(response)
					if debug:
						print args1
						print args2
					if len(args1) > 1:
						action = processResponse(player, args1)
						if action != None:
							processStdin(action)
						if len(args2) > 1:
							processResponse(player, args2)
					else:
					# Received empty packet from server, ask for retransmission
						player.makeRequest(JAWMethods.RETRANSMIT)
				elif fileno == stdinfd:
					userinput = sys.stdin.read(128).strip()
					# print "STDIN: " + userinput
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