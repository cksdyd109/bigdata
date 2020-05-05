from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import requests
import time
import re
import os
import json

driver = webdriver.Chrome('D:\Workspace\Python\Crawler\chromedriver.exe')
base_dir = os.path.dirname(os.path.abspath(__file__))

datas = []

path = 'https://www.greenmangaming.com/bestsellers/'
game_page_url = 'https://www.greenmangaming.com'
driver.get(path)

# for page in range(1, 2):

gmae_page = driver.page_source
game_inform = BeautifulSoup(gmae_page, 'lxml')
driver.implicitly_wait(5)
time.sleep(3)
try:
    for i in range(0, 655):
        driver.switch_to.window(driver.window_handles[0])
        y = 500*i + 250
        #driver.execute_script("window.scrollTo(0, " + str(y) + ");")
        time.sleep(2)
        if (i != 0):
            driver.find_element_by_xpath('//*[@class="load-more"]').click()
        driver.implicitly_wait(3)
        time.sleep(2)
        driver.implicitly_wait(3)
        for j in range(10*i + 1, 10*(i+1)+1):
            if (i == 654 and j == 6548):
                break
            data = {}
            driver.implicitly_wait(3)
            time.sleep(2)
            driver.switch_to.window(driver.window_handles[0])
            p = '//*[@class="table-search-listings"]/li[' + str(10+j) + ']/div/div/div/a'
            element = driver.find_element_by_xpath(p)
            ActionChains(driver).key_down(Keys.CONTROL).click(element).key_up(Keys.CONTROL).perform()
            time.sleep(2)
            driver.switch_to.window(driver.window_handles[1])
            driver.implicitly_wait(3)
            time.sleep(2)
            page = driver.page_source
            inform = BeautifulSoup(page, 'lxml')
            game_url = driver.current_url
            try:
                name = inform.find('h1', attrs={'ng-bind': 'product.name'})
                game_name = re.sub('^ ', '', name.text)
                try:
                    prices = inform.find('div', attrs={'class': 'prices-details'})
                    price = prices.findAll('span')
                    #print(price)
                    normal_price = re.sub('\t|\n|원|,|₩| ', '', price[0].text)
                    try:
                        #-------할인 가격--------
                        sale_price = re.sub('\t|\n|원|,|₩| ', '', price[3].text)
                    except:
                        #--------일반 가격---------
                        sale_price = normal_price
                    if (normal_price == 'KRW'):
                        normal_price = '-1'
                        sale_price = '-1'
                except AttributeError as e:
                    normal_price = '-1'
                    sale_price = '-1'
                print(game_name, normal_price, sale_price)
                #driver.find_element_by_xpath(p).click()
                driver.close()
                data = {'name': game_name, 'url': game_url, 'store_name': 'gmg', 'normal_price': int(normal_price),
                        'sale_price': int(sale_price)}
                datas.append(data)
                print(j)
            except:
                pass
except:
    with open(os.path.join(base_dir, 'result_temp.json'), 'w+', encoding='utf-8') as file:
        json.dump(datas, file, ensure_ascii=False, indent='\t')
with open(os.path.join(base_dir, 'result_temp.json'), 'w+', encoding='utf-8') as file:
    json.dump(datas, file, ensure_ascii=False, indent='\t')