import urllib,urllib2,sys,re,xbmcplugin,xbmcgui,xbmcaddon,xbmc,os
import datetime
import time
import net

from threading import Timer
import json

PLUGIN='plugin.video.sportsmania'
ADDON = xbmcaddon.Addon(id=PLUGIN)
SETTINGS = xbmc.translatePath(os.path.join(ADDON.getAddonInfo('profile'),'settings.xml'))
image='http://xunitytalk.com/stvb/'
MEDIA_URL = 'special://home/addons/{0}/resources/'.format('plugin.video.sportsmania')
auth=ADDON.getSetting('authtoken')
ontapp1=int(ADDON.getSetting('ontapp_id_1'))
ontapp2=int(ADDON.getSetting('ontapp_id_2'))

USER='[COLOR yellow]'+ADDON.getSetting('snusername')+'[/COLOR]'
updateid= int(ADDON.getSetting('id'))
THESITE='sportsmania.eu'

if ADDON.getSetting('hlsenable')=='true':
   UA='iPhone'
else:    
    UA='XBMC'

net=net.Net()

STVBINI = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'sportsmania.ini')

try:
   filename = 'sportsmania.ini' 
   import xbmcvfs
   ottv = xbmcaddon.Addon('script.tvguidedixie')
   path = ottv.getAddonInfo('profile')
   file = os.path.join(path, 'ini', filename)
   stvb = xbmcaddon.Addon('plugin.video.sportsmania')
   src = os.path.join(stvb.getAddonInfo('path'), 'resources', filename)
   xbmcvfs.copy(src, file)
except:
   pass
                

def OPEN_URL(url):
    req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"}) 
    con = urllib2.urlopen( req )
    link= con.read()
    return link

def EXIT():
        xbmc.executebuiltin("XBMC.Container.Update(path,replace)")
        xbmc.executebuiltin("XBMC.ActivateWindow(Home)")
    
    
if ADDON.getSetting('snusername')=='':
    dialog = xbmcgui.Dialog()
    if dialog.yesno(THESITE.upper(), "If You Dont Have An Account", "Please Sign Up At",THESITE.upper(),"Exit","Carry On"):
        
        dialog.ok(THESITE.upper(), "You Now Need To Input", "Your [COLOR yellow]Username[/COLOR]")
        search_entered = ''
        keyboard = xbmc.Keyboard(search_entered, THESITE.upper())
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_entered = keyboard.getText() 
        ADDON.setSetting('snusername',search_entered)
        
        dialog.ok(THESITE.upper(), "You Now Need To Input", "Your [COLOR yellow]Password[/COLOR]")
        search_entered = ''
        keyboard = xbmc.Keyboard(search_entered, THESITE.upper())
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_entered = keyboard.getText() 
        ADDON.setSetting('snpassword',search_entered)
        ADDON.setSetting('login_time','2000-01-01 00:00:00')
    else:
        EXIT()

        



def TryAgain():
     dialog = xbmcgui.Dialog()       
     dialog.ok(THESITE.upper(), "You Now Need To Input", "Your [COLOR yellow]Username[/COLOR]")
     search_entered = ''
     keyboard = xbmc.Keyboard(search_entered, THESITE.upper())
     keyboard.doModal()
     if keyboard.isConfirmed():
         search_entered = keyboard.getText() 
     ADDON.setSetting('snusername',search_entered)
     
     dialog.ok(THESITE.upper(), "You Now Need To Input", "Your [COLOR yellow]Password[/COLOR]")
     search_entered = ''
     keyboard = xbmc.Keyboard(search_entered, THESITE.upper())
     keyboard.doModal()
     if keyboard.isConfirmed():
         search_entered = keyboard.getText() 
     ADDON.setSetting('snpassword',search_entered)
     ADDON.setSetting('login_time','2000-01-01 00:00:00')
     CATEGORIES()
 
        
site='http://'+THESITE+'/site/live-tv/'


datapath = xbmc.translatePath(ADDON.getAddonInfo('profile'))
cookie_path = os.path.join(datapath, 'cookies')
cookie_jar = os.path.join(cookie_path, THESITE+"_amember_new_matrix.lwp")
cookie_amember = os.path.join(cookie_path, THESITE+"_amember_.lwp")
cookies_123 = os.path.join(cookie_path, '123.lwp')
channeljs=os.path.join(cookie_path, "channels.js")
paki=os.path.join(datapath, "paki")



def checksub():
   #print'########################## checking ########################'
   username = ADDON.getSetting('snusername')
   password = ADDON.getSetting('snpassword')
   try:os.remove(cookie_jar)
   except:pass
   headers={'Host': THESITE,
            'Connection': 'keep-alive',
            'Origin': 'http://'+THESITE,
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'XBMC',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': 'http://'+THESITE+'/payments/login',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.8'}

   TIME = time.time()- 3600
   
   data={'amember_login':username, 'amember_pass':password , 'login_attempt_id': str(TIME)}
   html = net.http_POST('http://sportsmania.eu/payments/login',data,headers).content

   if 'true' in html:
      ADDON.setSetting('resetpass','false')
      net.save_cookies(cookie_amember)
      net.set_cookies(cookie_amember)

      html = net.http_GET('http://sportsmania.eu/payments/member').content

      try:
         
          match=re.compile('<h2 id="member-main-subscriptions-head">(.+?)</h2><div class="am-block" id="member-main-subscriptions">    <h3>(.+?)</h3>').findall(html)
     
          line1 = match[0][0].strip()
          line2 = match[0][1].strip()
          line3 = ''
          addDir('No Active Subscriptions','',2007,'','','','')
          addDir('Please Login And Pay For a Subscription','',2007,'','','','')
          addDir('@','',2007,'','','','')
          addDir('WWW.SPORTSMANIA.EU','',2007,'','','','')
          addDir('','',2007,'','','','')
          addDir('Thank You','',2007,'','','','')
    
      except:
          addDir('[COLOR red]-->[/COLOR] [COLOR limegreen]Click Me To Enter Addon[/COLOR] [COLOR red]<--[/COLOR]','',1,'','','','')
          addDir('My Active Subscriptions','',2007,'','','','')
          match=re.compile('<li><strong>(.+?)</strong>(.+?)</li>',re.DOTALL).findall(html)
          for sub , expiry in match:
             sub=sub.strip().replace('  ','')
             expiry=expiry.replace('\n',' ').replace('  ','')
             
             addDir('[COLOR white]%s %s[/COLOR]' % (sub,expiry),'',2007,'','','','')
          
   else:
    if 'please contact website administator' in html:
       
       addDir("------>>>>>> [COLOR red]Please Contact An Admin To Unlock Your Account[/COLOR] <<<<<<-----",'',2007,'','','','')
       addDir('','',2007,'','','','')
       addDir("------>>>>>> [COLOR red]Your Account is Locked For Some Reason[/COLOR] <<<<<<-----",'',2007,'','','','')
       addDir('','',2007,'','','','')
       addDir("------>>>>>> [COLOR red]It Maybe Locked Due To Too Many Login Attempts[/COLOR] <<<<<<-----",'',2007,'','','','')
       addDir('','',2007,'','','','')
       addDir("------>>>>>> [COLOR red]OR You Have Input Your Details Incorrectly Too Many Times[/COLOR] <<<<<<-----",'',2007,'','','','')
       addDir('','',2007,'','','','')
       addDir('Visit The Website Below For Help','',2007,'','','','')
       addDir('------>>>>>> [COLOR cyan]HTTP://SPORTSMANIA.EU[/COLOR] <<<<<<-----','',2007,'','','','')
       addDir('','',2007,'','','','')
    else:     
       dialog = xbmcgui.Dialog()
       dialog.ok("Please Check Your Details", "Username : "+ADDON.getSetting('snusername'), "Password : "+ ADDON.getSetting('snpassword'), "[COLOR red]is Wrong ...[/COLOR]")
       addDir("Doesn't Seem You Have an Account OR Details",'',2007,'','','','')
       addDir('Are Incorrect','',2007,'','','','')
       addDir('','',2007,'','','','')
       addDir('------>>>>>> [COLOR red]RESET PASSWORD [/COLOR]<<<<<<-----','url',2008,'','','','')
       addDir('OR','',2007,'','','','')
       addDir('------>>>>>>   [COLOR green]Try AGAIN    [/COLOR]<<<<<<-----','url',2009,'','','','')


def resetpass():
    loginurl = 'http://'+THESITE+'/payments/sendpass'
    headers  = {'Host':THESITE,
                                            'Origin':'http://'+THESITE,
                                            'Referer':'http://'+THESITE+'/payments/login',
                                                    'X-Requested-With':'XMLHttpRequest'}
    
    get = net.http_POST(loginurl, {'login':ADDON.getSetting('snusername')}, headers).content

    message=re.compile('"error":\["(.+?)"\]').findall(get)[0]
    try:
        line1 = message.split('.')[0]
        line2 = message.split('.')[1]
        line3 = ''
        dialog = xbmcgui.Dialog()
        dialog.ok(THESITE.upper(), line1,line2, line3)
        dialog.ok(THESITE.upper(), '','Please Check Your Junk Folder', '')
        ADDON.setSetting('resetpass','false')
    except:
        line1 = message.split('[')[0]
        line2 = message.split('[')[1]
        line2 = '[COLOR red]'+line2.split(']')[0]+'[/COLOR]'
        line3 = message.split(']')[1]      
        dialog = xbmcgui.Dialog()
        dialog.ok(THESITE.upper(), line1,line2, line3)
        EXIT()
        import update
        update.reset()
      
def KICKOUT():
        try:
            checksub()
            
            try:os.remove(cookie_jar)
            except:pass
        except:
            pass   


    
def WAIT():
        try:
            os.remove(cookie_jar)
            #print'cookie removed'
        except:
            pass   
        dialog = xbmcgui.Dialog()
        dialog.ok('[COLOR red]ERROR !![/COLOR]',"", "[COLOR red]Cannot Retrieve Channels[/COLOR]", "")
        Login()
               

def LOGOUT():
    net.set_cookies(cookie_jar)
    html = net.http_GET(site).content
    match=re.compile('  href="(.+?)">Log Out</a>').findall(html)[0]
    net.set_cookies(cookie_jar)
    logout = net.http_GET(match.replace('#038;','')).content
    if 'You are now logged out' in logout:
        #print'===============LOGGED OUT !!==============='
        dialog = xbmcgui.Dialog()
        dialog.ok(THESITE.upper(),'', "You Are Now Logged Out", "")
        EXIT()
        
    

def Login():
    #print'###############    LOGIN TO Sports Mania   #####################'
    loginurl = 'http://'+THESITE+'/payments/login'
    username = ADDON.getSetting('snusername')
    password = ADDON.getSetting('snpassword')

    import time
    TIME = time.time()- 3600
    
    data={'amember_login':username,'amember_pass':password,'login_attempt_id':str(TIME).split('.')[0],'remember_login':'1'} 
  

    headers={'Accept':'*/*',
    'Accept-Encoding':'gzip,deflate,sdch',
    'Accept-Language':'en-US,en;q=0.8',
    'Connection':'keep-alive',
    'Content-Type':'application/x-www-form-urlencoded',
    'Host':THESITE,
    'Origin':'http://'+THESITE,
    'Referer':'http://'+THESITE+'/payments/login',
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.146 Safari/537.36',
    'X-Requested-With':'XMLHttpRequest'}

    html = net.http_POST(loginurl, data, headers).content
  
     
    if os.path.exists(cookie_path) == False:
            os.makedirs(cookie_path)
    add_ontapp = ontapp1 + 1        
    ADDON.setSetting('ontapp_id_1',str(add_ontapp))       
    net.save_cookies(cookie_jar)
    net.set_cookies(cookie_jar)
    a=net.http_GET('http://'+THESITE+'/payments/api/matrix/channels',headers={'User-Agent' :UA}).content
    f = open(channeljs, mode='w')
    f.write(a)
    f.close()


def downloadchannel():
    if os.path.exists(cookie_path) == False:
        os.makedirs(cookie_path)
    if sessionExpired():
        Login()
    net.set_cookies(cookie_jar)
    a=net.http_GET('http://'+THESITE+'/site/MatrixUp/payments/api/matrix/channels',headers={'User-Agent' :UA}).content
    f = open(channeljs, mode='w')
    f.write(a)
    f.close()


def parse_date(dateString):
    import time
    return datetime.datetime.fromtimestamp(time.mktime(time.strptime(dateString.encode('utf-8', 'replace'), "%Y-%m-%d %H:%M:%S")))


def getday():
    today = datetime.datetime.today()
    return today.strftime("%A")  


def sessionExpired():
    #print'##############################'
    try:
        a=open(cookie_jar).read()
        r=ADDON.getSetting('snusername')+'\%7C(.+?)\%7C'
        expiry=re.compile(r).findall(a)[0]
        expiry=int(expiry)
        
    except:     
        expiry=0000000000

    import time
     
    now        = int(time.time())
    
    if now > expiry:
       #print'Sesson Expired True'
       #print'##############################'
       return True
    else:
       #print'Sesson Expired False'
       #print'##############################'
       return False
    


def server():
    net.set_cookies(cookie_jar)
    a=net.http_GET('http://'+THESITE+'/payments/api/matrix/channels',headers={'User-Agent' :UA}).content
  
    #print'WEB READ'
    return a


def CheckChannels():
    update=OPEN_URL('http://xty.me/xunitytalk/addons/plugin.video.offside/update.txt')
    ADDON.setSetting('pakauth',re.compile('<pakauth>(.+?)</pakauth>').findall(update)[0]) 
    ADDON.setSetting('pakurl',re.compile('<pakurl>(.+?)</pakurl>').findall(update)[0])

def cleanHex(text):
    def fixup(m):
        text = m.group(0)
        if text[:3] == "&#x": return unichr(int(text[3:-1], 16)).encode('utf-8')
        else: return unichr(int(text[2:-1])).encode('utf-8')
    return re.sub("(?i)&#\w+;", fixup, text.decode('ISO-8859-1').encode('utf-8'))


#

def CreatIniNow(name,url,mode,iconimage,play,date,description,page=''):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)+"&play="+urllib.quote_plus(play)+"&date="+urllib.quote_plus(date)+"&description="+urllib.quote_plus(description)+"&page="+str(page)
        a=name.replace('-[US]','').replace('-[EU]','').replace('[COLOR yellow]','').replace('[/COLOR]','').replace(' GB','').replace(' (G)','').replace(' HD','').replace(' EU','')+'='+u
        f = open(STVBINI, mode='a')
        f.write(a+'\n')
        f.close()           

def CATEGORIES():
    #CheckChannels()
    if sessionExpired():
        Login()

    try:
        link = json.loads(server())
    except:
        return KICKOUT()

    data2 = link['channels']
    lista = []
    for k in data2:
        #print'id: '+k['cat_id']
        lista.append(k['cat_id'])
    
    if ontapp1 > ontapp2:
        a='[%s]\n'% PLUGIN
        f = open(STVBINI, mode='w')
        f.write(a)
        f.close()
        
  
    uniques=[]
    uniquesurl=[]
    data=link['categories']
    ret = ''
    for j in data:
        if j in lista:
            url = j
            name = data[j].encode("utf-8")
            
            if name not in uniques:
                uniques.append(name)
                uniquesurl.append(url)
                if ".GAME ZONE" in name:
                    #print"gamezone::::: "+url
                    addDir('[COLOR blanchedalmond]'+name+'[/COLOR]',url,4,MEDIA_URL+'games.png','','','')
                elif ".English Premier" in name:
                    addDir('[COLOR chartreuse]'+name+'[/COLOR]',url,4,MEDIA_URL+'epl1.png','','','')
                elif "Aussie Mania" in name:
                    addDir('[COLOR yellow]'+name+'[/COLOR]',url,4,MEDIA_URL+'aus.png','','','')
                else:
                    addDir(name,url,4,MEDIA_URL+url+'.png','','','')

            
             
    if ontapp1 > ontapp2:                
        #print'################# CREATING INI ########################'        
        data=link['channels']
        for field in data:
            id= str(field['id'])
            name= field['title'].encode("utf-8")
            if ".GAME ZONE" in name:
                
                CreateInitNow('[COLOR blanchedalmond]'+name+'[/COLOR]',url,2,MEDIA_URL+'games.png','','','')
            elif ".English Premier" in name:
                CreateInitNow('[COLOR chartreuse]'+name+'[/COLOR]',url,2,MEDIA_URL+'premiere.jpg','','','')
            else:
                iconimage=id+'.png'
                CreatIniNow(name,id,2,MEDIA_URL+iconimage,'False','','')

                 
    if os.path.exists(cookie_jar) == True:
        addDir('.[COLOR white]-->>[/COLOR][COLOR chocolate]Click Here To Check When Your Sub Expires [/COLOR][COLOR white]<---[/COLOR]','url',2007,'','','','')
        addDir('[COLOR aqua].Maintenance Tools[/COLOR]','url',16000,'','','','')
        addDir('[COLOR red].View Calendar[/COLOR]','http://sportsmania.eu/sites/view.php?pg=calendar',2005,MEDIA_URL+'calendar.png','','','')
        addDir('[COLOR red].View USA Calendar[/COLOR]','http://sportsmania.eu/sites/view.php?pg=usacalendar',2005,MEDIA_URL+'test.png','','','')
        addDir('[COLOR gold].Willows Sports Mix (Football Rugby & More)[/COLOR]','http://'+THESITE+'/apisprotected/extrassm.php',2003,MEDIA_URL+'extra.png','','','')
        #addDir('[COLOR aquamarine].Premier League Matchday Football[/COLOR]','http://'+THESITE+'/apisprotected/plp.php',2003,MEDIA_URL+'epl1.png','','','')
        addDir('[COLOR mediumorchid].NFL Game Day[/COLOR]','http://'+THESITE+'/apisprotected/usa.php',2003,MEDIA_URL+'nfl.png','','','')
        addDir('[COLOR navajowhite].MLB Game Pass[/COLOR]','http://'+THESITE+'/apisprotected/mlb.php',2003,MEDIA_URL+'mlb.png','','','')
        addDir('[COLOR cyan].Sports On Demand[/COLOR]','http://'+THESITE+'/apisprotected/channels1.php',2003,MEDIA_URL+'cup.png','','','')                
        addDir('[COLOR mediumspringgreen].Movies / TV Shows On Demand [/COLOR][COLOR gold][/COLOR]','http://xtyrepo.me/xunitytalk/playlist/OSS%20MAIN',12000,MEDIA_URL+'movies.png','','','')           
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    ADDON.setSetting('ontapp_id_2',str(ontapp1))
    xbmc.executebuiltin('Container.SetViewMode(51)')

def schedule(url):
    if 'usa' in url:
       media=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons','usa')
    else:
       media=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons','uk')
       
    net.set_cookies(cookie_jar)
    response = net.http_GET(url)
    link = response.content.replace('\t','').replace('\n','').replace('\r','')
    titles=re.compile('<div class="panel-heading"><center><b>(.+?)</b></center>').findall(link)
    for heading in titles:
        if not 'sport' in heading.lower():
           if getday().lower() in heading.lower():           
              addDir('[COLOR cyan]*** %s ***[/COLOR]'% heading,'url',200,'','','','')

              links=link.split(heading)[1]
              links=links.split('</table>')[0]
              links=links.split('<tr>')
              for p in links:
                  try:
                      match=re.compile('<th bgcolor="(.+?)"><font color=".+?">(.+?)</font>',re.DOTALL).findall(p)

                      font= match[0][0]
                      if font =='#624F27':       #CRICKET/NFL
                        font = 'sienna'
                      if font =='#0000FF':       #FOOTBALL/SOCCER
                        font = 'royalblue'
                      if font =='#006F09':       #RUGBY/NBA
                        font = 'coral'
                      if font =='#69005F':       #SNOOKER/NHL
                        font = 'purple'
                      if font =='#FF0000':       #MOTOR/MLB
                        font = 'red'
                      if font =='#E68300':       #MMA
                        font = 'orange'
                      if font =='#000000':       #HORSE
                        font = 'grey'
                      if font =='#ADFF2F':       #TENNIS
                        font = 'lime'
                      if font =='#FF1493':       #GOLF
                        font = 'pink'
                      if font =='#40E0D0':       #GAA/NASCAR
                        font = 'turquoise'
                      if font =='#DAA520':       #DARTS/NCAA
                        font = 'darkcyan'
                          
                          
                      time= match[0][1]
                      name= match[1][1]
                      channels= match[2][1].replace('Game Zone / ','').replace(' Thai',' HD TH').strip()
        
                      NAME= '[COLOR %s]%s - %s -[/COLOR][COLOR green]%s[/COLOR]' % (font,time.replace('-',''),name.replace('-',''),channels.replace('-',''))
                      
                      addDir(NAME.encode('utf-8'),'url',2,media+'/'+font+'.png','GET_EVENT','','')
                  except:pass
    setView('tvshow', 'calendar')  


def MySearch():
    addDir('[COLOR white]Click to >> [/COLOR][COLOR lime]Search Tv/Movies [COLOR white]<<[/COLOR]','url',3000,'','','','','')
    favs = ADDON.getSetting('favs').split(',')
    for title in favs:
        if len(title)>1:
            addDir(title.title(),title,3000,'','','','','')      
        #addDir(title,NEW_URL,8,'','')


def OnDemandFirstCat():
    addDir('[COLOR white]Search Tv/Movies[/COLOR]','url',3003,'','','','','')
    addDir('[COLOR white]Movies[/COLOR]','movie',4001,'','','','','')
    addDir('[COLOR white]Tv Shows[/COLOR]','series',4001,'','','','','')


def OnDemandSecondCat(url):
    addDir('[COLOR white]Most Popular[/COLOR]','http://123movies.to/movie/filter/%s/view/all/all/all/all/all/'%url,4002,'','','','',0)   
    addDir('[COLOR white]Latest[/COLOR]','http://123movies.to/movie/filter/%s/latest/all/all/all/all/all/'%url,4002,'','','','',0)
    addDir('[COLOR white]Most Favourite[/COLOR]','http://123movies.to/movie/filter/%s/favorite/all/all/all/all/all/'%url,4002,'','','','',0)
    addDir('[COLOR white]Most Rating[/COLOR]','http://123movies.to/movie/filter/%s/rating/all/all/all/all/all/'%url,4002,'','','','',0)
    addDir('[COLOR white]Top IMDb[/COLOR]','http://123movies.to/movie/filter/%s/imdb_mark/all/all/all/all/all/'%url,4002,'','','','',0)
            

def OnDemandThirdCat(url,page):

    page =page+1
    THE_URL =url
    user='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36'
    headers={'User-Agent':user}
                          
    try:
       net.set_cookies(cookies_123)
       LINK=net.http_GET(url+str(page),headers=headers).content
       net.save_cookies(cookies_123)
       #print'CLOUDFLARE BYPASSED'
    except:
       import cloudflare
               
       LINK=cloudflare.solve(url+str(page),cookies_123,user)

    LINK = LINK.split('"ml-item">')
    for p in LINK:
        try:
           URL=re.compile('a href="(.+?)"',re.DOTALL).findall(p)[0]
           name=re.compile('title="(.+?)"',re.DOTALL).findall(p)[0]
           iconimage=re.compile('img data-original="(.+?)"',re.DOTALL).findall(p)[0]           

           addDir(name,URL,3001,iconimage,'','','','')
        except:pass  
    addDir('[COLOR royalblue]>> Next Page >>[/COLOR]',THE_URL,4002,'','','','',page)
            
       

def getme():
   return '|User-Agent=Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'


def Oo0Oool(url):
 iI111iI = urllib2 . Request (url )
 IiII = urllib2 . urlopen ( iI111iI )
 iI1Ii11111iIi = IiII . read ( )
 IiII . close ( )
 return iI1Ii11111iIi

def auth():
 DATA_URL='https://app.dynns.com/keys/apps_token.php'
 request = urllib2.Request(DATA_URL)
 base64string = 'dm94c29mdGV4cGVydDpAdm94c29mdGV4cGVydEA='
 request.add_header("Authorization", "Basic %s" % base64string)   
 return urllib2.urlopen(request).read()
           
def worldlinks(name,url):
    NAME=name
    genre=name.split('[COLOR')[0].replace('.','')
    addDir('[COLOR gold]hmmm...[/COLOR]','url',2004,'','','','')
    AUTH=auth()
    aa=open(url).read()
    link=aa.split('<items>')
    for p in link:
        try:
            name=re.compile('<programTitle>(.+?)</programTitle>').findall(p)[0]
            URL=re.compile('<programURL>(.+?)</programURL>').findall(p)[0]
            iconimage=re.compile('<programImage>(.+?)</programImage>').findall(p)[0]
            if '<programCategory>'+genre+'<' in p:
                addDir(name,URL+AUTH,2004,iconimage,'','','')
        except:pass             
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    
def parseAPI(url):
       ADDME=[]
       net.set_cookies(cookie_jar)
       a=net.http_GET(url,headers={'User-Agent':'XBMC'}).content

       import json
       link=json.loads(a)
       data=link['vod_channels']
       for field in data:
           id= str(field['channel_url'])
           name= field['channel_title'].encode("utf-8")
           if '(' in name:
              date='('+name.split('(')[1]
              name=name.split('(')[0]
              NAME='[COLOR aqua]%s[/COLOR] - [COLOR yellow]%s[/COLOR]' % (name,date)
           else:
              NAME='[COLOR aqua]%s[/COLOR]' % (name)
           addDir(NAME,id,2004,'','','','')

def SportsOnDemand(url):
       ADDME=[]
       net.set_cookies(cookie_jar)
       a=net.http_GET(url,headers={'User-Agent':'XBMC'}).content

       import json
       link=json.loads(a)
       data=link['vod_channels']
       for field in data:
           id= str(field['channel_url'])
           name= field['channel_title'].encode("utf-8")
           if '(' in name:
              date='('+name.split('(')[1]
              name=name.split('(')[0]
              NAME='[COLOR darkgrey]%s[/COLOR] - [COLOR yellow]%s[/COLOR]' % (name,date)
           else:
              NAME='[COLOR darkgrey]%s[/COLOR]' % (name)
           addDir(NAME,id,2004,'','','','') 
        
        
def playAPI(name,url,iconimage):
    if 'wmsAuthSign=' in url:
        url = url+'|User-Agent='+getuser()
         
    if url =='none':
        dialog = xbmcgui.Dialog()
        return dialog.ok(THESITE.upper(), '',"Streams Not Active Until match Time", "")
      
    if '.f4m' in url:
        import F4MProxy
        player=F4MProxy.f4mProxyHelper()
        player.playF4mLink(url, name,iconimage)      
    else:  
       if 'CHANGEME' in url:
          URL=['1600','3000','4500']
          NAME=['480P','720P','1080P']
          RES = URL[xbmcgui.Dialog().select('Please Select Resolution', NAME)]
          url=url.replace('CHANGEME',RES)+getme()
       liz = xbmcgui.ListItem(name, iconImage='DefaultVideo.png', thumbnailImage=iconimage)
       liz.setInfo(type='Video', infoLabels={'Title':name})
       liz.setProperty("IsPlayable","true")
       liz.setPath(url)
       xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

       
def GENRES(name,url):

    if sessionExpired():
        Login()
    link = json.loads(server())
    data=link['channels']
    for field in data:
        id= field['id']
        title= field['title'].encode("utf-8")
        genre= field['cat_id']
        iconimage=image+id+'.png'
        if url == genre:
            addDir(title,id,2,iconimage,'False','','')
          
    if url=='40':
       SportsOnDemand('http://'+THESITE+'/apisprotected/bt.php')

    if url=='27':
       SportsOnDemand('http://'+THESITE+'/apisprotected/bbc.php')
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)             
    setView('movies', 'channels')        


def SEARCH(search_entered):
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36'}
    favs = ADDON.getSetting('favs').split(',')
    if 'url' in search_entered:
        keyboard = xbmc.Keyboard('', 'Search Movies / Tv Shows')
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_entered = keyboard.getText()

    search_entered = search_entered.replace(',', '')

    if len(search_entered) == 0:
        return

    if not search_entered in favs:
        favs.append(search_entered)
        ADDON.setSetting('favs', ','.join(favs))

    search_entered = search_entered.replace(' ','%20')
        
    url='http://123movies.to/movie/search/' + str(search_entered).replace(' ','+')
    #printurl
    try:
       net.set_cookies(cookies_123)
       LINK=net.http_GET(url,headers=headers).content
       net.save_cookies(cookies_123)
       #print'CLOUDFLARE BYPASSED'
    except:
       import cloudflare
       user='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36'                   
       LINK=cloudflare.solve(url,cookies_123,user)
                          
    #match=re.compile('class="ml-item">.+?a href="(.+?)".+?class="ml-mask jt".+?title="(.+?)">.+?data-original="(.+?)"',re.DOTALL).findall(LINK)
    LINK = LINK.split('"ml-item">')
    for p in LINK:
        try:
           URL=re.compile('a href="(.+?)"',re.DOTALL).findall(p)[0]
           name=re.compile('title="(.+?)"',re.DOTALL).findall(p)[0]
           iconimage=re.compile('img data-original="(.+?)"',re.DOTALL).findall(p)[0]           

           addDir(name,URL,3001,iconimage,'','','','')
        except:pass

        

def GetSearchLinks(name,url,iconimage,page):
  
    user='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36'
    headers={'User-Agent':user}
                          
    try:
       net.set_cookies(cookies_123)
       LINK=net.http_GET(url+'watching.html',headers=headers).content
       net.save_cookies(cookies_123)
       #print'CLOUDFLARE BYPASSED'
    except:
       import cloudflare
               
       LINK=cloudflare.solve(url+'watching.html',cookies_123,user)
                          
    uniques=[]
    try:movie_id = re.compile('movie-id="(.+?)"').findall(LINK)[0]
    except:movie_id = re.compile('updateMovieView\((.+?)\)').findall(LINK)[0]
    token = re.compile('player-token="(.+?)"').findall(LINK)[0]
    coookie_1 = re.compile('ds_hash: "(.*?)"').findall(LINK)[0]
    coookie_2 = re.compile('ds_token: "(.*?)"').findall(LINK)[0]
    coookie = coookie_1 + '=' + coookie_2

    net.set_cookies(cookies_123)                      
    LOAD =net.http_GET('http://123movies.to/ajax/get_episodes/%s/%s'%(movie_id,token),headers=headers).content
    link=LOAD.split('<div id="server-')
    for p in link:
        #try:
             host= p.split('"')[0]
           
             HTML=p.split('<a title="')

             for d in HTML:
                 TITLE=d.split('"')[0]
                 if 'Season' in name:
                    TITLE=TITLE
                    if TITLE not in uniques:
                       uniques.append(TITLE)
                       if ':' in TITLE:
                           addDir(TITLE,LOAD,3010,iconimage,'','',coookie,'')
                           xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)   
                 else:
                    TITLE=name+' - '+TITLE
          
                    try:
                        YEAR=re.compile('Release:</strong>(.+?)<').findall(LINK)[0].strip()
                        #printYear
                        token = re.compile('hash="(.+?)"').findall(d)[0]
                        SERVER=d.split('loadEpisode(')[1]
                        server=SERVER.split(',')[0]
                        episodeid=re.compile(',(.+?),').findall(SERVER)[0]

                        URL='http://123movies.to/ajax/load_episode/%s/%s' % (episodeid,token)                            
                        
                        #printHTML
                        addDir(TITLE,URL,3002,iconimage,'','',coookie,'')
                        

                    except:pass
                    
    match=re.compile('data-episodes="(.+?)-(.+?)"').findall(LOAD)
  
    for episodeid , token in match:

      URL='http://123movies.to/ajax/load_episode/%s/%s' % (episodeid,token)                            
      addDir('.'+name+' HD',URL,3002,iconimage,'','',coookie,'')
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)      


def GetEpisodeLinks(name,LOAD,iconimage,page):
    NAME = name
    link=LOAD.split('<div id="server-')
    for p in link:
        #try:
             host= p.split('"')[0]
           
             HTML=p.split('<a title="')

             for d in HTML:
                 TITLE=d.split('"')[0]
          
                 try:
                     token = re.compile('hash="(.+?)"').findall(d)[0]
                     SERVER=d.split('loadEpisode(')[1]
                     server=SERVER.split(',')[0]
                     episodeid=re.compile(',(.+?),').findall(SERVER)[0]

                     URL='http://123movies.to/ajax/load_episode/%s/%s' % (episodeid,token)                            
                     
                     if NAME in TITLE:
                         addDir(TITLE,URL,3002,iconimage,'','',page,'')
                     

                 except:pass                
    match=re.compile('data-episodes="(.+?)-(.+?)"').findall(LOAD)

    for episodeid , token in match:

      URL='http://123movies.to/ajax/load_episode/%s/%s' % (episodeid,token)                            
      addDir('.'+NAME+' HD',URL,3002,iconimage,'','',page,'')
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)      
        

def OnDemand(url):
    addDir('[COLOR lime]Search[/COLOR]','url',3003,'','','','','')
    
    link = OPEN_URL(url).replace('\n','').replace('\t','').replace('\r','')
    if '<streamtvbox>' in link:
        message=re.compile('<streamtvbox>(.+?)</streamtvbox>').findall (link)
        for name in message:
            addLink(name,'url','','')


    DIRS=re.compile('<name>(.+?)</name><link>(.+?)</link><thumbnail>(.+?)</thumbnail>',re.DOTALL).findall (link)

    for name , url , iconimage  in DIRS:      
        addDir(name,url,6,iconimage,'','','','')

        
    DIRS=re.compile('<title>(.+?)</title><dir>(.+?)</dir><thumbnail>(.+?)</thumbnail>',re.DOTALL).findall (link)

    for name , url , iconimage  in DIRS:      
        addDir(name,url,6,iconimage,'','','','')        



def OnDemandLinks(url):
    link = OPEN_URL(url).replace('\n','').replace('\t','').replace('\r','')
    if '<message>' in link:
       message=re.compile('<message>(.+?)</message>').findall (link)
       for name in message:
           addLink(name,'url','','')   

    DIRS=re.compile('<name>(.+?)</name><link>(.+?)</link><thumbnail>(.+?)</thumbnail>',re.DOTALL).findall (link)

    for name , url , iconimage  in DIRS:      
        addDir(name,url,6,iconimage,'','','','')  

    LINKS=re.compile('<title>(.+?)</title.+?<link>(.+?)</link.+?<thumbnail>(.+?)</thumbnail>',re.DOTALL).findall (link)
    
   
    for name , url , iconimage in LINKS:
        addDir(name,url,7,iconimage,'','','','')


def GrabVK(url):
    html=OPEN_URL(url)
    r      ='"url(\d+)":"(.+?)"'
    name=[]
    url=[]
    match = re.compile(r,re.DOTALL).findall(html)
    for quality,stream in match:
        name.append(quality.replace('\\','')+'p')
        url.append(stream.replace('\/','/'))
    return url[xbmcgui.Dialog().select('Please Select Resolution', name)]
    
def afdah(url):
    url= 'https://m.afdah.org/watch?v='+url

    loginurl = 'https://m.afdah.org/video_info/html5'

    v=url.split('v=')[1]
    data={'v': v}
    headers = {'host': 'm.afdah.org','origin':'https://m.afdah.org', 'referer': url,
               'user-agent':'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_2 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8H7 Safari/6533.18.5','x-requested-with':'XMLHttpRequest'}

    first= net.http_POST(loginurl,data,headers).content

    link= json.loads(first)
    name=[]
    url=[]
    for j in link:
        name.append(j.upper())
   
        url.append(urllib.unquote(link[j][3]))

    THEURL= url[xbmcgui.Dialog().select('Please Select Resolution', name)]
    import requests
    r=requests.get(THEURL,allow_redirects=False, verify=False )   

    r = requests.get(str(r.headers['Location']),allow_redirects=False, verify=False )

    return r.headers['location']


def PlayOnDemand(url):

    if 'googlevideo' in url or 'blogspot' in url:
        url=url
    elif not 'http' in url:
        url=afdah(url)
    elif 'http://vk' in url:
        url=GrabVK(url)

    elif 'movreel' in url:
        import movreel
        url=movreel.solve(url)
    elif 'xmovies8.tv' in url:
        url=url        
    else:
        import urlresolver
        url=urlresolver.resolve(url)
            
         
    liz = xbmcgui.ListItem(name, iconImage='DefaultVideo.png', thumbnailImage=iconimage)
    liz.setInfo(type='Video', infoLabels={'Title':description})
    liz.setProperty("IsPlayable","true")
    liz.setPath(url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


    


 
def EVENTS():
    link = OPEN_URL('http://channelstatus.weebly.com/upcoming-events.html')
    link=link.split('<div class="paragraph" style="text-align:left;"')[1]
    link=link.split('>***')
    for p in link:
        try:
            DATE=re.compile('(.+?)\*').findall(p)[0]
            addDir('[COLOR cyan]'+DATE+'[/COLOR]','',2000,'','False','','')  
            match=re.compile('\[(.+?)\]</strong>__ (.+?) - (.+?)__',re.DOTALL).findall (p)
            for TIME ,VS , CHANNEL in match:

                CHANNEL=CHANNEL.replace('beIN','beIN Sports ').replace('Sports  Sports','Sports')
                name= '[COLOR white][%s][/COLOR][COLOR yellow]- %s -[/COLOR][COLOR green]%s[/COLOR]' %(TIME,VS,CHANNEL)
                addDir(name,'url',2,'','GET_EVENT','','')       
        except:pass
    xbmc.executebuiltin('Container.SetViewMode(51)')  
        

 
def Show_Dialog():
    dialog = xbmcgui.Dialog()
    dialog.ok(THESITE.upper(), '',"All Done Try Now", "")
        
def REPLAY():
       
        xbmc.executebuiltin('ActivateWindow(videos,plugin://plugin.video.footballreplays)')

 
    
def OPEN_MAGIC(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent' , "Magic Browser")
    response = urllib2.urlopen(req)
    link=response.read()
    response.close()
    return link
        
        
        
def timeout():
    if ADDON.getSetting('hlsenable')=='true':
       return ''
    else:  
       quality = ADDON.getSetting('timeout')
       if quality == '0':
           return ' timeout=5 '
       elif quality == '1':
           return ' timeout=10'
       elif quality == '2':
           return ' timeout=15'
       elif quality == '3':
           return ' timeout=20'
       elif quality == '4':
           return ' timeout=25'
       elif quality == '5':
           return ' timeout=30'
       elif quality == '6':
           return ' timeout=35'
       elif quality == '7':
           return ' timeout=40'
       elif quality == '8':
           return ' timeout=45'
       elif quality == '9':
           return ' timeout=50'
        


def Show_Down():
    dialog = xbmcgui.Dialog()
    dialog.ok(THESITE.upper(), 'Sorry Channel is Down',"Will Be Back Up Soon", "Try Another Channel")  
    
def Show_Cover():
    dialog = xbmcgui.Dialog()
    dialog.ok(THESITE.upper(), '',"Sorry We Dont Cover This Channel", "")

    
def Show_Dif_Channel():
    dialog = xbmcgui.Dialog()
    dialog.ok(THESITE.upper(), '',"Please Use A Different Channel", "")

def PLAY_DEMAND_STREAM(name, url, iconimage,cookie):

   headers={'Cookie':cookie,'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36','Referer': 'http://123movies.to','x-requested-with':'XMLHttpRequest'}
   STREAM=[]
   NAMED=[]
   GRAB=[]
   uniques=[]
   try:
      #net.set_cookies(cookies_123)
      #print'CLOUDFLARE BYPASSED'
      HTML=net.http_GET(url,headers=headers).content
      
      if 'oops' in HTML.lower():
        dialog = xbmcgui.Dialog()
        return dialog.ok(THESITE.upper(), 'Sorry Channel',"", "Could Not Find A Stream") 
      match=re.compile('file="(.+?)".+?label="(.+?)"',re.DOTALL).findall(HTML)
      #printmatch
      for FINAL_URL , res in match:
           if len(res)>4:
              res='700'
           
           GRAB.append([FINAL_URL , res])
      matched=re.compile('file="(.+?)"',re.DOTALL).findall(HTML)

      for FINAL_URL  in matched:
   
           HOST=FINAL_URL.split('://')[1]
           HOST=HOST.split('/')[0]              
           GRAB.append([FINAL_URL , '700'])
           
      for FINAL_URL , res  in GRAB:
           HOST=FINAL_URL.split('://')[1]
           HOST=HOST.split('/')[0]                                  
            
           if not '.srt' in FINAL_URL:
               res=res.replace('p','')
               
               res=int(res)
               if (res > 700):
                   res='[COLOR green]1080P[/COLOR]'
                   NAME='%s - [COLOR royalblue]%s[/COLOR]' %(res,HOST.upper())
                   if FINAL_URL not in uniques:
                      uniques.append(FINAL_URL)   
                      STREAM.append(FINAL_URL)
                      NAMED.append(NAME)
             
              
               if (res > 500):
                   res='[COLOR yellow]720P[/COLOR]'
                   NAME='%s - [COLOR royalblue]%s[/COLOR]' %(res,HOST.upper())
                   if FINAL_URL not in uniques:
                      uniques.append(FINAL_URL)   
                      STREAM.append(FINAL_URL)
                      NAMED.append(NAME)                

                        
               if (res < 500):
                   res='[COLOR orange]SD[/COLOR]'
                 

                   NAME='%s - [COLOR royalblue]%s[/COLOR]' %(res,HOST.upper())
                   if FINAL_URL not in uniques:
                      uniques.append(FINAL_URL)   
                      STREAM.append(FINAL_URL)
                      NAMED.append(NAME)
                        
                       
   except:pass
   url=STREAM[xbmcgui.Dialog().select('Choose Source !!', NAMED)]
   if 'streaming.fshare' in url:
      req = urllib2.Request(url, headers=headers) 
      url = urllib2.urlopen( req )  .geturl()    
      #url=urllib.urlopen(url).geturl()
      #printurl
   liz = xbmcgui.ListItem(name, iconImage='DefaultVideo.png', thumbnailImage=iconimage)
   liz.setInfo(type='Video', infoLabels={'Title':name})
   liz.setProperty("IsPlayable","true")
   liz.setPath(url.replace('amp;',''))
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

    
def PLAY_STREAM(name, url, iconimage, play, description):

    
    if play =='GET_EVENT':
        url=PLAY_FROM_EVENTS(name, url, iconimage, play, description)

           
        if not url:
            return Show_Cover()
         
    if len(url)>7:
       stream_url = url

    else:   
       if sessionExpired():
           Login()
       net.set_cookies(cookie_jar)
       stream_url= net.http_GET('http://'+THESITE+'/payments/api/matrix/channel/%s'%url,headers={'User-Agent' :UA}).content+timeout()
       if stream_url=='':
           return Show_Down()
    liz = xbmcgui.ListItem(name, iconImage='DefaultVideo.png', thumbnailImage=iconimage)
    liz.setInfo(type='Video', infoLabels={'Title':description})
    liz.setProperty("IsPlayable","true")
    liz.setPath(stream_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz) 



def PLAY_FROM_EVENTS(name, url, iconimage, play, description):
    name=name.split('[COLOR green]')[1].replace('[/COLOR]','')
    name=name.replace('/',',').strip()
    if not 'EPL' in name:
       name.replace('-','').strip()
    nameFINAL=[]
    urlFINAL=[]
    if ',' in name:
       
        nameSelect=[]
        urlSelect=[]
        name=name.split(',')
        for p in name:
            urlSelect.append(p.strip().lower())
            nameSelect.append(p.strip())
        TITLE = urlSelect[xbmcgui.Dialog().select('Please Select Channel', nameSelect)]      
        TITLE=TITLE.replace(' ','').lower().strip()
        if 'btsport' in TITLE:
             net.set_cookies(cookie_jar)
             a=net.http_GET('http://'+THESITE+'/apisprotected/bt.php',headers={'User-Agent':'XBMC'}).content
             link=json.loads(a)
             data=link['vod_channels']
             for field in data:
                 id= str(field['channel_url'])
                 YOYO= field['channel_title'].encode("utf-8")
                 if TITLE in YOYO.replace(' ','').lower():
                     urlFINAL.append(id)
                     nameFINAL.append('[COLOR lime]%s[/COLOR]'%(YOYO))
             link = json.loads(server())
             data=link['channels']
             for field in data:
                 id= str(field['id'])
                 YOYO= field['title'].encode("utf-8")     
                 if TITLE in YOYO.replace(' ','').lower():
                     urlFINAL.append(id)
                     nameFINAL.append('[COLOR lime]%s[/COLOR]'%(YOYO))
             if urlFINAL:
                 return urlFINAL[xbmcgui.Dialog().select('Multiple Channels Found', nameFINAL)]  
        else:       
           link = json.loads(server())
           data=link['channels']
           for field in data:
               id= str(field['id'])
               YOYO= field['title'].encode("utf-8")     
               if TITLE in YOYO.replace(' ','').lower():
                   urlFINAL.append(id)
                   nameFINAL.append('[COLOR lime]%s[/COLOR]'%(YOYO))
           if urlFINAL:
               return urlFINAL[xbmcgui.Dialog().select('Multiple Channels Found', nameFINAL)] 

    else:
    
        NAME=name.replace(' ','').lower().strip()
        if 'btsport' in NAME:
             net.set_cookies(cookie_jar)
             a=net.http_GET('http://'+THESITE+'/apisprotected/bt.php',headers={'User-Agent':'XBMC'}).content
             link=json.loads(a)
             data=link['vod_channels']
             for field in data:
                 id= str(field['channel_url'])
                 YOYO= field['channel_title'].encode("utf-8")
                 if NAME in YOYO.replace(' ','').lower():
                     urlFINAL.append(id)
                     nameFINAL.append('[COLOR lime]%s[/COLOR]'%(YOYO))
             link = json.loads(server())
             data=link['channels']
             for field in data:
                 id= str(field['id'])
                 NAME_= field['title'].encode("utf-8")   
                 if NAME in NAME_.replace(' ','').lower().strip():
                     urlFINAL.append(id)
                     nameFINAL.append('[COLOR lime]%s[/COLOR]'%(NAME_))
                     
             if urlFINAL:
                 return urlFINAL[xbmcgui.Dialog().select('Multiple Channels Found', nameFINAL)]
        else:       
           link = json.loads(server())
           data=link['channels']
           for field in data:
               id= str(field['id'])
               NAME_= field['title'].encode("utf-8")   
               if NAME in NAME_.replace(' ','').lower().strip():
                   urlFINAL.append(id)
                   nameFINAL.append('[COLOR lime]%s[/COLOR]'%(NAME_))
           if urlFINAL:
               return urlFINAL[xbmcgui.Dialog().select('Multiple Channels Found', nameFINAL)] 
           else:
               return False
         
         
def setView(content, viewType):
        if content:
                xbmcplugin.setContent(int(sys.argv[1]), content)
        if ADDON.getSetting('auto-view') == 'true':#<<<----see here if auto-view is enabled(true) 
                xbmc.executebuiltin("Container.SetViewMode(%s)" % ADDON.getSetting(viewType) )#<<<-----then get the view type
                      
                          
            
    
def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param
def getSetting(setting):
        import json
        setting = '"%s"' % setting
 
        query = '{"jsonrpc":"2.0", "method":"Settings.GetSettingValue","params":{"setting":%s}, "id":1}' % (setting)
        response = xbmc.executeJSONRPC(query)

        response = json.loads(response)                

        if response.has_key('result'):
            if response['result'].has_key('value'):
                return response ['result']['value'] 


def setSetting(setting, value):



    query = '{"jsonrpc":"2.0", "method":"Settings.SetSettingValue","params":{"setting":"%s","value":%s}, "id":1}' % (setting, value)
    #printquery
    xbmc.executeJSONRPC(query)
    xbmc.executebuiltin("Container.Refresh") 

    
         
def Tools():
    addDir('Check For Updates','.f4m',16005,'','','','',0)  
    addDir('Delete Cache','.f4m',16006,'','','','',0)
    if ADDON.getSetting('hlsenable')=='true':
       last='RTMP'
    else:
       last='HLS'
    addDir('Speed Test','.f4m',16001,'','','','',0)   
    addDir('Change Username or Password','.f4m',16002,'','','','',0)  
    addDir('Use %s Stream'% last,'.f4m',16003,'','','','',0)

    if int(getSetting('videoplayer.stretch43'))<4:       
        addDir('Force 16:9 Video','.f4m',16004,'','','','videoplayer.stretch43',4)

        
    if getSetting('videoplayer.usedxva2')==True:      
        addDir('Disable Hardware Acceleration','.f4m',16004,'','','','videoplayer.usedxva2','false')
    else:      
        addDir('Enable Hardware Acceleration','.f4m',16004,'','','','videoplayer.usedxva2','true')
    addDir('Delete Cookie','.f4m',203,'','','','',0)

    

    

def changeEnableHLS():
    if ADDON.getSetting('hlsenable')=='true':
       change='false'
    else:
       change='true'
       
    ADDON.setSetting('hlsenable',change)
    xbmc.executebuiltin("Container.Refresh")
    

def CheckUpdate():
    dialog = xbmcgui.Dialog()
    link=OPEN_URL('https://raw.githubusercontent.com/Willowsportsmania/SportsMania/master/plugin.video.sportsmania/addon.xml')
    match=re.compile('name="SportsMania" version="(.+?)"').findall(link)[0]
    if ADDON.getAddonInfo('version')==match:

        dialog.ok(THESITE.upper(),'', "You Are On Latest Version", "")
    else:   
        xbmc.executebuiltin('UpdateLocalAddons') 
        xbmc.executebuiltin("UpdateAddonRepos")
        dialog.ok(THESITE.upper(),'', "Updating Repo Now", "")
        

def Deletecache():
     dialog = xbmcgui.Dialog()
     packages_cache_path = xbmc.translatePath(os.path.join('special://home/addons/packages', ''))
   
     for root, dirs, files in os.walk(packages_cache_path):
         file_count = 0
         file_count += len(files)
         
     # Count files and give option to delete
         if file_count > 0:

             dialog = xbmcgui.Dialog()
             for f in files:
                 os.unlink(os.path.join(root, f))
             for d in dirs:
                 shutil.rmtree(os.path.join(root, d))


     xbmc_cache_path = os.path.join(xbmc.translatePath('special://home'), 'cache')
     if os.path.exists(xbmc_cache_path)==True:    
         for root, dirs, files in os.walk(xbmc_cache_path):
             file_count = 0
             file_count += len(files)
        
         # Count files and give option to delete
             if file_count > 0:

                  for f in files:
                      if not '.db' in f:
                         try:
                             os.unlink(os.path.join(root, f))
                         except:
                             pass
                  for d in dirs:
                      if not '.db' in f:     
                         try:
                             shutil.rmtree(os.path.join(root, d))
                         except:
                             pass
 
     xbmc_cache_path = os.path.join(xbmc.translatePath('special://home'), 'temp')
     if os.path.exists(xbmc_cache_path)==True:    
         for root, dirs, files in os.walk(xbmc_cache_path):
             file_count = 0
             file_count += len(files)
        
         # Count files and give option to delete
             if file_count > 0:
 
                 
                  for f in files:
                      try:
                          os.unlink(os.path.join(root, f))
                      except:
                          pass
                  for d in dirs:
                      try:
                          shutil.rmtree(os.path.join(root, d))
                      except:
                          pass
     dialog.ok(THESITE.upper(),'', "All Done And Deleted", "")


def addDir(name,url,mode,iconimage,play,date,description,page=''):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)+"&play="+urllib.quote_plus(play)+"&date="+urllib.quote_plus(date)+"&description="+urllib.quote_plus(description)+"&page="+str(page)
        #printname.replace('-[US]','').replace('-[EU]','').replace('[COLOR yellow]','').replace('[/COLOR]','').replace(' (G)','')+'='+u
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name,"Premiered":date,"Plot":description} )
        menu=[]
        menu.append(('[COLOR green]Refresh Channel List[/COLOR]','XBMC.RunPlugin(%s?mode=202&url=None)'% (sys.argv[0])))
        menu.append(('[COLOR blue]Reset Password[/COLOR]','XBMC.RunPlugin(%s?mode=2008&url=None)'% (sys.argv[0])))
        menu.append(('[COLOR red]Delete Cookie[/COLOR]','XBMC.RunPlugin(%s?mode=203&url=None)'% (sys.argv[0])))
        menu.append(('[COLOR cyan]Log Out[/COLOR]','XBMC.RunPlugin(%s?mode=205&url=None)'% (sys.argv[0])))
        liz.addContextMenuItems(items=menu, replaceItems=False)
        if mode == 2 or mode==7  or mode==2004 or mode==3002 or mode==16001 or mode==16002 or mode==16003 or mode==16004 or mode==16005 or mode==16006 or mode==203:
            if not mode == 2000:
                if not '.f4m' in url:
                    liz.setProperty("IsPlayable","true")
            ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
          
        else:
            ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok




def addLink(name,url,iconimage, fanart):
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty("IsPlayable","true")
        liz.setProperty("Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)

        
def setView(content, viewType):
        if content:
                xbmcplugin.setContent(int(sys.argv[1]), content)
        if ADDON.getSetting('auto-view') == 'true':#<<<----see here if auto-view is enabled(true) 
                xbmc.executebuiltin("Container.SetViewMode(%s)" % ADDON.getSetting(viewType) )#<<<-----then get the view type
                      
               
params=get_params()
url=None
name=None
mode=None
iconimage=None
date=None
description=None
page=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        iconimage=urllib.unquote_plus(params["iconimage"])
except:
        pass
try:        
        mode=int(params["mode"])
except:
        pass
try:
        play=urllib.unquote_plus(params["play"])
except:
        pass
try:
        date=urllib.unquote_plus(params["date"])
except:
        pass
try:
        description=urllib.unquote_plus(params["description"])
except:
        pass
try:        
        page=int(params["page"])
except:
        try:        
               page=params["page"]
        except:
               pass
   
        
#these are the modes which tells the plugin where to go
if mode==None or url==None or len(url)<1:
        CATEGORIES()
               
elif mode==2:
        PLAY_STREAM(name,url,iconimage,play,description)
        
elif mode==3:
        REPLAY()
        
elif mode==4:
        GENRES(name,url)

elif mode==5:
        OnDemand(url)


elif mode==6:
        OnDemandLinks(url)

elif mode==7:
        PlayOnDemand(url)         
        
elif mode==200:
        schedule(name,url,iconimage)
        
elif mode==201:
        fullguide(name,url,iconimage,description)
        
elif mode==202:
        Login()
        Show_Dialog()
        
elif mode==203:
   
        try:os.remove(cookie_jar)
        except:pass
        try:os.remove(cookie_amember)
        except:pass
        Show_Dialog()

elif mode==204:
        downloadchannel()      
        
elif mode==205:
        LOGOUT()


elif mode==501:
        worldlinks(name,url)  
        

elif mode==1999:
        EVENTS()        
        
elif mode==2001:
        ADDON.openSettings()

elif mode==2003:
        parseAPI(url)

elif mode==20003:
        SportsOnDemand(url) 
        
elif mode==2004:
        playAPI(name,url,iconimage)
        
elif mode==2005:
        schedule(url)

elif mode==2006:
        PremPass(url)

elif mode==2007:
        checksub()

elif mode==2008:
     resetpass()        

elif mode==2009:
     TryAgain()
     
elif mode==3000:
     SEARCH(url)

elif mode==3001:
     GetSearchLinks(name,url,iconimage,description)      


elif mode==3010:
     GetEpisodeLinks(name,url,iconimage,description) 

elif mode==3002:
     PLAY_DEMAND_STREAM(name,url,iconimage,description)

elif mode==3003:
     MySearch()

elif mode == 3004:
    
    favs = ADDON.getSetting('favs').split(",")
    try:
        favs.remove(name.lower())
        ADDON.setSetting('favs', ",".join(favs))
    except:pass

elif mode == 4000:
    OnDemandFirstCat()

elif mode == 4001:
    OnDemandSecondCat(url)

elif mode == 4002:
    OnDemandThirdCat(url,page)      
    
elif mode==10000:
     import update

    
elif mode==11000:
     import skininstall    

elif mode==12000:
     xbmc.executebuiltin('ActivateWindow(videos,plugin://script.icechannel)')
     
elif mode==16000:
     Tools()
     
elif mode==16001:
     import speedtest

elif mode==16002:
     ADDON.openSettings()

elif mode==16003:
     changeEnableHLS()

elif mode==16004:
     setSetting(description, page)
     
elif mode==16005:
     CheckUpdate()

elif mode==16006:
     Deletecache() 
else:
        #just in case mode is invalid 
        CATEGORIES()

               
xbmcplugin.endOfDirectory(int(sys.argv[1]))

