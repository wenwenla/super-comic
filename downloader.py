import json
import os
import requests
import bs4


FILE_ROOT = 'app/static/list/'
COVER_ROOT = 'app/static/cover/'
CONTENT_ROOT = 'app/static/intro/'


def load_(file_path):
    with open(file_path, 'rb') as f:
        return f.read().decode('utf8')


class IntroPageParser(object):

    def __init__(self):
        self.content = None
        self.soup = None

    def set_content(self, text):
        self.content = text
        self.soup = bs4.BeautifulSoup(text, 'html5lib')

    def parse_chapter(self):
        """:return list which introduce chapters"""
        root = self.soup.find_all('div', attrs={'class': 'chapter-list'})
        result = []
        for item in root:
            ul = item.find_all('ul')
            for u in ul:
                li = u.find_all('li')
                for fd in reversed(li):
                    result.append({
                        'url': fd.find('a')['href'],
                        'name': fd.find('a')['title']
                    })
        return result

    def parse_intro(self):
        """:return {rank, status, intro}"""
        result = {}
        rank = self.soup.find('div', attrs={'class': 'rank'}).text.strip()
        result['rank'] = rank[:-2]
        ul = self.soup.find('ul', attrs={'class': 'detail-list'})
        for index, data in enumerate(ul.find_all('li')):
            if index == 3:
                # print('status', data.text)
                result['status'] = data.text.strip()[5:]
        intro = self.soup.find('div', attrs={'id': 'intro-all'}).text.strip()
        result['intro'] = intro
        return result

    def parse(self):
        res = {}
        res.update({'chapter': self.parse_chapter()})
        res.update(self.parse_intro())
        return res


class Downloader(object):

    def __init__(self, base_url):
        pass

    @staticmethod
    def load_exist(file_path):
        return set(next(os.walk(file_path))[2])

    @staticmethod
    def get_list(page_count=10):
        session = requests.Session()
        session.headers.update({'origin': 'https://www.manhuagui.com',
                                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                                              'Chrome/71.0.3578.98 Safari/537.36'})
        url = 'https://www.manhuagui.com/list/index_p{}.html'
        exists = Downloader.load_exist(FILE_ROOT)

        page_count = min(page_count, 644)
        for i in range(1, page_count + 1):
            result = []
            if 'page{:03d}.txt'.format(i) in exists:
                continue

            try_cnt = 0
            ok = False
            page = None
            while not ok and try_cnt < 5:
                try:
                    page = session.get(url.format(i), timeout=9)
                    ok = True
                except requests.exceptions.ConnectTimeout as e:
                    print(e)
                    try_cnt += 1

            if ok:
                soup = bs4.BeautifulSoup(page.text, 'html5lib')
                root = soup.find('ul', attrs={'id': 'contList'})

                for li in root.find_all('li'):
                    link = li.find('a')
                    cover = link.find('img')
                    cover_src = cover.get('src', None)
                    if not cover_src:
                        cover_src = cover.get('data-src', None)
                    result.append({
                        'href': 'https://www.manhuagui.com' + link['href'],
                        'title': link['title'],
                        'cover': cover_src
                    })
            with open('static/list/page{:03d}.txt'.format(i), 'wb') as f:
                f.write(json.dumps(result, ensure_ascii=False).encode('utf8'))
            print('write page{:03d}.txt success'.format(i))

    @staticmethod
    def _download_pic(url, file_name):
        ok = False
        cnt = 0
        session = requests.Session()
        session.headers.update({'origin': 'https://www.manhuagui.com',
                                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                                              'Chrome/71.0.3578.98 Safari/537.36'})
        while not ok and cnt < 5:
            try:
                res = session.get(url, timeout=9)
                with open(file_name, 'wb') as out:
                    out.write(res.content)
                ok = True
            except Exception as e:
                print(e)
                cnt += 1
        return ok

    @staticmethod
    def _download_content(url, file_name):
        ok = False
        cnt = 0
        session = requests.Session()
        session.headers.update({'origin': 'https://www.manhuagui.com',
                                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                                              'Chrome/71.0.3578.98 Safari/537.36'})
        while not ok and cnt < 5:
            try:
                res = session.get(url, timeout=9)
                page = res.text
                with open(file_name, 'wb') as out:
                    out.write(page.encode('utf8'))
                ok = True
            except Exception as e:
                print(e)
                cnt += 1
        return ok

    @staticmethod
    def get_content():
        cnt = 1
        exist = Downloader.load_exist(CONTENT_ROOT)

        p = os.path.join(FILE_ROOT, 'out.txt')
        with open(p, 'rb') as j:
            data = json.loads(j.read().decode('utf8'))
            for d in data:
                url = d['href']
                file_name = '{}.html'.format(cnt)
                if file_name not in exist:
                    Downloader._download_content(url, os.path.join(CONTENT_ROOT, file_name))
                print('Download {} ok!'.format(cnt))
                cnt += 1

    @staticmethod
    def get_cover():
        cnt = 1
        exist = Downloader.load_exist(COVER_ROOT)

        p = os.path.join(FILE_ROOT, 'out.txt')
        with open(p, 'rb') as j:
            data = json.loads(j.read().decode('utf8'))
            for item in data:
                if '{}.jpg'.format(cnt) not in exist:
                    Downloader._download_pic(item['cover'], '{}{}.jpg'.format(COVER_ROOT, cnt))
                print('Download {} ok!'.format(cnt))
                cnt += 1

    @staticmethod
    def merge_list():
        rt, _, file = next(os.walk(FILE_ROOT))
        res = []
        for f in file:
            path = os.path.join(rt, f)
            with open(path, 'rb') as in_:
                data = json.loads(in_.read().decode('utf8'))
                res.extend(data)
        with open(FILE_ROOT + 'out.txt', 'wb') as out:
            out.write(json.dumps(res, ensure_ascii=False).encode('utf8'))


if __name__ == '__main__':
    # Downloader.get_list(644)
    # Downloader.merge_list()
    # Downloader.get_cover()
    # Downloader._download_content('https://www.manhuagui.com/comic/19785/', 'test.html')
    test = IntroPageParser()
    test.set_content(load_('test.html'))
    # print(test.parse_chapter())
    print(test.parse())
