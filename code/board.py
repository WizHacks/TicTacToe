from __future__ import print_function

class Board(object):
	def __init__(self, player1, player2, currentPlayer):
		self.player1 = player1							# the first player
		self.player2 = player2							# the second player
		self.currentPlayer = currentPlayer				# current player
		self.observers=[]								# additional players obserivng
		self.board = [0, 0, 0, 0, 0, 0, 0, 0, 0]		# board as specified in help
														# 0- empty, 1-player1, 2-player2
	def __str__(self):
		'''
		the 'toString' method for our Board class
		@return String representation of the Tic Tac Toc game board
		'''
		boardString = ""
		for i in range(0, len(self.board)):
			if self.board[i] == 0:
				boardString += "."
			else:
				boardString += "X" if self.board[i] == 1 else "O"
		return boardString

	def gameFinished(self):
		'''
		tests to see if the game has finished
		@return String Winner if there is one. Draw if there is one. Otherwise, None.
		'''
		winner = 0
		# first row
		if self.board[0] != 0 and self.board[0] == self.board[1] and self.board[0] == self.board[2]:
			winner = self.board[0]
		# second row
		if self.board[3] != 0 and self.board[3] == self.board[4] and self.board[3] == self.board[5]:
			winner = self.board[3]
		# third row
		if self.board[6] != 0 and self.board[6] == self.board[7] and self.board[6] == self.board[8]:
			winner = self.board[6]

		# first column
		if self.board[0] != 0 and self.board[0] == self.board[3] and self.board[0] == self.board[6]:
			winner = self.board[0]
		# second column
		if self.board[1] != 0 and self.board[1] == self.board[4] and self.board[1] == self.board[7]:
			winner = self.board[1]
		# third column
		if self.board[2] != 0 and self.board[2] == self.board[5] and self.board[2] == self.board[8]:
			winner = self.board[2]

		# down diagonal
		if self.board[0] != 0 and self.board[0] == self.board[4] and self.board[0] == self.board[8]:
			winner = self.board[0]
		# up diagonal
		if self.board[2] != 0 and self.board[2] == self.board[4] and self.board[2] == self.board[6]:
			winner = self.board[2]

		if winner == 0 and self.board[0] * self.board[1] * self.board[2] * self.board[3] * self.board[4] * self.board[5] * self.board[6] * self.board[7] * self.board[8] > 0:
			print("This game is a draw")
			return "None"
		if winner != 0:
			print((self.player1 if winner != 1 else self.player2) + " has won")
			return self.player1 if winner != 1 else self.player2
		return None

	def place(self, move):
		'''
		places the board piece in spcified position, places symbol based on currentPlayer
		@param move The position of the game board
		@return boolean True if a move was placed. Otherwise, false.
		'''
		if self.isValidMove(move):
			self.board[move - 1] = 1 if self.player1 == self.currentPlayer else 2
			self.currentPlayer = self.player2 if self.player1 == self.currentPlayer else self.player1
			self.gameFinished()
			return True
		else:
			return False

	def isValidMove(self, move):
		'''
		determines if the specified location is valid
		@param move The position of the game board
		@return boolean True if move is valid. Otherwise, false
		'''
		if move > 9 or move < 0 or self.board[move-1] != 0:
			print("Illegal Move")
			return False
		return True

	# def addObserver(self, observer):
	# 	print(observer + " has started watching the game")
	# 	self.observers.extend([observer])

	# def removeObserver(self, observer):
	# 	if observer in self.observers:
	# 		print(observer + " has left watching the game")
	# 		self.observers.remove(observer)
	# 	else:
	# 		print(observer + " is already not observing")

	# def comment(self, player, comment):
	# 	print(player + ": " + comment)

	def debug(self):
		print("\n\nDEBUG\nPlayer 1: " + self.player1)
		print("Player 2: " + self.player2)
		print("C Player: " + self.currentPlayer)
		print("Observers: ", end='')
		for i in self.observers:
			print(i + " ", end='')
		print("\nBoard allignment: ")
		#print self
