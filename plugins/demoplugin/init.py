from Plugin import Item
import time

def main(bridge, url):
	if not url:
		return [Item('1', 'movies'), Item('2', 'tv'), Item('3', 'dialogs')]
	if url == '1':
		return [Item('11', 'movie1', 'sub-title of movie1', 'https://pixabay.com/static/uploads/photo/2016/07/29/18/42/spider-1555216_960_720.jpg', 'A lot of details about movie1', {})]
	if url == '2':
		return [Item('21', 'tv1', 'sub-title of tv1', 'https://pixabay.com/static/uploads/photo/2016/07/24/23/35/blackberries-1539540_960_720.jpg', 'A lot of details about tv1', {})]
	if url == '11':
		bridge.play("https://devimages.apple.com.edgekey.net/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8") #test stream taken from VLC site
		return
	if url == '21':
		bridge.play('http://satfeedhunter.nl/2.mp4') #test stream taken from VLC site
		return
	if url == '3':
		return [Item('31', 'input'), Item('32', 'progress'), Item('33', 'select')]
	if url == '31':
		ans = bridge.inputdialog('my title', 'hello world')
		if ans:
			bridge.alertdialog('response', 'User entered: {}'.format(ans))
		return
	if url == '32':
		bridge.progressdialog('progress title', 'progress text')
		time.sleep(1)
		if bridge.isprogresscanceled():
			return
		bridge.updateprogressdialog('0.2', 'new progress text')
		time.sleep(1)
		if bridge.isprogresscanceled():
			return
		bridge.updateprogressdialog('0.5', 'new progress text')
		time.sleep(1)
		if bridge.isprogresscanceled():
			return
		bridge.updateprogressdialog('0.8', 'new progress text')
		time.sleep(1)
		if bridge.isprogresscanceled():
			return
		bridge.closeprogress()
		return
	if url == '33':
		ans = bridge.selectdialog('select from list', [Item('41', 'item 1'), Item('42', 'item 2')])
		bridge.alertdialog('select ended', 'user selected item {}'.format(ans))
		return
	