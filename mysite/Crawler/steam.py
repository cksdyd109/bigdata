import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import json
import os
from pymongo import MongoClient
import time

client = MongoClient('localhost', 27017)
database = client.project
collection = database.games
genreList = ['Action','Adventure','Casual','Indie','Massively Multiplayer','Racing','RPG','Simulation','Sports','Strategy']


def steamCrawler(start, end):
    driver = webdriver.Chrome('D:\Workspace\Python\Crawler\\chromedriver')
    driver.implicitly_wait(3)  # 웹 자원 로드를 위해 3초까지 기다려 준다.

    for i in range(start, end + 1):
        driver.get('https://store.steampowered.com/games/#p=' + str(i) + '&tab=TopSellers')
        driver.implicitly_wait(5)  # 웹 자원 로드를 위해 3초까지 기다려 준다.
        time.sleep(3)
        for j in range(1, 16):
            path = '//*[@id="TopSellersRows"]/a[' + str(j) + ']'
            driver.find_element_by_xpath(path).click()
            driver.implicitly_wait(5)
            time.sleep(3)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            try:
                img = soup.find("img", class_="game_header_image_full").get('src')
                genres = soup.select(".details_block > a")
                game_genre = []
                for genre in genres:
                    for i in range(len(genreList)):
                        if(genre.text == genreList[i]):
                            game_genre.append(genre.text)

                description = soup.find("div", class_ = "game_description_snippet").text

                #sale check
                check = soup.find("div", class_="game_purchase_action_bg")
                discount = check.find("div", class_="discount_block")

                if discount is None:
                    normal_price = int(soup.find("div", class_="game_purchase_price").text.replace('₩ ', "").replace(",", ""))
                    sale_price = normal_price
                else:
                    normal_price = int(soup.find("div", class_="discount_original_price").text.replace('₩ ', "").replace(",", ""))
                    sale_price = int(soup.find("div", class_="discount_final_price").text.replace('₩ ', "").replace(",", ""))

                title = soup.find("div", class_ = "apphub_AppName").text
                developer = soup.find("div", id = "developers_list").text
                publisher = soup.find_all("div", class_ = "summary column")[2].text
                date = soup.find("div", class_ = "date").text
                url = driver.current_url

                collection.insert_one({
                    "title": title,
                    "img": img,
                    "description": description,
                    "genre" : game_genre,
                    "developer": developer,
                    "publisher": publisher,
                    "date": date,
                    "prices": [
                        {
                            "store_name": "steam",
                            "url": url,
                            "normal_price": normal_price,
                            "sale_price": sale_price
                        }
                    ]
                })
            except:
                print("")

            driver.back()


steamCrawler(0,96)