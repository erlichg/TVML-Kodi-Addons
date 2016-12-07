from Plugin import Item
import time
import kodi_utils

def main(bridge, url):
	if not url:
		return [Item('1', 'movies'), Item('2', 'tv'), Item('3', 'dialogs')]
	if url == '1':
		return [Item('11', 'movie1', 'sub-title of movie1', 'https://pixabay.com/static/uploads/photo/2016/07/29/18/42/spider-1555216_960_720.jpg', 'A lot of details about movie1', {})]
	if url == '2':
		return [Item('21', 'tv1', 'sub-title of tv1', 'https://pixabay.com/static/uploads/photo/2016/07/24/23/35/blackberries-1539540_960_720.jpg', 'A lot of details about tv1', {})]
	if url == '11':
		def f(time):
			print 'in addon, player stop at {}'.format(time)
		
		bridge.play("https://devimages.apple.com.edgekey.net/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8", stop_completion=f)
		return
	if url == '21':
		def f(time):
			print 'detected player stop at {}'.format(time)		
		bridge.play('http://satfeedhunter.nl/2.mp4', stop_completion=f)
		return
	if url == '3':
		return [Item('31', 'input'), Item('32', 'progress'), Item('33', 'select'), Item('34', 'form'), Item('35', 'test')]
	if url == '31':
		ans = bridge.inputdialog('my title', 'hello world')
		if ans:
			bridge.alertdialog('response', 'User entered: {}'.format(ans))
		return
	if url == '32':
		bridge.progressdialog('progress title', 'progress text \n second line')
		time.sleep(0.5)
		if bridge.isprogresscanceled():
			return
		bridge.updateprogressdialog('0.2', 'new progress text \n new second line')
		time.sleep(0.5)
		if bridge.isprogresscanceled():
			return
		bridge.updateprogressdialog('0.5', 'new progress text')
		time.sleep(0.5)
		if bridge.isprogresscanceled():
			return
		bridge.updateprogressdialog('0.8', 'new progress text')
		time.sleep(0.5)
		if bridge.isprogresscanceled():
			return
		bridge.closeprogress()
		
		bridge.progressdialog('progress title2', 'progress text \n second line')
		time.sleep(0.5)
		if bridge.isprogresscanceled():
			return
		bridge.updateprogressdialog('0.2', 'new progress text \n new second line')
		time.sleep(0.5)
		if bridge.isprogresscanceled():
			return
		bridge.updateprogressdialog('0.5', 'new progress text')
		time.sleep(0.5)
		if bridge.isprogresscanceled():
			return
		bridge.updateprogressdialog('0.8', 'new progress text')
		time.sleep(0.5)
		if bridge.isprogresscanceled():
			return
		bridge.closeprogress()
		
		return [Item('55', 'bah')]
	if url == '33':
		ans = bridge.selectdialog('select from list', list_=[Item('41', 'item 1'), Item('42', 'item 2')])
		bridge.alertdialog('select ended', 'user selected item {}'.format(ans))
		return
	if url == '34':
		ans = bridge.formdialog('hello', sections={'section 1':[{'type':'textfield', 'label':'label1', 'value':'hello world', 'description':'desc', 'placeholder':'place holder'}, {'type':'yesno', 'label':'label2', 'value':False}, {'type':'selection', 'label':'label3', 'value':'choice1', 'choices':['choice1', 'choice2', 'choice3']}], 'section 2':[{'type':'textfield', 'label':'label4', 'value':''}]}, cont=True)
		bridge.alertdialog('form ended', 'form selections are: {}'.format(ans))
		return
	if url == '35':
		bridge._message({'type':'load', 'url':'/catalog/{}'.format(kodi_utils.b64encode('demoplugin')), 'replace':True, 'data':kodi_utils.b64encode('33')})
		return
	