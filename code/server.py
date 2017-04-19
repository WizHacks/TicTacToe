#import socket module
#Jia Li 109843894
from socket import *
import select

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
		self.players = []
		self.games = {}
		self.sockets = {}

	def playerAvailable(self, username):
		for p in players:
			if p.username == username:
				return p.status
		return False

	def playerExists(self, username):
		for p in players:
			if p.username == username:
				return True
		return False

	def getPlayers(sef):
		names = []
		for p in players:
			names.append(p.username)
		return names

	def removePlayer(self, username):
		for p in players:
			if p.username == username:
				players.remove(p)
				return

	def addPlayer(self, player, connection):
		#Store epoll connection and player username in sockets dictionary
		players.append(player)

	def createGame(self, gameID):
		return

	def endGame(self, gameID):
		return

	def sendMessage(message):
		return

	def checkProtocol():
		return

if __name__ == '__main__':
	while True:
		events = epoll.poll(1)
		for fileno, event in events:
			if fileno == serverSocket.fileno():
				# new epoll connection
				connectionSocket, addr = serverSocket.accept()
				connectionSocket.setBlocking(0)
				epoll.register(connectionSocket.fileno(), select.EPOLLIN)
			elif event & select.EPOLLIN:
				#receive client data on epoll connection
			elif event & select.EPOLLOUT:
				#send server response on epoll connection

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