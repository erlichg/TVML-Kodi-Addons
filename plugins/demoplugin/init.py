from Plugin import Item

def main(bridge, url):
	if not url:
		return [Item('1', 'movies'), Item('2', 'tv'), Item('3', 'dialogs')]
	if url == '1':
		return [Item('11', 'movie1', 'sub-title of movie1', 'https://pixabay.com/static/uploads/photo/2016/07/29/18/42/spider-1555216_960_720.jpg', 'A lot of details about movie1', {})]
	if url == '2':
		return [Item('21', 'tv1', 'sub-title of tv1', 'https://pixabay.com/static/uploads/photo/2016/07/24/23/35/blackberries-1539540_960_720.jpg', 'A lot of details about tv1', {})]
	if url == '11':
		bridge.play('http://satfeedhunter.nl/3.mp4') #test stream taken from VLC site
		return
	if url == '21':
		bridge.play('http://satfeedhunter.nl/2.mp4') #test stream taken from VLC site
		return
	if url == '3':
		ans = bridge.inputdialog('my title', 'hello world')
		print ans
		if ans == '1':
			return [Item('11', 'movie1', 'sub-title of movie1', 'https://pixabay.com/static/uploads/photo/2016/07/29/18/42/spider-1555216_960_720.jpg', 'A lot of details about movie1', {})]
		if ans == '2':
			return [Item('21', 'tv1', 'sub-title of tv1', 'https://pixabay.com/static/uploads/photo/2016/07/24/23/35/blackberries-1539540_960_720.jpg', 'A lot of details about tv1', {})]
		return