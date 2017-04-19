class JAWMethods(object):
	LOGIN = "LOGIN"
	PLACE = "PLACE"
	PLAY = "PLAY"
	EXIT = "EXIT"
	WHO = "WHO"

class JAWResponses(object):
	PRINT = "PRINT"
	PLAYER = "PLAYER"
	WINNER = "WINNER"
	PLAYERS = "PLAYERS"
	QUIT = "QUIT"

class JAWStatuses(object):
	OK = "OK"
	ERROR = "ERROR"
	USERNAME_TAKEN = "USERNAME TAKEN"
	USER_BUSY = "USER BUSY"
	USER_NOT_FOUND = "USER NOT FOUND"
	INVALID_MOVE = "INVALID MOVE"
	GAME_END = "GAME END"
	USER_QUIT = "USER QUIT"

if __name__ == "__main__":
	request = JAWMethods.LOGIN
	print request
	response = JAWResponses.PLAYERS
	print response