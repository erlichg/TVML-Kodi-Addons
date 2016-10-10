# -*- coding: utf-8 -*-

'''
    Exodus Add-on
    Copyright (C) 2016 Exodus

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import re,urllib,urlparse,json,base64

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import directstream


class source:
    def __init__(self):
        self.domains = ['pelispedia.tv']
        self.base_link = 'http://www.pelispedia.tv'
        self.search_link = 'aHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vY3VzdG9tc2VhcmNoL3YxZWxlbWVudD9rZXk9QUl6YVN5Q1ZBWGlVelJZc01MMVB2NlJ3U0cxZ3VubU1pa1R6UXFZJnJzej1maWx0ZXJlZF9jc2UmbnVtPTEwJmhsPWVuJmN4PTAxMzA0MzU4NDUzMDg1NzU4NzM4MTpkcGR2Y3FlbGt3dyZnb29nbGVob3N0PXd3dy5nb29nbGUuY29tJnE9JXM='


    def movie(self, imdb, title, year):
        try:
            t = cleantitle.get(title)

            query = '%s %s' % (title, year)
            query = base64.b64decode(self.search_link) % urllib.quote_plus(query)

            result = client.request(query)
            result = json.loads(result)['results']

            result = [(i['url'], i['titleNoFormatting']) for i in result]
            result = [(i[0], re.findall('(?:^Ver |)(.+?)(?: HD |)\((\d{4})', i[1])) for i in result]
            result = [(i[0], i[1][0][0], i[1][0][1]) for i in result if len(i[1]) > 0]

            r = [i for i in result if t == cleantitle.get(i[1]) and year == i[2]]

            if len(r) == 0:
                t = 'http://www.imdb.com/title/%s' % imdb
                t = client.request(t, headers={'Accept-Language':'es-ES'})
                t = client.parseDOM(t, 'title')[0]
                t = re.sub('(?:\(|\s)\d{4}.+', '', t).strip()
                t = cleantitle.get(t)

                r = [i for i in result if t == cleantitle.get(i[1]) and year == i[2]]

            try: url = re.findall('//.+?(/.+)', r[0][0])[0]
            except: url = r[0][0]
            try: url = re.findall('(/.+?/.+?/)', url)[0]
            except: pass
            url = client.replaceHTMLCodes(url)
            url = url.encode('utf-8')

            return url
        except:
            pass


    def tvshow(self, imdb, tvdb, tvshowtitle, year):
        try:
            t = cleantitle.get(tvshowtitle)

            query = '%s %s' % (tvshowtitle, year)
            query = base64.b64decode(self.search_link) % urllib.quote_plus(query)

            result = client.request(query)
            result = json.loads(result)['results']

            result = [(i['url'], i['titleNoFormatting']) for i in result]
            result = [(i[0], re.findall('(?:^Ver Serie|^Ver |)(.+?)(?: HD |)\((\d{4})', i[1])) for i in result]
            result = [(i[0], i[1][0][0], i[1][0][1]) for i in result if len(i[1]) > 0]
            result = [i for i in result if '/serie/' in i[0]]

            r = [i for i in result if t == cleantitle.get(i[1]) and year == i[2]]

            if len(r) == 0:
                t = 'http://www.imdb.com/title/%s' % imdb
                t = client.request(t, headers={'Accept-Language':'es-ES'})
                t = client.parseDOM(t, 'title')[0]
                t = re.sub('\((?:.+?|)\d{4}.+', '', t).strip()
                t = cleantitle.get(t)

                r = [i for i in result if t == cleantitle.get(i[1]) and year == i[2]]

            try: url = re.findall('//.+?(/.+)', r[0][0])[0]
            except: url = r[0][0]
            try: url = re.findall('(/.+?/.+?/)', url)[0]
            except: pass
            url = client.replaceHTMLCodes(url)
            url = url.encode('utf-8')

            return url
        except:
            return


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        if url == None: return

        url = [i for i in url.split('/') if not i == ''][-1]
        url = '/pelicula/%s-season-%01d-episode-%01d/' % (url, int(season), int(episode))
        url = client.replaceHTMLCodes(url)
        url = url.encode('utf-8')
        return url


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []

            if url == None: return sources

            r = urlparse.urljoin(self.base_link, url)

            result = client.request(r)

            f = client.parseDOM(result, 'iframe', ret='src')
            f = [i for i in f if 'iframe' in i][0]

            result = client.request(f, headers={'Referer': r})

            r = client.parseDOM(result, 'div', attrs = {'id': 'botones'})[0]
            r = client.parseDOM(r, 'a', ret='href')
            r = [(i, urlparse.urlparse(i).netloc) for i in r]
            r = [i[0] for i in r if 'pelispedia' in i[1]]

            links = []

            for u in r:
                result = client.request(u, headers={'Referer': f})

                try:
                    url = re.findall('sources\s*:\s*\[(.+?)\]', result)[0]
                    url = re.findall('"file"\s*:\s*"(.+?)"', url)
                    url = [i.split()[0].replace('\\/', '/') for i in url]

                    for i in url:
                        try: links.append({'source': 'gvideo', 'quality': directstream.googletag(i)[0]['quality'], 'url': i})
                        except: pass
                except:
                    pass

                try:
                    headers = {'X-Requested-With': 'XMLHttpRequest', 'Referer': u}

                    post = re.findall('gkpluginsphp.*?link\s*:\s*"([^"]+)', result)[0]
                    post = urllib.urlencode({'link': post})

                    url = urlparse.urljoin(self.base_link, '/Pe_flv_flsh/plugins/gkpluginsphp.php')
                    url = client.request(url, post=post, headers=headers)
                    url = json.loads(url)['link']

                    links.append({'source': 'gvideo', 'quality': 'HD', 'url': url})
                except:
                    pass

                try:
                    headers = {'X-Requested-With': 'XMLHttpRequest'}

                    post = re.findall('var\s+parametros\s*=\s*"([^"]+)', result)[0]
                    post = urlparse.parse_qs(urlparse.urlparse(post).query)['pic'][0]
                    post = urllib.urlencode({'sou': 'pic', 'fv': '21', 'url': post})

                    url = urlparse.urljoin(self.base_link, '/Pe_Player_Html5/pk/pk/plugins/protected.php')
                    url = client.request(url, post=post, headers=headers)
                    url = json.loads(url)[0]['url']

                    links.append({'source': 'cdn', 'quality': 'HD', 'url': url})
                except:
                    pass

            for i in links: sources.append({'source': i['source'], 'quality': i['quality'], 'provider': 'Pelispedia', 'url': i['url'], 'direct': True, 'debridonly': False})

            return sources
        except:
            return sources


    def resolve(self, url):
        return url


