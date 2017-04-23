#import socket module
#Jia Li 109843894
from socket import *
import select, uuid, board, jaw_enums, json
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
			if username == value.username:
				return value.status
		return False

	def playerExists(self, username):
		'''
		Checks if player with a user id of username exists
		@param username User id of user to check for
		@return True if player exists. False otherwise.
		'''
		for key, value in self.players.iteritems():
			if username == value.username:
				return True
		return False

	def getAvailablePlayers(self):
		'''
		Returns the list of all available players
		@return List of all available players
		'''
		names = []
		for key, value in self.players.iteritems():
			names.append(value.username) if value.status == True
		return names

	def removePlayer(self, username):
		'''
		Removes the player with a user id of username
		@param usernamed User id of user to remove
		'''
		for key, value in self.players.iteritems():
			if username == value.username:
				#close connection and remove user
				return
		return

	def addPlayer(self, connection, player):
		'''
		Adds player to the server
		@param connection Socket connection associated with player
		@param player Player to add to the server
		'''
		#Store epoll connection and player username in sockets dictionary
		self.players[connection.fileno()] = player

	def createGame(self, connection, p1, p2):
		'''
		Create game with 2 players
		@param connection Connection associated with p1 or p2
		@param p1 Player 1
		@param p2 Player 2
		'''
		gameId = uuid.uuid4().hex
		newBoard = None
		if p1.timeLoggedIn <= p2.timeLoggedIn:
			newBoard = Board(p1, p2, p1)
		else:
			newBoard = Board(p1, p2, p2)
		self.games[gameId] = newBoard
		return

	def endGame(self, gameID):
		'''
		Ends the game
		@param gameID Game ID of the game to end
		'''
		return

	def sendMessage(self, message, connection):
		'''
		Sends a message to the client
		@param message Message to send
		@param connection Sock connection to send message to
		'''
		return

	def checkProtocol(self, connection):
		'''
		Checks the protocol
		@param connection Incoming socket connection
		'''
		return

server = Server()

if __name__ == '__main__':
	try:
		while True:
			events = epoll.poll(1)
			for fileno, event in events:
				if fileno == serverSocket.fileno():
					# new epoll connection
					connectionSocket, addr = serverSocket.accept()
					connectionSocket.setBlocking(0)
					epoll.register(connectionSocket.fileno(), select.EPOLLIN)
					server.createGame(connection)
				elif event & select.EPOLLIN:
					#receive client data on epoll connection
					server.checkProtocol(connection)
				elif event & select.EPOLLOUT:
					#send server response on epoll connection
					connections[fileno].send("Hello")
	finally:
		epoll.unregister(serversocket.fileno())
		epoll.close()
		serversocket.close()
