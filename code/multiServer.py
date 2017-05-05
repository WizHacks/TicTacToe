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
			try:
				self.sendMessage("JAW/1.0 202 USER_QUIT \r\n QUIT:" + currentPlayer['username'] + " \r\n\r\n", fileno)
			except Exception:
				# Player closed the connection before server can send message
				if debug:
					print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + "\t" + currentPlayer['username'] + " at connection " + str(fileno) + " closed before QUIT message sent."
			fNum = fileno

			# Remove player and its corresponding ePoll connection
			epoll.unregister(fileno)
			self.connections[fNum].close()
			del self.connections[fNum]
			del self.players[fNum]
			del self.retransmits[fNum]
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
			del self.retransmits[fNum]
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
		newBoard = board.Board(p1['username'], p2['username'], p1['username'])
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

	def getGames(self):
		'''
		Get all current games with players in server
		@return String representation of all games. gameID-player1,player2;gameId-player1,player2;...
		'''
		output = ""
		for key, value in self.games.iteritems():
			output += str(key) + "-" + value.player1 + "," + value.player2 + ";"
		return output[:(len(output)-1)]

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

	def processRequestProtocol(self, fileno):
		'''
		Processes the request protocol
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
			if len(requests) < 3:
				# Invalid command usage
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
					self.sendMessage("JAW/1.0 200 OK \r\n\r\n", fileno)
					self.retransmits[fileno] = ["JAW/1.0 200 OK \r\n\r\n"]
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
					print currentPlayer
					print otherPlayer
					self.broadcast("JAW/1.0 200 OK \r\n PRINT:" + str(currentGame) + " \r\n\r\n", [fileno, self.getSocket(otherPlayer)])
					self.retransmits[fileno] = ["JAW/1.0 200 OK \r\n PRINT:" + str(currentGame) + " \r\n\r\n"]
					self.retransmits[self.getSocket(otherPlayer)] = ["JAW/1.0 200 OK \r\n PRINT:" + str(currentGame) + " \r\n\r\n"]
					results = currentGame.gameFinished()
					if results != None:
						# Game finished
						self.retransmits[fileno].append("JAW/1.0 201 GAME_END \r\n WINNER:" + results + " \r\n\r\n")
						self.retransmits[self.getSocket(otherPlayer)].append("JAW/1.0 201 GAME_END \r\n WINNER:" + results + " \r\n\r\n")
						self.broadcast("JAW/1.0 201 GAME_END \r\n WINNER:" + results + " \r\n\r\n", [fileno, self.getSocket(otherPlayer)])
						self.endGame(currentPlayer['gameId'], currentPlayer, self.players[self.getSocket(otherPlayer)])
					else:
						# Game not finished
						self.broadcast("JAW/1.0 200 OK \r\n PLAYER:" + currentGame.currentPlayer + " \r\n\r\n", [fileno, self.getSocket(otherPlayer)])
						self.retransmits[fileno].append("JAW/1.0 200 OK \r\n PLAYER:" + currentGame.currentPlayer + " \r\n\r\n")
						self.retransmits[self.getSocket(otherPlayer)].append("JAW/1.0 200 OK \r\n PLAYER:" + currentGame.currentPlayer + " \r\n\r\n")
				else:
					self.sendMessage("JAW/1.0 405 INVALID_MOVE \r\n\r\n", fileno)
					self.retransmits[fileno] = ["JAW/1.0 405 INVALID_MOVE \r\n\r\n"]
		# PLAY
		elif requests[1] == "PLAY":
			if len(requests) < 3:
				# Invalid command usage
				self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
				self.retransmits[fileno] = ["JAW/1.0 400 ERROR \r\n\r\n"]
			else:
				otherPlayer = self.getPlayer(requests[2])
				if otherPlayer == None or otherPlayer['username'] == self.players[fileno]['username']:
					# Checks if player is playing someone else who exists. You cannot play yourself
					self.sendMessage("JAW/1.0 403 USER_NOT_FOUND \r\n\r\n", fileno)
					self.retransmits[fileno] = ["JAW/1.0 403 USER_NOT_FOUND \r\n\r\n"]
				else:
					if self.playerAvailable(otherPlayer['username']):
						# Other player is not busy. Now set up game
						game = self.createGame(self.players[fileno], otherPlayer)
						self.retransmits[fileno] = ["JAW/1.0 200 OK \r\n PRINT:" + str(game) + " \r\n\r\n", "JAW/1.0 200 OK \r\n PLAYER:" + game.currentPlayer + " \r\n\r\n"]
						self.retransmits[self.getSocket(otherPlayer['username'])] = ["JAW/1.0 200 OK \r\n PRINT:" + str(game) + " \r\n\r\n", "JAW/1.0 200 OK \r\n PLAYER:" + game.currentPlayer + " \r\n\r\n"]
						self.broadcast("JAW/1.0 200 OK \r\n PRINT:" + str(game) + " \r\n\r\n", [fileno, self.getSocket(otherPlayer['username'])])
						self.broadcast("JAW/1.0 200 OK \r\n PLAYER:" + game.currentPlayer + " \r\n\r\n", [fileno, self.getSocket(otherPlayer['username'])])
					else:
						# Other player is busy
						self.sendMessage("JAW/1.0 402 USER_BUSY \r\n\r\n", fileno)
						self.retransmits[fileno] = ["JAW/1.0 402 USER_BUSY \r\n\r\n"]
		# EXIT
		elif requests[1] == "EXIT":
			if len(requests) < 2:
				# Invalid command usage
				self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
			else:
				self.removePlayer(fileno)
		# WHO
		elif requests[1] == "WHO":
			if len(requests) < 2:
				# Invalid command usage
				self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
			else:
				# Gets list of all available players. Remove current player from list
				currentPlayer = self.players[fileno]
				players = self.getAvailablePlayers()
				data = ""
				for p in players:
					if p != currentPlayer['username']:
						data += p + ","
				info = "JAW/1.0 200 OK \r\n PLAYERS:" + data[:(len(data)-1)] + " \r\n\r\n"
				print info
				self.retransmits[fileno] = [info]
				self.sendMessage(info, fileno)
		# GAMES
		elif requests[1] == "GAMES":
			if len(requests) < 2:
				# Invalid command usage
				self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
			else:
				# Gets list of all current Games
				games = self.getGames()
				self.sendMessage("JAW/1.0 200 OK \r\n GAMES:" + games + " \r\n\r\n", fileno)
				self.retransmits[fileno] = ["JAW/1.0 200 OK \r\n GAMES:" + games + " \r\n\r\n"]
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
	debug = False # False-turn off debugging/logging		True- Turn on debugging/logging
	try:
		while True:
			events = epoll.poll(0.01)
			for fileno, event in events:
				if fileno == serverSocket.fileno():
					# new epoll connection
					connectionSocket, addr = serverSocket.accept()
					connectionSocket.setblocking(0)
					epoll.register(connectionSocket.fileno(), select.EPOLLIN | select.EPOLLET)
					server.addConnection(connectionSocket)
				elif event & select.EPOLLIN:
					# ePoll connection has incoming data to read
					server.processRequestProtocol(fileno)
				elif event & (select.EPOLLERR | select.EPOLLHUP):
					# ePoll connection has an error
					server.removePlayer(fileno)
	finally:
		epoll.unregister(serverSocket.fileno())
		epoll.close()
		serverSocket.close()
#scp -P 130 code/* jijli@allv25.all.cs.stonybrook.edu:~/project/
#ssh -p 130 -o ServerAliveInterval=60 jijli@allv25.all.cs.stonybrook.edu