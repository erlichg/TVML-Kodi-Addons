'''
    Movreel.com Host resolver
    for Istream ONLY
    18/01/2014

    Jas0npc

    Big thanks to all that has guided me on my XBMC Journey.

    A thank you to all members of the Xunity team.

    (c)2014 Xunity.

    This resolver IS NOT OPEN SOURCE, It is to be used as
    part of Istream ONLY.

    version 0.3
'''
import net,re

net=net.Net()

def solve(url):
    html = net.http_GET(url)
    import time
    time.sleep(2)
    html=html.content
    postData = {}
    for item in re.finditer(r'\"\sname\=\"(.*?)\"\svalue=\"?(.*?)\"',html,re.I):
        postData.update({str(item.group(1)):str(item.group(2))})

    if postData:
        URL=net.http_POST(url,postData,headers={'Content-Type':'application/x-www-form-urlencoded',
                                                   'Referer':str(url),'Origin':'http://movreel.com',
                                                   'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}).content
       
        LINK=URL.split('<a href')
        for p in LINK:
            d =p.split('<')[0]
            if 'download link' in d.lower():
                finalLink=re.compile('="(.+?)"').findall(d)[0]
               

                
                if finalLink:
                    return finalLink

        


