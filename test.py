#导入需要的库
import requests
from lxml import etree
import time
from openpyxl import Workbook
import json

# 主页地址
BASE_DOMAIN = 'http://www.dytt8.net'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36 Edg/125.0.0.0',
}


def get_detail_urls(url):
    """
    获取电影详情页面的url
    :param url: 每一页电影列表的地址url
    :return:
    """
    response = requests.get(url, headers=HEADERS)
    response.encoding = 'gbk'  # 设置正确的编码方式

    html_element = etree.HTML(response.text)

    # 获取所有电影详情页面的地址
    detail_urls = html_element.xpath('//table[@class="tbspan"]//a/@href')

    # 过滤掉“综合电影”导致的脏数据
    detail_urls = [BASE_DOMAIN + url for url in detail_urls if url != '/html/gndy/jddy/index.html']

    return detail_urls


def parse_detail_page(detail_url):
    """
    解析电影详情页面
    :param detail_url: 详情页面的地址
    :return: film字典
    """
    response = requests.get(detail_url, headers=HEADERS)
    response.encoding = 'gbk'  # 设置正确的编码方式

    html_element = etree.HTML(response.text)

    # 电影标题
    title = html_element.xpath('//div[@class="title_all"]//font[@color="#07519a"]/text()')[0]

    # Zoom标签
    zoom_element = html_element.xpath('//div[@id="Zoom"]')[0]

    # 电影封面和截图链接
    imgs = zoom_element.xpath(".//img/@src")
    cover = imgs[0] if imgs else ''
    screen_shot = imgs[1] if len(imgs) > 1 else ''

    # 获取Zoom标签下的所有文本数据
    infos = zoom_element.xpath('.//text()')

    # 解析电影详细信息
    year, country, type, rating, duration, director, actors, desc, download_url = '', '', '', '', '', '', [], '', ''

    for index, info in enumerate(infos):
        if info.startswith('◎年　　代'):
            year = info.replace('◎年　　代', '').strip()
        elif info.startswith('◎产　　地'):
            country = info.replace('◎产　　地', '').strip()
        elif info.startswith('◎类　　别'):
            type = info.replace('◎类　　别', '').strip()
        elif info.startswith('◎豆瓣评分'):
            rating = info.replace('◎豆瓣评分', '').strip()
        elif info.startswith('◎片　　长'):
            duration = info.replace('◎片　　长', '').strip()
        elif info.startswith('◎导　　演'):
            director = info.replace('◎导　　演', '').strip()
        elif info.startswith('◎主　　演'):
            actors.append(info.replace('◎主　　演', '').strip())
            for j in range(index + 1, len(infos)):
                if infos[j].startswith('◎简　　介'):
                    break
                actors.append(infos[j].strip())
        elif info.startswith('◎简　　介'):
            desc = info.replace('◎简　　介', '').strip()
            for j in range(index + 1, len(infos)):
                if infos[j].startswith('【下载地址】'):
                    break
                desc += infos[j].strip()

    # 下载地址
    download_url = html_element.xpath('//td[@bgcolor="#fdfddf"]/a/@href')[0].strip() if html_element.xpath(
        '//td[@bgcolor="#fdfddf"]/a/@href') else ''

    film = {
        'title': title,
        'cover': cover,
        'screen_shot': screen_shot,
        'year': year,
        'country': country,
        'type': type,
        'rating': rating,
        'duration': duration,
        'director': director,
        'actors': actors,
        'desc': desc,
        'download_url': download_url
    }

    return film


def spider():
    """
    爬虫的入口
    :return:
    """
    base_url = 'http://www.dytt8.net/html/gndy/dyzz/list_23_{}.html'

    films = []

    # 创建一个工作簿
    wb = Workbook()
    ws = wb.active

    # 添加表头
    headers = ['电影标题', '封面链接', '截图链接', '年代', '产地', '类别', '豆瓣评分', '片长', '导演', '演员', '简介', '下载链接']
    ws.append(headers)

    # 获取第1-2页的数据（示例中仅获取2页）
    for index in range(1, 3):
        print('开始爬第{}页'.format(index))

        # 电影列表的地址url
        url = base_url.format(index)

        # 获取当前页面包含的所有电影详情地址
        detail_urls = get_detail_urls(url)

        # 解析每一个电影的详情页面
        for detail_url in detail_urls:
            film = parse_detail_page(detail_url)
            films.append(film)

            # 写入Excel表格
            row_data = [
                film['title'], film['cover'], film['screen_shot'], film['year'], film['country'],
                film['type'], film['rating'], film['duration'], film['director'], '\n'.join(film['actors']),
                film['desc'], film['download_url']
            ]
            ws.append(row_data)

            # 暂停一段时间，以免请求过于频繁被封IP
            time.sleep(1)

    # 保存文件
    wb.save('电影详情.xlsx')

    # 将数据保存到data.json文件
    with open('data.json', 'w', encoding='utf-8') as json_file:
        json.dump(films, json_file, ensure_ascii=False, indent=4)

    print("数据已保存到电影详情.xlsx和data.json文件中。")


if __name__ == '__main__':
    spider()
