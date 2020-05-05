from selenium import webdriver
from bs4 import BeautifulSoup
import time
import re
import os
import json

driver = webdriver.Chrome('D:\Workspace\Python\Crawler\chromedriver.exe')
base_dir = os.path.dirname(os.path.abspath(__file__))

datas = []

for page in range(60, 65):
    path = "https://directg.net/game/game.html?page="
    driver.get(path + str(page))
    data = {}

    for i in range(1, 8):
        for j in range (1, 4):
            path = '//*[@class="browse-view-inner list-group-item"]/div[' + str(i*2 - 1) + ']/div[' + str(j) + ']/div/div/a'
            driver.find_element_by_xpath(path).click()
            #driver.implicitly_wait(2)
            #time.sleep(2)
            game_page = driver.page_source
            game_detail = BeautifulSoup(game_page, 'lxml')
            game_url = driver.current_url
            name = game_detail.find('div', attrs={'class': 'page-header'})
            g_name = name.select('h1 > span')
            game_name = re.sub('^ ', '', g_name[0].text)
            price_content = game_detail.find('div', attrs={'class': 'product-price salesprice'})
            prices = price_content.select('span')
            try:
                normal_price = re.sub('\t|\n|원|,| ', '', prices[1].text)
                sale_price = re.sub('\t|\n|,| ', '', prices[4].text)
            except:
                normal_price = '-1'
                sale_price = '-1'
            print(game_name, normal_price, sale_price)
            data = {'name': game_name, 'url': game_url, 'store_name':'다이렉트 게임즈', 'normal_price': int(normal_price), 'sale_price': int(sale_price)}
            datas.append(data)
            driver.back()
            #driver.implicitly_wait(2)
            #time.sleep(2)
            print(page, i, j)
            if ((i == 7 and j == 2) or (page == 64 and i == 4 and j == 1)):
                break
        if (page == 64 and i == 4 and j == 1):
            break

with open(os.path.join(base_dir, 'result_temp.json'), 'w+', encoding='utf-8') as file:
    json.dump(datas, file, ensure_ascii=False, indent='\t')
