#import socket module
#Jia Li 109843894
from socket import *
import select, uuid, board, player, jaw_enums, json

serverSocket = socket(AF_INET, SOCK_STREAM)
serversocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverPort = 9347
serverSocket.bind(('', serverPort))
serverSocket.listen(1)
serversocket.setblocking(0)
Server server = Server()

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
			if username == value.username
				return value.status
		return False

	def playerExists(self, username):
		'''
		Checks if player with a user id of username exists
		@param username User id of user to check for
		@return True if player exists. False otherwise.
		'''
		for key, value in self.players.iteritems():
			if username == value.username
				return True
		return False

	def getPlayers(sef):
		'''
		Returns the list of players
		@return List of players
		'''
		names = []
		for key, value in self.players.iteritems():
			names.append(value.username)
		return names

	def removePlayer(self, username):
		for key, value in self.players.iteritems():
			if username == value.username:
				#close connection and remove user
		return

	def addPlayer(self, connection, player):
		#Store epoll connection and player username in sockets dictionary
		self.players[connection.fileno()] = player

	def createGame(self, connection, p1, p2):
		gameId = uuid.uuid4().hex
		newBoard = None
		if p1.timeLoggedIn <= p2.timeLoggedIn:
			newBoard = Board(p1, p2, p1)
		else:
			newBoard = Board(p1, p2, p2)
		self.games[gameId] = newBoard
		return

	def endGame(self, gameID):
		return

	def sendMessage(self, message, connection):
		return

	def checkProtocol(self, connection):
		return

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
				elif event & select.EPOLLOUT:
					#send server response on epoll connection
	finally:
		epoll.unregister(serversocket.fileno())
		epoll.close()
		serversocket.close()

# while True:
# 	#Establish the connection
# 	print 'Ready to serve...'
# 	connectionSocket, addr = serverSocket.accept()
# 	try:
# 		message = connectionSocket.recv(1024)
# 		filename = message.split()[1]
# 		f = open(filename[1:])
# 		outputdata = f.read()
# 		#Send one HTTP header line into socket
# 		#Fill in start
# 		connectionSocket.send('\nHTTP/1.1 200 OK\n\n')
# 		#Fill in end
# 		#Send the content of the requested file to the client
# 		for i in range(0, len(outputdata)):
# 			connectionSocket.send(outputdata[i])
# 		connectionSocket.close()
# 	except IOError:
# 		#Send response message for file not found
# 		#Fill in start
# 		connectionSocket.send('\nHTTP/1.1 404 Not Found\n\n')
# 		#Fill in end
# 		#Close client socket
# 		#Fill in start
# 		connectionSocket.close()
# 		#Fill in end
# serverSocket.close()