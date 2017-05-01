from argparse import ArgumentParser
from jaw_enums import JAWMethods, JAWResponses, JAWStatuses, JAWMisc, JAWStatusNum
import time
import json
import socket, select
import sys, os, fcntl

global player


class Player(object):
	def __init__(self, username, server, status=True, gameId=0, timeLoggedIn = None):
		self.username = username
		self.status = status
		self.gameId = gameId
		self.server = server
		self.lastRequestSent = None
		self.isLoggedIn = False
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
			print "---------------------------------------------------------"
		else:
			print "No such request!"

	def sendMessage(self, message):
		'''
		Send request to client socket with given message
		@param message the message to send to server
		'''
		clientSocket.send(message)
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
	@param requestState player request state
	@param response response received from the server
	'''
	if responseList[1] == JAWStatusNum.OK_NUM and responseList[2] == JAWStatuses.OK:
		print "Last request: " + player.lastRequestSent
		# LOGIN
		if len(responseList) == 3 and player.lastRequestSent == JAWMethods.LOGIN:
			player.isLoggedIn = True
			print "Logged in successfully at time: ", time.strftime("%b %d %Y %H:%M:%S", time.gmtime(player.timeLoggedIn))
		# PRINT
		elif (player.lastRequestSent == JAWMethods.PLACE or player.lastRequestSent == JAWMethods.LOGIN or player.lastRequestSent == JAWMethods.PLAY) and responseList[3][:responseList[3].find(":")] == JAWResponses.PRINT:
			print "board"
			board = responseList[3][responseList[3].find(":")+1:]
			print board[:3] + "\n" + board[3:6] + "\n" + board[6:]
			player.status = False
		# PLAYER
		elif (player.lastRequestSent == JAWMethods.PLACE or player.lastRequestSent == JAWMethods.LOGIN or player.lastRequestSent == JAWMethods.PLAY) and responseList[3][:responseList[3].find(":")] == JAWResponses.PLAYER:
			playerTurn = responseList[3][responseList[3].find(":")+1:]
			if player.username == playerTurn:
				print "Your turn, please place a move:"
			else:
				print "Waiting for opponent ..."
		# PLAYERS
		elif player.lastRequestSent == JAWMethods.WHO and responseList[3][:responseList[3].find(":")] == JAWResponses.PLAYERS:
			playersList = responseList[3][responseList[3].find(":")+1:].split(",")
			if len(playersList) == 0:
				print "No users online!"
			else:
				players = ""
				for player in playersList:
					players += players
				print "Users online: %s" %(players)


	# What happens if server sends me 400?
	if responseList[1] == JAWStatusNum.ERROR_NUM and responseList[2] == JAWResponses.ERROR:
		print "Server sent a 400 ERROR"
		exit(1)

	if responseList[1] == JAWStatusNum.USERNAME_TAKEN_NUM and responseList[2] == JAWStatuses.USERNAME_TAKEN and player.lastRequestSent == JAWMethods.LOGIN:
		print "Username as been taken, please enter another name:"
		return JAWMethods.LOGIN.lower()

	if responseList[1] == JAWStatusNum.USER_BUSY_NUM and responseList[2] == JAWStatuses.USER_BUSY and player.lastRequestSent == JAWMethods.PLAY:
		print "Opponent %s is busy!" %(player.opponent)
		player.opponent = None
		return None

	if responseList[1] == JAWStatusNum.USER_NOT_FOUND_NUM and responseList[2] == JAWStatuses.USER_NOT_FOUND and player.lastRequestSent == JAWMethods.PLAY:
		print "Opponent %s does not exist!" %(player.opponent)
		player.opponent = None
		return None

	if responseList[1] == JAWStatusNum.INVALID_MOVE_NUM and responseList[2] == JAWStatuses.INVALID_MOVE and player.lastRequestSent == JAWMethods.PLACE:
		print "Invalid move: %s" %(player.move)
		return None

	if responseList[1] == JAWStatusNum.GAME_END_NUM and responseList[2] == JAWStatuses.GAME_END and responseList[3][:responseList[3].find(":")] == JAWResponses.WINNER:
		if responseList[3][responseList[3].find(":") + 1:] == player.username:
			print "Congratulations, you won!"
		elif responseList[3][responseList[3].find(":") + 1:] == "None":
			print "Game is a draw!"
		else:
			print "You lost, better luck next time!"
		player.status = True
		return None	# this means someone won

	if responseList[1] == JAWStatusNum.USER_QUIT_NUM and responseList[2] == JAWStatuses.USER_QUIT and player.lastRequestSent == JAWMethods.EXIT:
		print "hi"
		if responseList[3][responseList[3].find(":") + 1:] == player.username:
			print player.username + "Logging off ..."
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
	elif args[0] == "login" or not player.isLoggedIn:
		if player.isLoggedIn:
			print "You have already logged in"
		else:
			while True:
				try:
					username = raw_input("")
					if checkUsername(username):
						break
					print "Username must not contain any spaces!"
				except EOFError:
					continue
			player.username = username
			player.makeRequest(JAWMethods.LOGIN)
	elif args[0] == "exit":
		player.makeRequest(JAWMethods.EXIT)
	elif args[0] == "who":
		player.makeRequest(JAWMethods.WHO)
	elif args[0] == "play":
		if player.status == False:
			print "Already in a game!"
		else:
			player.makeRequest(JAWMethods.PLAY, arg=args[1])
			print "Waiting for server ..."
	elif args[0] == "place":
		if len(args) == 2 and len(args[1]) == 1 and args[1][0] > '0' and args[1][0] <= '9':
			player.makeRequest(JAWMethods.PLACE, args[1][0])
		else:
			print "Invalid number of arguments\nExpected: place [index]\t [ 1, 2, 3]"
			print "\t\t\t [ 4, 5, 6]"
			print "\t\t\t [ 7, 8, 9]"
			print "\t\t\t\t- place your symbol at the corresponding poisition labeled in grid above"
	elif args[0] == "play":
		if  args[1] == player.username:
			print "Cannot play yourself!"
		elif len(args) == 2 and checkUsername(args[1]):
			player.makeRequest(JAWMethods.PLAY, args[1])
	# elif args[0] == "observe":
	# 	print "if len(args) == 2"
	else:
		print "invalid command "

def checkResponseProtocol(packet):
	'''
	Checks to see if response from server is valid protocol
	@return list of extracted protocol details
	'''
	statusCodes = [JAWStatuses.OK, JAWStatuses.ERROR, JAWStatuses.USERNAME_TAKEN,
				JAWStatuses.USER_BUSY, JAWStatuses.USER_NOT_FOUND, JAWStatuses.INVALID_MOVE,
				JAWStatuses.GAME_END, JAWStatuses.USER_QUIT]
	statusBodies = [JAWResponses.PRINT, JAWResponses.PLAYER, JAWResponses.WINNER,
				JAWResponses.PLAYERS, JAWResponses.QUIT]

	args = []
	# print packet
	# print packet.count(JAWMisc.CRNLCRNL)
	if packet.count(JAWMisc.CRNLCRNL) == 1:
		args = packet.strip().split()
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
	print "response protocol: ", args
	return args

def checkUsername(username):
	'''Determine whether the username is valid or not'''
	return username.find(" ") == -1 and len(username) != 0

def help():
	'''
	Prints the help menu
	'''
	print "login [username] \t- logs into a server with unique id.  Force quits if username is already taken"
	print "place [index]\t [ 1, 2, 3]"
	print "\t\t [ 4, 5, 6]"
	print "\t\t [ 7, 8, 9]"
	print "\t\t\t- place your symbol at the corresponding poisition labeled in grid above"
	print "exit\t\t\t- quits the program at any time"
	print "games\t\t\t- obtains a list of all ongoing games along with their respective gameID and players"
	print "who\t\t\t- obtains a list of all players available to play"
	print "play [player] \t\t- challenges the specified player if s/he is available to play"
	print "observe [gameID]\t- tunes into the the specified game"
	print "unobserve [gameID]\t- stops receiving incoming data about particular game"

if __name__ == "__main__":
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
	print "Input your username: ",
	sys.stdout.flush()
	username = raw_input("")
	if not checkUsername(username):
		print "Username must not contain any spaces!"
		exit(1)

	try:
		clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		clientSocket.connect((serverName,serverPort))

		player = Player(username, clientSocket)

		# prompt user to log in
		player.login()
		# dont wait for login response from server, user may wish to exit instead
		# while loop here
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
			events = epoll.poll(0.01) # file no and event code
			for fileno, event in events:
				if event & select.EPOLLHUP:
					# epoll.unregister(fileno)
					# epoll.unregister(stdinfd)
					# epoll.close()
					# clientSocket.close()
					print "Lost connection to server\n Exiting..."
					exit(1)
				if fileno == clientSocket.fileno():
					# print "Received something from the server, process it"
					response = clientSocket.recv(2048)
					# print "RCVD: " + response
					if len(response) == 0:
						print "Lost connection to server\n Exiting..."
						exit(1)
					args = checkResponseProtocol(response)
					# print "ARGS: ",args
					if len(args) != None and len(args) != 0:
						action = processResponse(player, args)
						if action != None:
							processStdin(action)
					else:
						player.makeRequest(JAWMethods.RETRANSMIT)
				elif fileno == stdinfd:
					userinput = sys.stdin.read(128).strip()
					# print "STDIN: " + userinput
					processStdin(userinput)
				else:
					print "Not suppose to print"

	except socket.error:
		print "Error connecting to server. Exiting ..."
	finally:
		epoll.unregister(clientSocket.fileno())
		epoll.unregister(stdinfd)
		epoll.close()
		clientSocket.close()