class JAWMethods(object):
	LOGIN 				= "LOGIN"
	PLACE 				= "PLACE"
	PLAY 				= "PLAY"
	EXIT 				= "EXIT"
	WHO 				= "WHO"
	RETRANSMIT			= "RETRANSMIT"

class JAWResponses(object):
	PRINT 				= "PRINT"
	PLAYER 				= "PLAYER"
	WINNER 				= "WINNER"
	PLAYERS 			= "PLAYERS"
	QUIT 				= "QUIT"
	OTHER_PLAYER		= "OTHER_PLAYER"

class JAWStatuses(object):
	OK 					= "OK"
	ERROR 				= "ERROR"
	USERNAME_TAKEN 		= "USERNAME_TAKEN"
	USER_BUSY 			= "USER_BUSY"
	USER_NOT_FOUND 		= "USER_NOT_FOUND"
	INVALID_MOVE 		= "INVALID_MOVE"
	GAME_END 			= "GAME_END"
	USER_QUIT 			= "USER_QUIT"
	PLEASE_WAIT			= "PLEASE_WAIT"

class JAWStatusNum(object):
	OK_NUM 				= "200"
	ERROR_NUM 			= "400"
	USERNAME_TAKEN_NUM 	= "401"
	USER_BUSY_NUM 		= "402"
	USER_NOT_FOUND_NUM 	= "403"
	INVALID_MOVE_NUM 	= "405"
	GAME_END_NUM 		= "201"
	USER_QUIT_NUM 		= "202"
	PLEASE_WAIT_NUM		= "406"

class JAWMisc(object):
	CRNLCRNL 			= "\r\n\r\n"
	CRNL 				= "\r\n"
	JAW 				= "JAW/1.0"

if __name__ == "__main__":
	request 			= JAWMethods.LOGIN
	print request
	response 			= JAWResponses.PLAYERS
	print response
