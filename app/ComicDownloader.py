import requests
import bs4
from lzstring import LZString
import json
import os
import itertools
from PIL import Image
from io import BytesIO


class ComicDownloader(object):

    def __init__(self):
        self.sess = requests.Session()
        self.sess.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                          ' AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/70.0.3538.110 Safari/537.36'})
        self.root = 'app/static/comic/'
        self.comic_path = ''

    def download(self, url, comic_id, chapter_id):
        v = url
        js = self.parse_page(v)
        self.sess.headers.update({
            'Referer': v
        })

        now_dict = json.loads(self.parse_js(js))
        now_dict['comic_id'] = comic_id
        now_dict['chapter_id'] = chapter_id
        # print(now_dict)

        if not self.comic_path:
            self.comic_path = os.path.join(self.root, str(comic_id))
            print(self.comic_path)

            if not os.path.exists(self.comic_path):
                os.mkdir(self.comic_path)

        return self.download_img(now_dict)

    def parse_page(self, url):
        js = ''
        response = self.sess.get(url)
        soup = bs4.BeautifulSoup(response.text, 'html5lib')
        for _ in soup.find_all('script'):
            if _.text[0:6] == 'window':
                js = _.text
                break
        return js

    def parse_js(self, js):
        param = js[js.find('}(') + 2:-1]
        p1_end = param[1:].find('\'') + 1
        p1 = param[1:p1_end]
        param = param[p1_end + 2:]
        p2_end = param.find(',')
        p2 = int(param[:p2_end])
        param = param[p2_end + 1:]
        p3_end = param.find(',')
        p3 = int(param[:p3_end])
        param = param[p3_end + 2:]
        p4_end = param.find('\'')
        p4 = param[:p4_end]
        p5 = 0
        p6 = {}
        (p, a, c, k, e, d) = (p1, p2, p3, p4, p5, p6)
        k = LZString.decompressFromBase64(k).split('|');
        lenk = len(k)

        key = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        index = 0
        for i in key:
            d[i] = k[index] if k[index] else i
            index += 1
            if index == lenk:
                break
        if index != lenk:
            for i in itertools.product('123456789', '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'):
                tmp = i[0] + i[1]
                d[tmp] = k[index] if k[index] else tmp
                index += 1
                if index == lenk:
                    break

        # print('d: ', d)

        ac_list = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        now_rep = ''
        res = ''
        for i in p:
            if i in ac_list:
                now_rep += i
            else:
                res += d[now_rep] if now_rep in d else now_rep
                now_rep = ''
                res += i
        if now_rep:
            res += d[now_rep] if now_rep in d else now_rep
        res = res[res.find('{'):res.rfind('}') + 1]
        # print(res)

        return res

    def download_img(self, source):
        chapter_path = os.path.join(self.comic_path, str(source['chapter_id']))
        if not os.path.exists(chapter_path):
            os.mkdir(chapter_path)
        print(chapter_path)
        prefix = 'https://i.hamreus.com'
        prefix += source['path']
        cnt = 1
        result = []
        for f in source['files']:
            url = '{}{}?cid={}&md5={}'.format(prefix, f, source['cid'], source['sl']['md5'])
            print('Grabing {}...'.format(url))
            try_cnt = 0
            succ = False
            file_path = os.path.join(chapter_path, '{}.jpg.jpg'.format(cnt))

            if os.path.exists(file_path):
                # This file has been downloaded
                print('Pass {}.'.format(cnt))
                result.append(False)
            else:
                while not succ and try_cnt < 3:
                    try:
                        res = self.sess.get(url, timeout=9)
                        if res.status_code == 200:
                            img = Image.open(BytesIO(res.content))
                            img.save(file_path)
                            succ = True
                    except Exception as e:
                        print(e)
                        try_cnt += 1

                if succ:
                    print('Get {} success.'.format(cnt))
                    result.append(True)
                else:
                    result.append(False)
                    with open(os.path.join(self.comic_path, 'error.log'), 'a') as error_log:
                        error_log.writelines('{} get {} failed!\n'.format(source['cname'], cnt))
            # time.sleep(2)
            cnt += 1
        return result


if __name__ == '__main__':
    '''
    example:
    python down_comic.py --url=https://www.manhuagui.com/comic/17023/
    '''
    '''
    parser = argparse.ArgumentParser(description='Input download homepage')
    parser.add_argument('-u', '--url', metavar='url', dest='url', required=True, help='download homepage')
    args = parser.parse_args()
    downloader = ComicDownloader()
    downloader.download(args.url)
    '''
    downloader = ComicDownloader()
    downloader.download('https://www.manhuagui.com/comic/30718/412543.html', 1, 1)
