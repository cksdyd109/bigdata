from selenium import webdriver
from bs4 import BeautifulSoup
import time
import re
import os
import json
import math

driver = webdriver.Chrome('D:\Workspace\Python\Crawler\chromedriver.exe')
base_dir = os.path.dirname(os.path.abspath(__file__))

datas = []
page_data = []
temp = 99
check = False

for k in range(1, 300):
    page = temp
    if (page == 107):
        break
    path = "https://www.humblebundle.com/store/search?sort=bestselling&page="
    driver.get(path + str(page))
    game_page = driver.page_source
    game_lists = BeautifulSoup(game_page, 'lxml')
    driver.implicitly_wait(2)
    time.sleep(1)
    games = game_lists.find('ul', attrs={'class': 'entities-list js-entities-list no-style-list full js-full'})
    game = games.findAll('li')
    driver.implicitly_wait(2)
    time.sleep(1)
    for i in range(0, len(game)):
        data = {}
        try:
            gurl = 'https://www.humblebundle.com'
            game_info = game[i].find('a', attrs={'class': 'entity-link js-entity-link'})
            game_name = game[i].find('span', attrs={'class': 'entity-title'}).text
            game_url = gurl + game_info.attrs['href']
            try:
                dis_per_text = game[i].find('span', attrs={'class': 'discount-percentage'}).text
                sale_per = int(re.sub('%|\t|\n|원|,|₩| ', '', dis_per_text))
            except:
                sale_per = 0
            s_price = game[i].find('span', attrs={'class': 'price'}).text
            temp_sale_price = float(re.sub('\t|\n|원|,|₩| |[$]', '', s_price))
            if (sale_per == -100):
                sale_per = -99.99
            normal_price = temp_sale_price / ((100 + sale_per)/100) * 1200
            sale_price = temp_sale_price * 1200
            data = {'name': game_name, 'url': game_url, 'store_name': 'humblebundle', 'normal_price': round(normal_price),
                    'sale_price': round(sale_price)}
            datas.append(data)
            print(game_name, normal_price, sale_price)
        except AttributeError as e:
            pass
    if (len(game) == 1):
        temp = page
    else:
        temp += 1
    print(page, len(game))

print(page_data)
with open(os.path.join(base_dir, 'result_temp.json'), 'w+', encoding='utf-8') as file:
    json.dump(datas, file, ensure_ascii=False, indent='\t')
