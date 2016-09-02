import base64, random, string

def b64decode(data):
	"""Decode base64, padding being optional.

	:param data: Base64 data as an ASCII byte string
	:returns: The decoded byte string.

	"""
	missing_padding = len(data) % 4
	if missing_padding != 0:
		data += b'='* (4 - missing_padding)
	return base64.b64decode(data)
	
def b64encode(s):
	return base64.b64encode(s)

def randomword():
	"""Create a random string of 20 characters"""
	return ''.join(random.choice(string.lowercase) for i in range(20))