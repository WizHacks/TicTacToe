from socket import *
import select, uuid, board, json, time
#import player

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverPort = 9347
serverSocket.bind(('', serverPort))
serverSocket.listen(1)
serverSocket.setblocking(0)

epoll = select.epoll()
epoll.register(serverSocket.fileno(), select.EPOLLIN)

class Server(object):
	def __init__(self):
		self.players = {}
		self.games = {}
		self.connections = {}
		self.retransmits = {}

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
			currentPlayer = self.players[fileno]
		except Exception:
			fNum = fileno
			epoll.unregister(fileno)
			self.connections[fNum].close()
			del self.connections[fNum]
			return
		# Player is not in game
		if currentPlayer['status'] == True:
			self.sendMessage("JAW/1.0 202 USER_QUIT \r\n QUIT:" + currentPlayer['username'] + " \r\n\r\n", fileno)
			fNum = fileno
			epoll.unregister(fileno)
			self.connections[fNum].close()
			del self.connections[fNum]
			try:
				del self.players[fNum]
			except Exception:
				print "Username was taken. No big deal."
		# Player is in game
		else:
			if currentPlayer['gameId'] == None:
				epoll.modify(fileno, select.EPOLLIN | select.EPOLLET)
				return
			currentGame = self.games[currentPlayer['gameId']]
			otherPlayer = currentGame.player2 if currentPlayer['username'] != currentGame.player2 else currentGame.player1
			del self.games[currentPlayer['gameId']]
			self.retransmits[self.getSocket(otherPlayer)] = ["JAW/1.0 202 USER_QUIT \r\n QUIT:" + currentPlayer['username'] + " \r\n\r\n", "JAW/1.0 201 GAME_END \r\n WINNER:" + otherPlayer + " \r\n\r\n"]
			self.broadcast("JAW/1.0 202 USER_QUIT \r\n QUIT:" + currentPlayer['username'] + " \r\n\r\n", [fileno, self.getSocket(otherPlayer)])
			self.broadcast("JAW/1.0 201 GAME_END \r\n WINNER:" + otherPlayer + " \r\n\r\n", [fileno, self.getSocket(otherPlayer)])
			otherPlayer = self.getPlayer(otherPlayer)
			otherPlayer['gameId'] = None
			otherPlayer['status'] = True
			fNum = fileno
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
		gameId = uuid.uuid4().hex
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
		@param connection Sockwt connection to send message to
		'''
		epoll.modify(fileno, select.EPOLLOUT)
		self.connections[fileno].send(message)
		epoll.modify(fileno, select.EPOLLIN | select.EPOLLET)
		print "Sent: " + message #TO DELETE
		return


	def broadcast(self, message, connections):
		'''
		Broadcasts message to everyone
		@param message Message to send
		@param connections Socket connections to send message to
		'''
		for c in connections:
			self.sendMessage(message, c)
		return

	def checkRequestProtocol(self, fileno):
		'''
		Checks the request protocol
		@param fileno Incoming socket connection file descriptor
		'''
		connection = self.connections[fileno]
		request = connection.recv(1024).decode()
		print request#TO DELETE
		#Check for errors
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
			print "Number of players: " + str(len(self.connections))
			if len(requests) < 3 or len(self.connections) > 2:
				self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
				fNum = fileno
				epoll.unregister(fileno)
				self.connections[fNum].close()
				del self.connections[fNum]
			else:
				newPlayer = request[request.find(" ")+6 : len(request)]
				try:
					player = json.loads(newPlayer)
				except Exception:
					self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
					fNum = fileno
					epoll.unregister(fileno)
					self.connections[fNum].close()
					del self.connections[fNum]
					return
				if self.playerExists(player['username']):
					self.sendMessage("JAW/1.0 401 USERNAME_TAKEN \r\n\r\n", fileno)
					self.retransmits[fileno] = ["JAW/1.0 401 USERNAME_TAKEN \r\n\r\n"]
				else:
					self.addPlayer(connection, player)
					#self.sendMessage("JAW/1.0 200 OK \r\n\r\n", fileno)
					#self.retransmits[fileno] = ["JAW/1.0 200 OK \r\n\r\n"]
					if len(self.connections) == 2:
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
						self.sendMessage("JAW/1.0 406 PLEASE_WAIT \r\n\r\n", fileno)
						self.retransmits[fileno] = ["JAW/1.0 406 PLEASE_WAIT \r\n\r\n"]
		# PLACE
		elif requests[1] == "PLACE":
			if len(requests) < 3:
				self.sendMessage("JAW/1.0 400 ERROR \r\n\r\n", fileno)
				self.retransmits[fileno] = ["JAW/1.0 400 ERROR \r\n\r\n"]
			else:
				currentPlayer = self.players[fileno]
				if currentPlayer['gameId'] == 0 or currentPlayer['gameId'] == None:
					self.sendMessage("JAW/1.0 405 INVALID_MOVE \r\n\r\n", fileno)
					self.retransmits[fileno] = ["JAW/1.0 405 INVALID_MOVE \r\n\r\n"]
					return
				currentGame = self.games[currentPlayer['gameId']]
				if currentPlayer['username'] != currentGame.currentPlayer:
					self.sendMessage("JAW/1.0 405 INVALID_MOVE \r\n\r\n", fileno)
					self.retransmits[fileno] = ["JAW/1.0 405 INVALID_MOVE \r\n\r\n"]
					return
				validMove = currentGame.place(int(requests[2]))
				if validMove:
					otherPlayer = currentGame.currentPlayer
					print currentPlayer 
					print otherPlayer
					self.retransmits[fileno] = ["JAW/1.0 200 OK \r\n PRINT:" + str(currentGame) + " \r\n\r\n"]
					self.retransmits[self.getSocket(otherPlayer)] = ["JAW/1.0 200 OK \r\n PRINT:" + str(currentGame) + " \r\n\r\n"]
					self.broadcast("JAW/1.0 200 OK \r\n PRINT:" + str(currentGame) + " \r\n\r\n", [fileno, self.getSocket(otherPlayer)])
					results = currentGame.gameFinished()
					if results != None:
						self.retransmits[fileno] .append("JAW/1.0 201 GAME_END \r\n WINNER:" + results + " \r\n\r\n")
						self.retransmits[self.getSocket(otherPlayer)].append("JAW/1.0 201 GAME_END \r\n WINNER:" + results + " \r\n\r\n")
						self.broadcast("JAW/1.0 201 GAME_END \r\n WINNER:" + results + " \r\n\r\n", [fileno, self.getSocket(otherPlayer)])
						self.endGame(currentPlayer['gameId'], currentPlayer, self.players[self.getSocket(otherPlayer)])
						time.sleep(3)
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
			for v in self.retransmits[fileno]:
				self.sendMessage(v, fileno)
		else:
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
					#receive client data on epoll connection
					print "Receiving data from fileno: " + str(fileno)
					server.checkRequestProtocol(fileno)
				elif event & (select.EPOLLERR | select.EPOLLHUP):
					# fNum = fileno
					# epoll.unregister(fileno)
					# server.connections[fNum].close()
					# del server.connections[fNum]
					server.removePlayer(fileno)
	finally:
		epoll.unregister(serverSocket.fileno())
		epoll.close()
		serverSocket.close()
#scp -P 130 server.py jijli@allv25.all.cs.stonybrook.edu:~
#ssh -p 130 -o ServerAliveInterval=60 jijli@allv25.all.cs.stonybrook.edu