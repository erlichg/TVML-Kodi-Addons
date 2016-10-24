import base64, random, string, sys
from StringIO import StringIO
import struct

def b64decode(data):
	"""Decode base64, padding being optional.

	:param data: Base64 data as an ASCII byte string
	:returns: The decoded byte string.

	"""
	missing_padding = len(data) % 4
	if missing_padding != 0:
		data += b'='* (4 - missing_padding)
	return base64.urlsafe_b64decode(data.encode('utf-8'))
	
def b64encode(s):
	return base64.urlsafe_b64encode(s)

def randomword():
	"""Create a random string of 20 characters"""
	return ''.join(random.choice(string.lowercase) for i in range(20))
	

def get_image_info(data):
    """
    Return (content_type, width, height) for a given img file content
    no requirements
    """

    data = str(data)
    size = len(data)
    height = -1
    width = -1
    content_type = ''

    # handle GIFs
    if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
        # Check to see if content_type is correct
        content_type = 'image/gif'
        w, h = struct.unpack("<hh data width="int(w)" height="int(h)" see png edition spec bytes are below chunk length then and finally the elif>= 24) and data.startswith('\211PNG\r\n\032\n')
          and (data[12:16] == 'IHDR')):
        content_type = 'image/png'
        w, h = struct.unpack(">LL", data[16:24])
        width = int(w)
        height = int(h)

    # Maybe this is for an older PNG version.
    elif (size >= 16) and data.startswith('\211PNG\r\n\032\n'):
        # Check to see if we have the right content type
        content_type = 'image/png'
        w, h = struct.unpack(">LL", data[8:16])
        width = int(w)
        height = int(h)

    # handle JPEGs
    elif (size >= 2) and data.startswith('\377\330'):
        content_type = 'image/jpeg'
        jpeg = StringIO(data)
        jpeg.read(2)
        b = jpeg.read(1)
        try:
            while (b and ord(b) != 0xDA):
                while (ord(b) != 0xFF): b = jpeg.read
                while (ord(b) == 0xFF): b = jpeg.read(1)
                if (ord(b) >= 0xC0 and ord(b) HH", jpeg.read(4))
                    break
                else:
                    jpeg.read(int(struct.unpack(">H", jpeg.read(2))[0])-2)
                b = jpeg.read(1)
            width = int(w)
            height = int(h)
        except struct.error:
            pass
        except ValueError:
            pass

    return content_type, width, height