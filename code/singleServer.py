from socket import *
import select, uuid, board, json, time, datetime

global debug
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverPort = 9347 # Default port number
serverSocket.bind(('', serverPort))
serverSocket.listen(1)
serverSocket.setblocking(0)

epoll = select.epoll()
epoll.register(serverSocket.fileno(), select.EPOLLIN)

class Server(object):
	def __init__(self):
		self.players = {} # Dictionary with key as connection's file descriptor and value as JSON format of Player class
		self.games = {} # Dictionary with key as game's Id and value as the Board class
		self.connections = {} # Dictionary with key as connection's file descriptor and value as actual connection. Used for ePoll connections
		self.retransmits = {} # Dictionary with key as connection's file descriptor and value as data that was last sent by server. Only contains most recent data sent by server.

	'''main methods'''
	def addConnection(self, connection):
		'''
		Add connection new socket connection
		@param connection the new socket connection
		'''
		self.connections[connection.fileno()] = connection

	def playerAvailable(self, username):
		'''
		Checks if player with a user id of username is busy or not
		@param username User id of user to check for
		@return True if player is not busy. False otherwise.
		'''
		for key, value in self.players.iteritems():
			if username == value['username']:
				return value['status']
		return False

	def playerExists(self, username):
		'''
		Checks if player with a user id of username exists
		@param username User id of user to check for
		@return True if player exists. False otherwise.
		'''
		for key, value in self.players.iteritems():
			if username == value['username']:
				return True
		return False

	def getAvailablePlayers(self):
		'''
		Returns the list of all available players
		@return List of all available players
		'''
		names = []
		for key, value in self.players.iteritems():
			if value['status'] == True:
				names.append(value['username'])
		return names

	def removePlayer(self, fileno):
		'''
		Removes the specified player
		@param fileno File descriptor associated with user
		'''
		try:
			# check if user logged in after establishing a connection
			currentPlayer = self.players[fileno]
		except Exception:
			# if user did not log in after establishing connection, just remove connection information
			fNum = fileno
			epoll.unregister(fileno)
			self.connections[fNum].close()
			del self.connections[fNum]
			return
		if currentPlayer['status'] == True:
			# Player is not in game
			self.sendMessage("JAW/1.0 202 USER_QUIT \r\n QUIT:" + currentPlayer['username'] + " \r\n\r\n", fileno)
			fNum = fileno

			# Remove player and its corresponding ePoll connection
			epoll.unregister(fileno)
			self.connections[fNum].close()
			del self.connections[fNum]
			del self.players[fNum]
		else:
			# Player is in game
			currentGame = self.games[currentPlayer['gameId']]
			otherPlayer = currentGame.player2 if currentPlayer['username'] != currentGame.player2 else currentGame.player1
			del self.games[currentPlayer['gameId']]

			# Notify both players who quitted and who won. End the game
			try:
				self.retransmits[self.getSocket(otherPlayer)] = ["JAW/1.0 202 USER_QUIT \r\n QUIT:" + currentPlayer['username'] + " \r\n\r\n", "JAW/1.0 201 GAME_END \r\n WINNER:" + otherPlayer + " \r\n\r\n"]
				self.broadcast("JAW/1.0 202 USER_QUIT \r\n QUIT:" + currentPlayer['username'] + " \r\n\r\n", [fileno, self.getSocket(otherPlayer)])
				self.broadcast("JAW/1.0 201 GAME_END \r\n WINNER:" + otherPlayer + " \r\n\r\n", [fileno, self.getSocket(otherPlayer)])
			except Exception:
				# Current player did Ctrl+C
				self.retransmits[self.getSocket(otherPlayer)] = ["JAW/1.0 202 USER_QUIT \r\n QUIT:" + currentPlayer['username'] + " \r\n\r\n", "JAW/1.0 201 GAME_END \r\n WINNER:" + otherPlayer + " \r\n\r\n"]
				self.broadcast("JAW/1.0 202 USER_QUIT \r\n QUIT:" + currentPlayer['username'] + " \r\n\r\n", [self.getSocket(otherPlayer)])
				self.broadcast("JAW/1.0 201 GAME_END \r\n WINNER:" + otherPlayer + " \r\n\r\n", [self.getSocket(otherPlayer)])

			otherPlayer = self.getPlayer(otherPlayer)
			otherPlayer['gameId'] = None
			otherPlayer['status'] = True
			fNum = fileno

			# Remove quitting player and its corresponding ePoll connection
			epoll.unregister(fileno)
			self.connections[fNum].close()
			del self.connections[fNum]
			del self.players[fNum]
		return

	def addPlayer(self, connection, player):
		'''
		Adds player to the server
		@param connection Socket connection associated with player
		@param player Player to add to the server
		'''
		self.players[connection.fileno()] = player

	def createGame(self, p1, p2):
		'''
		Create game with 2 players
		@param p1 Player 1
		@param p2 Player 2
		@return game Object of the new game board created
		'''
		gameId = uuid.uuid4().int
		newBoard = None
		if p1['timeLoggedIn'] < p2['timeLoggedIn']:
			newBoard = board.Board(p1['username'], p2['username'], p1['username'])
		else:
			newBoard = board.Board(p1['username'], p2['username'], p2['username'])
		self.games[gameId] = newBoard
		p1['gameId'] = gameId
		p2['gameId'] = gameId
		p1['status'] = False
		p2['status'] = False
		return newBoard

	def endGame(self, gameID, p1, p2):
		'''
		Ends the game
		@param gameID Game ID of the game to end
		@param p1 Player1
		@param p2 Player2
		'''
		del self.games[gameID]
		p1['gameId'] = None
		p2['gameId'] = None
		p1['status'] = True
		p2['status'] = True
		return

	def sendMessage(self, message, fileno):
		'''
		Sends a message to the client
		@param message Message to send
		@param fileno File descriptor of ePoll connection to send message to
		'''
		epoll.modify(fileno, select.EPOLLOUT)
		self.connections[fileno].send(message)
		epoll.modify(fileno, select.EPOLLIN | select.EPOLLET)
		if debug:
			print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + "\tSent to connection " + str(fileno) + ": " + message # Log server action
		return


	def broadcast(self, message, connections):
		'''
		Broadcasts message to everyone
		@param message Message to send
		@param connections File descriptors of socket connections to send message to
		'''
		for c in connections:
			self.sendMessage(message, c)
		return

	def checkRequestProtocol(self, fileno):
		'''
		Checks the request protocol
		@param fileno Incoming socket connection file descriptor
		'''
		# Receive incoming data
		connection = self.connections[fileno]
		request = connection.recv(1024).decode()
		if debug:
			print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + "\tReceived request from connection " + str(fileno) + ": " + request # Log server action

		# Check for invalid protocol
		if (len(request) == 0):
			self.removePlayer(fileno)
			return
		recurr = request.count('\r\n\r\n')
		if recurr == 0 or recurr > 1:
			self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
			self.retransmits[fileno] = ["JAW/1.0 400 ERROR \r\n\r\n"]
			return
		requests = request.split()
		if len(requests) < 2:
			self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
			self.retransmits[fileno] = ["JAW/1.0 400 ERROR \r\n\r\n"]
			return

		# LOGIN
		if requests[1] == "LOGIN":
			# Invalid command usage
			if len(requests) < 3 or len(self.connections) > 2:
				self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
				fNum = fileno
				epoll.unregister(fileno)
				self.connections[fNum].close()
				del self.connections[fNum]
			else:
				# Extract player data
				newPlayer = request[request.find(" ")+6 : len(request)]
				try:
					player = json.loads(newPlayer)
				except Exception:
					# Invalid player data
					self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
					fNum = fileno
					epoll.unregister(fileno)
					self.connections[fNum].close()
					del self.connections[fNum]
					return
				if self.playerExists(player['username']):
					# Check if username (the user id) is taken
					self.sendMessage("JAW/1.0 401 USERNAME_TAKEN \r\n\r\n", fileno)
					self.retransmits[fileno] = ["JAW/1.0 401 USERNAME_TAKEN \r\n\r\n"]
				else:
					self.addPlayer(connection, player)
					if len(self.connections) == 2:
						# If 2 players are on, autoplay begins
						otherPlayer = None
						for key, value in self.players.iteritems():
							if player['username'] != value['username']:
								otherPlayer = value
								break
						game = self.createGame(otherPlayer, player)
						self.retransmits[fileno] = ["JAW/1.0 200 OK \r\n OTHER_PLAYER:" + otherPlayer['username'] + " \r\n\r\n"]
						self.retransmits[fileno].append("JAW/1.0 200 OK \r\n PRINT:" + str(game) + " \r\n\r\n")
						self.retransmits[fileno].append("JAW/1.0 200 OK \r\n PLAYER:" + game.currentPlayer + " \r\n\r\n")
						self.retransmits[self.getSocket(otherPlayer['username'])] = ["JAW/1.0 200 OK \r\n OTHER_PLAYER:" + player['username'] + " \r\n\r\n", "JAW/1.0 200 OK \r\n PRINT:" + str(game) + " \r\n\r\n", "JAW/1.0 200 OK \r\n PLAYER:" + game.currentPlayer + " \r\n\r\n"]
						self.sendMessage("JAW/1.0 200 OK \r\n OTHER_PLAYER:" + otherPlayer['username'] + " \r\n\r\n", fileno)
						self.sendMessage("JAW/1.0 200 OK \r\n OTHER_PLAYER:" + player['username'] + " \r\n\r\n", self.getSocket(otherPlayer['username']))
						self.broadcast("JAW/1.0 200 OK \r\n PRINT:" + str(game) + " \r\n\r\n", [fileno, self.getSocket(otherPlayer['username'])])
						self.broadcast("JAW/1.0 200 OK \r\n PLAYER:" + game.currentPlayer + " \r\n\r\n", [fileno, self.getSocket(otherPlayer['username'])])
					else:
						# Player has to wait for another player
						self.sendMessage("JAW/1.0 406 PLEASE_WAIT \r\n\r\n", fileno)
						self.retransmits[fileno] = ["JAW/1.0 406 PLEASE_WAIT \r\n\r\n"]
		# PLACE
		elif requests[1] == "PLACE":
			if len(requests) < 3:
				# Invalid command usage
				self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
				self.retransmits[fileno] = ["JAW/1.0 400 ERROR \r\n\r\n"]
			else:
				currentPlayer = self.players[fileno]
				if currentPlayer['gameId'] == 0 or currentPlayer['gameId'] == None:
					# Checks if player is in a game
					self.sendMessage("JAW/1.0 405 INVALID_MOVE \r\n\r\n", fileno)
					self.retransmits[fileno] = ["JAW/1.0 405 INVALID_MOVE \r\n\r\n"]
					return
				currentGame = self.games[currentPlayer['gameId']]
				if currentPlayer['username'] != currentGame.currentPlayer:
					# Check if it is the player's turn
					self.sendMessage("JAW/1.0 405 INVALID_MOVE \r\n\r\n", fileno)
					self.retransmits[fileno] = ["JAW/1.0 405 INVALID_MOVE \r\n\r\n"]
					return
				validMove = currentGame.place(int(requests[2]))
				if validMove:
					otherPlayer = currentGame.currentPlayer
					if debug:
						print "current Player:", currentPlayer
						print "opposing Playe:", otherPlayer
					self.retransmits[fileno] = ["JAW/1.0 200 OK \r\n PRINT:" + str(currentGame) + " \r\n\r\n"]
					self.retransmits[self.getSocket(otherPlayer)] = ["JAW/1.0 200 OK \r\n PRINT:" + str(currentGame) + " \r\n\r\n"]
					self.broadcast("JAW/1.0 200 OK \r\n PRINT:" + str(currentGame) + " \r\n\r\n", [fileno, self.getSocket(otherPlayer)])
					results = currentGame.gameFinished()
					if results != None:
						# Game finished
						self.retransmits[fileno] .append("JAW/1.0 201 GAME_END \r\n WINNER:" + results + " \r\n\r\n")
						self.retransmits[self.getSocket(otherPlayer)].append("JAW/1.0 201 GAME_END \r\n WINNER:" + results + " \r\n\r\n")
						self.broadcast("JAW/1.0 201 GAME_END \r\n WINNER:" + results + " \r\n\r\n", [fileno, self.getSocket(otherPlayer)])
						self.endGame(currentPlayer['gameId'], currentPlayer, self.players[self.getSocket(otherPlayer)])
						time.sleep(3) # Temporarily pause server to allow client sufficient time to receive data correctly. ePoll sends data too fast.

						#Automatically start a new game
						otherPlayer = self.getPlayer(otherPlayer)
						game = self.createGame(otherPlayer, currentPlayer)
						self.retransmits[fileno] = ["JAW/1.0 200 OK \r\n OTHER_PLAYER:" + otherPlayer['username'] + " \r\n\r\n"]
						self.retransmits[fileno].append("JAW/1.0 200 OK \r\n PRINT:" + str(game) + " \r\n\r\n")
						self.retransmits[fileno].append("JAW/1.0 200 OK \r\n PLAYER:" + game.currentPlayer + " \r\n\r\n")
						self.retransmits[self.getSocket(otherPlayer['username'])] = ["JAW/1.0 200 OK \r\n OTHER_PLAYER:" + currentPlayer['username'] + " \r\n\r\n", "JAW/1.0 200 OK \r\n PRINT:" + str(game) + " \r\n\r\n", "JAW/1.0 200 OK \r\n PLAYER:" + game.currentPlayer + " \r\n\r\n"]
						self.sendMessage("JAW/1.0 200 OK \r\n OTHER_PLAYER:" + otherPlayer['username'] + " \r\n\r\n", fileno)
						self.sendMessage("JAW/1.0 200 OK \r\n OTHER_PLAYER:" + currentPlayer['username'] + " \r\n\r\n", self.getSocket(otherPlayer['username']))
						self.broadcast("JAW/1.0 200 OK \r\n PRINT:" + str(game) + " \r\n\r\n", [fileno, self.getSocket(otherPlayer['username'])])
						self.broadcast("JAW/1.0 200 OK \r\n PLAYER:" + game.currentPlayer + " \r\n\r\n", [fileno, self.getSocket(otherPlayer['username'])])
					else:
						# Game not finished
						self.broadcast("JAW/1.0 200 OK \r\n PLAYER:" + currentGame.currentPlayer + " \r\n\r\n", [fileno, self.getSocket(otherPlayer)])
						self.retransmits[fileno] .append("JAW/1.0 200 OK \r\n PLAYER:" + currentGame.currentPlayer + " \r\n\r\n")
						self.retransmits[self.getSocket(otherPlayer)] .append("JAW/1.0 200 OK \r\n PLAYER:" + currentGame.currentPlayer + " \r\n\r\n")
				else:
					self.sendMessage("JAW/1.0 405 INVALID_MOVE \r\n\r\n", fileno)
					self.retransmits[fileno] = ["JAW/1.0 405 INVALID_MOVE \r\n\r\n"]
		# EXIT
		elif requests[1] == "EXIT":
			if len(requests) < 2:
				self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
				self.retransmits[fileno] = ["JAW/1.0 400 ERROR \r\n\r\n"]
			else:
				self.removePlayer(fileno)
		# RETRANSMIT
		elif requests[1] == "RETRANSMIT":
			if len(requests) < 2:
				# Invalid command usage
				self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
			else:
				# Retransmit last set of consecutive messages sent by the server when performing one action
				for v in self.retransmits[fileno]:
					self.sendMessage(v, fileno)
		else:
			# Invalid command specified
			self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
			self.retransmits[fileno] = ["JAW/1.0 400 ERROR \r\n\r\n"]
		return


	'''helper methods'''
	def getSocket(self, username):
		'''
		Gets the socket of player with id of username
		@param username id of the player
		'''
		for key, value in self.players.iteritems():
			if username == value['username']:
				return key
		return None

	def getPlayer(self, username):
		'''
		Gets the player with id of username
		@param username id of the player
		'''
		for key, value in self.players.iteritems():
			if username == value['username']:
				return value
		return None

server = Server()

if __name__ == '__main__':
	debug = True
	try:
		while True:
			events = epoll.poll(1)
			for fileno, event in events:
				if fileno == serverSocket.fileno():
					# new epoll connection
					connectionSocket, addr = serverSocket.accept()
					connectionSocket.setblocking(0)
					epoll.register(connectionSocket.fileno(), select.EPOLLIN | select.EPOLLET)
					server.addConnection(connectionSocket)
				elif event & select.EPOLLIN:
					# ePoll connection has incoming data to read
					server.checkRequestProtocol(fileno)
				elif event & (select.EPOLLERR | select.EPOLLHUP):
					# ePoll connection has an error
					server.removePlayer(fileno)
	finally:
		epoll.unregister(serverSocket.fileno())
		epoll.close()
		serverSocket.close()
#scp -P 130 server.py jijli@allv25.all.cs.stonybrook.edu:~
#ssh -p 130 -o ServerAliveInterval=60 jijli@allv25.all.cs.stonybrook.edu