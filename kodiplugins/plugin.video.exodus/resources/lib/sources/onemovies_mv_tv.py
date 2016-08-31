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


import re,urllib,urlparse,json

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import cache
from resources.lib.modules import directstream


class source:
    def __init__(self):
        self.domains = ['123movies.to', '123movies.ru', 'yesmovies.to']
        self.base_link = 'http://123movies.ru'
        self.search_link = '/ajax/suggest_search'
        self.info_link = '/ajax/movie_load_info/%s'
        self.server_link = '/ajax/get_episodes/%s'
        self.embed_link = '/ajax/load_embed/%s'
        self.base_link2 = 'http://yesmovies.to'
        self.info_link2 = '/ajax/movie_get_info/%s.html'
        self.play_link2 = '/ajax/v2_movie_quick_play/%s/%s/%s.html'
        self.server_link2 = '/ajax/v3_movie_get_episodes/%s/%s/%s/%s.html'
        self.embed_link2 = '/ajax/movie_load_embed/%s.html'


    def movie(self, imdb, title, year):
        try:
            t = cleantitle.get(title)

            headers = {'X-Requested-With': 'XMLHttpRequest'}

            query = urllib.urlencode({'keyword': title})

            url = urlparse.urljoin(self.base_link, self.search_link)

            r = client.request(url, post=query, headers=headers)

            r = json.loads(r)['content']
            r = zip(client.parseDOM(r, 'a', ret='href', attrs = {'class': 'ss-title'}), client.parseDOM(r, 'a', attrs = {'class': 'ss-title'}))
            r = [i[0] for i in r if cleantitle.get(t) == cleantitle.get(i[1])][:2]
            r = [(i, re.findall('(\d+)', i)[-1]) for i in r]

            for i in r:
                try:
                    y, q = cache.get(self.onemovies_info, 9000, i[1])
                    if not y == year: raise Exception()
                    return urlparse.urlparse(i[0]).path
                except:
                    pass
        except:
            return


    def tvshow(self, imdb, tvdb, tvshowtitle, year):
        try:
            url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            return


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

            t = cleantitle.get(data['tvshowtitle'])
            year = re.findall('(\d{4})', premiered)[0]
            years = [str(year), str(int(year)+1), str(int(year)-1)]
            season = '%01d' % int(season)
            episode = '%01d' % int(episode)

            headers = {'X-Requested-With': 'XMLHttpRequest'}

            query = urllib.urlencode({'keyword': '%s - Season %s' % (data['tvshowtitle'], season)})

            url = urlparse.urljoin(self.base_link, self.search_link)

            r = client.request(url, post=query, headers=headers)

            r = json.loads(r)['content']
            r = zip(client.parseDOM(r, 'a', ret='href', attrs = {'class': 'ss-title'}), client.parseDOM(r, 'a', attrs = {'class': 'ss-title'}))
            r = [(i[0], re.findall('(.+?) - season (\d+)$', i[1].lower())) for i in r]
            r = [(i[0], i[1][0][0], i[1][0][1]) for i in r if len(i[1]) > 0]
            r = [i for i in r if t == cleantitle.get(i[1])]
            r = [i[0] for i in r if season == '%01d' % int(i[2])][:2]
            r = [(i, re.findall('(\d+)', i)[-1]) for i in r]

            for i in r:
                try:
                    y, q = cache.get(self.onemovies_info, 9000, i[1])
                    if not y in years: raise Exception()
                    return urlparse.urlparse(i[0]).path + '?episode=%01d' % int(episode)
                except:
                    pass
        except:
            return


    def onemovies_info(self, url):
        try:
            u = urlparse.urljoin(self.base_link, self.info_link)
            u = client.request(u % url)

            q = client.parseDOM(u, 'div', attrs = {'class': 'jtip-quality'})[0]

            y = client.parseDOM(u, 'div', attrs = {'class': 'jt-info'})
            y = [i.strip() for i in y if i.strip().isdigit() and len(i.strip()) == 4][0]

            return (y, q)
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []

            if url == None: return sources

            url = urlparse.urljoin(self.base_link, url)
            url = referer = url.replace('/watching.html', '')

            try: url, episode = re.findall('(.+?)\?episode=(\d*)$', url)[0]
            except: episode = None

            vid_id = re.findall('-(\d+)', url)[-1]

            quality = cache.get(self.onemovies_info, 9000, vid_id)[1].lower()
            if quality == 'cam' or quality == 'ts': quality = 'CAM'
            elif quality == 'hd': quality = 'HD'
            else: quality = 'SD'


            try:
                headers = {'X-Requested-With': 'XMLHttpRequest', 'Referer': url}

                u = urlparse.urljoin(self.base_link, self.server_link % vid_id)

                r = client.request(u, headers=headers)

                r = client.parseDOM(r, 'div', attrs = {'class': 'les-content'})
                r = zip(client.parseDOM(r, 'a', ret='onclick'), client.parseDOM(r, 'a'))
                r = [(i[0], ''.join(re.findall('(\d+)', i[1])[:1])) for i in r]

                if not episode == None:
                    r = [i[0] for i in r if '%01d' % int(i[1]) == episode]
                else:
                    r = [i[0] for i in r]

                r = [re.findall('(\d+),(\d+)', i) for i in r]
                r = [i[0][:2] for i in r if len(i) > 0]

                links = []

                links += [{'source': 'openload.co', 'url': self.embed_link % i[1], 'direct': False} for i in r if i[0] == '14']

                links += [{'source': 'videomega.tv', 'url': self.embed_link % i[1], 'direct': False} for i in r if i[0] == '13']

                links += [{'source': 'videowood.tv', 'url': self.embed_link % i[1], 'direct': False} for i in r if i[0] == '12']

                head = '|' + urllib.urlencode(headers)

                for i in links: sources.append({'source': i['source'], 'quality': quality, 'provider': 'Onemovies', 'url': urlparse.urljoin(self.base_link, i['url']) + head, 'direct': i['direct'], 'debridonly': False})
            except:
                pass


            try:
                u = urlparse.urljoin(self.base_link2, self.info_link2)
                u = client.request(u % vid_id)
                u = client.parseDOM(u, 'a', ret='href', attrs = {'class': 'btn.+?'})
                u = [i for i in u if 'http' in i][0]

                headers = {'X-Requested-With': 'XMLHttpRequest', 'Referer': u}

                vid_slug = re.findall('/movie/(.+?)-\d+\.html', u)[0]
                vid_type = 'movie' if episode == None else 'series'

                u = self.play_link2 % (vid_slug, vid_id, vid_type)
                u = urlparse.urljoin(self.base_link2, u)

                r = client.request(u, headers=headers)
                r = client.parseDOM(r, 'a', ret='href', attrs = {'title': 'View all episodes'})[0]

                show_id, episode_id, server_id = re.findall('-(\d+)/(\d+)-(\d+)/', r)[0]

                r = self.server_link2 % (show_id, server_id, episode_id, vid_type)
                r = urlparse.urljoin(self.base_link2, r)

                r = str(client.request(r, headers=headers))

                if episode == None:
                    r = client.parseDOM(r, 'li', ret='onclick')

                else:
                    r = zip(client.parseDOM(r, 'li', ret='onclick'), client.parseDOM(r, 'a', ret='title'))
                    r = [(i[0], ''.join(re.findall('(\d+)', i[1])[:1])) for i in r]
                    r = [i[0] for i in r if '%01d' % int(i[1]) == episode]

                r = [re.findall('(\d+),(\d+)', i) for i in r]
                r = [i[0][:2] for i in r if len(i) > 0]

                links = []

                links += [{'source': 'openload.co', 'url': self.embed_link2 % i[0], 'direct': False} for i in r if i[1] == '14']

                links += [{'source': 'videomega.tv', 'url': self.embed_link2 % i[0], 'direct': False} for i in r if i[1] == '13']

                links += [{'source': 'videowood.tv', 'url': self.embed_link2 % i[0], 'direct': False} for i in r if i[1] == '12']

                head = '|' + urllib.urlencode(headers)

                for i in links: sources.append({'source': i['source'], 'quality': quality, 'provider': 'Onemovies', 'url': urlparse.urljoin(self.base_link2, i['url']) + head, 'direct': i['direct'], 'debridonly': False})
            except:
                pass


            return sources
        except:
            return sources


    def resolve(self, url):

        try: headers = dict(urlparse.parse_qsl(url.rsplit('|', 1)[1]))
        except: headers = None

        url = url.split('|')[0]

        result = client.request(url, headers=headers)

        try:
            url = re.findall('"?file"?\s*=\s*"(.+?)"', result)
            url = [directstream.googletag(i) for i in url]
            url = [i[0] for i in url if len(i) > 0]

            u = []
            try: u += [[i for i in url if i['quality'] == '1080p'][0]]
            except: pass
            try: u += [[i for i in url if i['quality'] == 'HD'][0]]
            except: pass
            try: u += [[i for i in url if i['quality'] == 'SD'][0]]
            except: pass

            url = client.replaceHTMLCodes(u[0]['url'])

            if 'requiressl=yes' in url: url = url.replace('http://', 'https://')
            else: url = url.replace('https://', 'http://')
            return url
        except:
            pass

        try:
            url = json.loads(result)['embed_url']
            return url
        except:
            pass


