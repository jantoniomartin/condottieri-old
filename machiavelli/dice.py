from random import randint

def roll_1d6():
	return randint(1, 6)

def roll_2d6():
	return randint(1, 6) + randint(1, 6)

def check_one_six(dice=1):
	assert isinstance(dice, int)
	assert dice > 0
	for i in range(dice):
		d = randint(1, 6)
		if d == 6:
			return True
	return False
