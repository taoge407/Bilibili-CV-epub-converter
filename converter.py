'''
todo
1. 从b站api中获取文集信息
2. 遍历所有文集
3. 剔除无用元素，打包epub
4. 如有可能，合并所有文集
'''
import os
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from ebooklib import epub
import time

rlId = 36436
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
    'Referer': 'https://www.bilibili.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9',

    'Cookie': 'buvid3=14315973-D650-A490-7CE8-DB027B37AEB368162infoc; b_nut=1768116368; b_lsid=AAC45DD9_19BABF2B0B3; _uuid=31D975A1-86C5-810CC-5B103-10BC2E1B65610367559infoc; buvid4=893A8AB6-E1A3-1613-E734-9A38EEE5B0C669631-026011115-Kd8ioH/4jFXnNx3bxmPt4Q%3D%3D; bmg_af_switch=1; bmg_src_def_domain=i0.hdslb.com; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjgzNzU1NjksImlhdCI6MTc2ODExNjMwOSwicGx0IjotMX0.e5RhQuVPwq6knQTSS8ARDE_jMseFN3SGW7tuE_n_sr8; bili_ticket_expires=1768375509; buvid_fp=77e4e584b296cd6bbf579947219f6e87; SESSDATA=7212ee90%2C1783668420%2C33dd6%2A12CjDWGrgX5WFH7dxmADxVDT779142AGCjdoiMxekJugAfQrNuCWh9Vn5hQxhSlbJYgMsSVmJrMHBOQnR2UnFQQ2Jka3pxTUZMVTBieGV4OEFlMXk1TzlTNTlJMFVLQm1ObmlJUkNsZ2NuRzdvY25jaFdwSmxmRERUdm9lQ2Q4STJObVR1MmVUQ3p3IIEC; bili_jct=53be9493c5fa3418208639af8d4d1678; DedeUserID=3546977543391411; DedeUserID__ckMd5=15d52563ef60469c; sid=81xyrdhc; CURRENT_FNVAL=2000; theme-tip-show=SHOWED; theme-avatar-tip-show=SHOWED; bp_t_offset_3546977543391411=1156542054663192576; home_feed_column=4; browser_resolution=1121-1614',
}


class ReadList:
    def __init__(self):
        self.article_ids = []
        self.cover_url  = None
        self.author = None
        self.name = None

    def fetch(self):
        global rlId, headers
        requestURL = "https://api.bilibili.com/x/article/list/web/articles?id=" + str(rlId)
        try:
            response = requests.get(requestURL, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 0:
                    print("got")
                    self.name = str(data['data']['list']['name'])
                    self.cover_url = str(data['data']['list']['image_url'])
                    self.author = str(data['data']['author']['name'])
                    for i in data['data']['articles']:
                        self.article_ids.append(str(i['dyn_id_str']))
        except Exception as e:
            print(e)
            exit()


class Opus_Article:
    def __init__(self, article_opus_id):
        self.images = []
        self.context = None
        self.title = None
        self.article_id = article_opus_id

    def fetch_content(self):
        opus_url = f"https://m.bilibili.com/opus/{self.article_id}?from=readlist"
        global headers
        try:
            os.makedirs("./cache", exist_ok=True)
            fn = f"./cache/{self.article_id}.txt"

            if os.path.isfile(fn):
                with open(fn, 'r') as f_content:
                    print(f"found article file {self.article_id}")
                    soup = BeautifulSoup(f_content.read(), 'html.parser')
            else:
                response = requests.get(opus_url, headers=headers)
                if response.status_code != 200:
                    raise Exception(f"无法访问页面id{self.article_id}，Code{response.status_code}")
                soup = BeautifulSoup(response.text, 'html.parser')
                with open(fn, 'w') as f_content:
                    f_content.write(response.text)
            self.title = soup.find("span", class_="opus-module-title__text").text.strip()
            content_div = soup.find("div", class_='opus-module-content opus-paragraph-children')
            if content_div:
                for p in soup.find_all("p"):
                    if p.find("span") is None:
                        p.decompose()
                for img in content_div.find_all("img"):

                    src = img.get('data-src') or img.get('src')
                    if src and not src.startswith('data:'):
                        # 处理相对路径
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = 'https://www.bilibili.com' + src
                    self.images.append(src)
                    src = "/images/image_" + str(src.split("/")[-1])

                self.context = str(content_div)
        except Exception as e:
            print(e)
            exit()

class Converter:
    def __init__(self, read_list: ReadList, articles: list[Opus_Article]):
        self.read_list = read_list

        self.article = articles

    def convert_epub(self):
        #print(f"Processing: {self.article.title}")
        #article_data = self.article.context

        ebook = epub.EpubBook()
        ebook.set_identifier(f"bilibili_rl_{rlId}")
        ebook.set_title(self.read_list.name)
        ebook.set_language("zh-CN")
        ebook.add_author(self.read_list.author)

        chapters = []
        index = 0
        image_urls_set = set()
        for chapter_article in self.article:
            chapter = epub.EpubHtml(
                title= chapter_article.title,
                file_name=f'article{index}.xhtml',
                lang='zh-CN'
            )
            chapter.content = f"""<html>
        <head>
            <title>{chapter_article.title}</title>
        </head>
        <body>
            <h1>{chapter_article.title}</h1>
            <hr></hr>
            {chapter_article.context}
        </body>
        </html>
        """.encode('utf-8')
            ebook.add_item(chapter)
            chapters.append(chapter)
            index += 1
            image_urls_set.update(chapter_article.images)

        for image_url in image_urls_set:
            try:
                image_data = download_image(url=image_url)
                if image_data:
                    ext = os.path.splitext(urlparse(image_url).path)[1].lower()
                    if ext in ['.jpg', '.jpeg']:
                        mime_type = 'image/jpeg'
                        file_ext = '.jpg'
                    elif ext == '.png':
                        mime_type = 'image/png'
                        file_ext = '.png'
                    elif ext == '.gif':
                        mime_type = 'image/gif'
                        file_ext = '.gif'
                    elif ext == '.webp':
                        mime_type = 'image/webp'
                        file_ext = '.webp'
                    else:
                        mime_type = 'image/jpeg'
                        file_ext = '.jpg'

                    img_id = image_url.split('/')[-1].split('.')[0]
                    image_item = epub.EpubImage(
                        uid=f"img_{img_id}",
                        file_name=f"images/image_{img_id}{file_ext}",
                        media_type=mime_type,
                        content=image_data,
                    )
                    ebook.add_item(image_item)
                    print(f"添加图片{img_id}")
            except Exception as e:
                print(e)
        ebook.toc = [(epub.Section('文集'), chapters)]
        ebook.add_item(epub.EpubNcx())
        ebook.add_item(epub.EpubNav())
        ebook.spine = ['nav'] + chapters

        # 写入文件
        epub.write_epub(f".\\rl{rlId}.epub", ebook, {})

def download_image(url) -> bytes:
    img_id = url.split('/')[-1].split('.')[0]
    os.makedirs("./images_cache/", exist_ok=True)
    fn = f"./images_cache/{img_id}"
    if os.path.exists(fn):
        with open(fn, 'rb') as f:
            print(f"found img file {img_id}")
            return f.read()

    try:
        response = requests.get(url, headers={
            'Referer': 'https://www.bilibili.com/',
            'User-Agent': headers['User-Agent']
        })
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type:
            print(f" {url} 不是图片 (Content-Type: {content_type})")
            return None
        with open(fn, 'wb') as f:
            f.write(response.content)
        return response.content
    except Exception as e:
        print(e)


print("get rl info:")
readlist = ReadList()
readlist.fetch()

articles = []
print("sss" + str(readlist.article_ids))
for opus_id in readlist.article_ids:
    article = Opus_Article(opus_id)
    print(f"getting opus id{opus_id}")
    article.fetch_content()
    articles.append(article)
    time.sleep(1)
c = Converter(readlist, articles)
c.convert_epub()
