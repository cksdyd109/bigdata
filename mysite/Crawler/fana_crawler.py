from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import requests
import time
import re
import os
import json

driver = webdriver.Chrome('D:\Workspace\Python\Crawler\chromedriver.exe')
base_dir = os.path.dirname(os.path.abspath(__file__))

datas = []

for page in range(30, 40):
    path = "https://www.fanatical.com/ko/search?page="
    driver.get(path + str(page))
    data = {}
    driver.implicitly_wait(2)
    time.sleep(2)
    try:
        won_path = '//*[@class="mr-2 btn btn-secondary btn-sm"]'
        driver.find_element_by_xpath(won_path).click()
    except:
        pass

    for i in range(1, 37):
        if (i!=1 and i%8 == 1):
            # body = driver.find_element_by_tag_name('body')
            # body.send_keys(Keys.PAGE_DOWN)
            y = 850 * (i/8)
            driver.execute_script("window.scrollTo(0, " + str(y) + ");")
        # body = driver.find_element_by_tag_name('body')
        # body.send_keys(Keys.PAGE_DOWN)
        # body.send_keys(Keys.PAGE_DOWN)
        time.sleep(2)
        path = '//*[@class="ais-Hits__root"]/div[' + str(i) + ']/div/div[2]/div/div[2]/a'
        driver.implicitly_wait(2)
        try:
            driver.find_element_by_xpath(path).click()
            driver.implicitly_wait(2)
            time.sleep(2)
            game_page = driver.page_source
            game_detail = BeautifulSoup(game_page, 'lxml')
            game_url = driver.current_url
            try:
                #-------일반---------
                g_name = game_detail.find('h1', attrs={'class': 'product-name'})
                game_name = re.sub('^ ', '', g_name.text)
            except AttributeError as e:
                #-------스타 딜-----------
                name = game_detail.find('div', attrs={'class': 'purchase-info-title'})
                g_name = name.select('div > h1')
                game_name = re.sub('^ ', '', g_name[0].text)
                print('name', e)
            try:
                #-------할인 딜-------
                price_content = game_detail.find('div', attrs={'class': 'price-container'})
                prices = price_content.select('span')
                try:
                    #--------할인 딜-------
                    sale_price = re.sub('\t|\n|원|,|₩| ', '', prices[1].text)
                    normal_price = re.sub('\t|\n|원|,|₩| ', '', prices[3].text)
                except IndexError as e:
                    #------번들 일반 딜------
                    sale_price = '-1'
                    normal_price = re.sub('\t|\n|원|,|₩| ', '', prices[2].text)
            except IndexError as e:
                #-----일반 딜--------
                sale_price = '-1'
                normal_price = re.sub('\t|\n|원|,|₩| ', '', prices[1].text)
            except AttributeError as e:
                #-------스타 딜--------
                price_content = game_detail.find('div', attrs={'class': 'd-flex align-items-center justify-content-end'})
                prices = price_content.select('span')
                normal_price = re.sub('\t|\n|원|,|₩| ', '', prices[1].text)
                sale_price = re.sub('\t|\n|원|,|₩| ', '', prices[3].text)
            print(game_name, normal_price, sale_price)
            data = {'name': game_name, 'url': game_url, 'store_name': 'fanatical', 'normal_price': int(normal_price),
                    'sale_price': int(sale_price)}
            datas.append(data)
            print(page, i)
        except:
            pass

        driver.back()
with open(os.path.join(base_dir, 'result.json'), 'w+', encoding='utf-8') as file:
    json.dump(datas, file, ensure_ascii=False, indent='\t')
