from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import requests
import time
import re
import os
import json

# driver = webdriver.Chrome('D:\Workspace\Python\Crawler\chromedriver.exe')
base_dir = os.path.dirname(os.path.abspath(__file__))

datas = []

for page in range(237, 238):
    path = "https://www.indiegala.com/store/search?type=games&filter=windows&page="
    game_page = requests.get(path + str(page))
    data = {}
    # driver.implicitly_wait(2)
    time.sleep(2)
    # game_page = driver.page_source
    game_lists = BeautifulSoup(game_page.content, 'lxml')
    game_info = game_lists.findAll('div', attrs={'class': 'game-row overflow-auto'})
    for i in range(0, 2):
        url = 'https://www.indiegala.com'
        temp_url = game_info[i].find('div', attrs={'class': 'game-data-cont overflow-auto right palette-background-6'})
        gurl = temp_url.select('h3 > a')
        game_url = url + gurl[0].attrs['href']
        game_name = gurl[0].text
        game_name = re.sub('^Pre-Purchase ', '', game_name)
        temp_price = game_info[i].find('div', attrs={'class': 'buttons-cont right relative'})
        try:
            price_info = temp_price.find('div', attrs={'class': 'inner palette-border-2'})
            prices = price_info.select('div')
            np = re.sub('\t|\n|원|,| |[$]', '', prices[0].text)
            sp = re.sub('\t|\n|원|,| |[$]', '', prices[1].text)
            normal_price = float(np) * 1200
            sale_price = float(sp) * 1200
        except AttributeError as e:
            price_info = temp_price.select('div')
            np = re.sub('\t|\n|원|,| |[$]', '', price_info[0].text)
            normal_price = float(np) * 1200
            sale_price = normal_price
        print(game_name, normal_price, sale_price)
        data = {'name': game_name, 'url': game_url, 'store_name': 'indiegala', 'normal_price': int(normal_price),
                'sale_price': int(sale_price)}
        datas.append(data)

    print(page)

with open(os.path.join(base_dir, 'result_temp.json'), 'w+', encoding='utf-8') as file:
    json.dump(datas, file, ensure_ascii=False, indent='\t')
