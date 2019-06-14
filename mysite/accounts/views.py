from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from pymongo import MongoClient
from matplotlib import pylab
from matplotlib import font_manager, rc
from pylab import *
import PIL, PIL.Image
import io
import base64
from django.views import generic
import re
import numpy as np
from scipy.stats import pearsonr
import math

client = MongoClient('localhost', 27017)
database = client.project
collection = database.gameinforms
user_coll = database.user

game_name = ""
genre = ""
tempgame_genre = "temp"
tempgame_publ = "temp"

font_name = font_manager.FontProperties(fname='c:/Windows/Fonts/malgun.ttf').get_name()
rc('font', family=font_name)

# Create your views here.
class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

def login(request):
    return render(request, 'registration/login.html')


def mypage(request):
    genCount = {'Action': 0, 'Adventure': 0, 'Casual': 0, 'Indie': 0, 'MassivelyMultiplayer': 0, 'Racing': 0, 'RPG': 0,
                'Simulation': 0, 'Sports': 0, 'Strategy': 0}
    if (user_coll.find_one({"_id": request.user.username}) is None):
        return render(request, 'content/mypage.html', {'check': 1})
    genre_results = user_coll.find_one({"_id": request.user.username})['games']
    genList = []
    genValue = []

    for result in genre_results:
        for genre in result['genre']:
            genCount[genre] += 1

    for genre in genCount:
        if genCount[genre] != 0:
            genList.append(genre)
            genValue.append(genCount[genre])

    fig = plt.figure(figsize=(12, 6))
    ax1 = fig.add_subplot(1, 3, 1)
    title("Genre", position=(0.5, 0.8))
    ax1.title.set_size(20)
    ax1.pie(genValue, labels=genList, autopct='%1.1f%%', shadow=False, startangle=90)
    ax1.axis('equal')

    publisher_dic = dict()
    publisher_results = user_coll.find_one({"_id": request.user.username})['games']

    for result in publisher_results:
        for publisher in result['publisher']:
            if publisher in publisher_dic:
                publisher_dic[publisher] += 1
            else:
                publisher_dic[publisher] = 1


    ax2 = fig.add_subplot(1, 3, 3)
    title("Publisher", position=(0.5, 0.8))
    ax2.title.set_size(20)
    ax2.pie(publisher_dic.values(), labels=publisher_dic.keys(), autopct='%1.1f%%', shadow=False, startangle=90)
    ax2.axis('equal')

    buffer = io.BytesIO()
    canvas = pylab.get_current_fig_manager().canvas
    canvas.draw()
    pilImage = PIL.Image.frombytes("RGB", canvas.get_width_height(), canvas.tostring_rgb())
    pilImage.save(buffer, "PNG")
    graphic = buffer.getvalue()
    graphic = base64.b64encode(graphic)
    graphic = graphic.decode('utf-8')

    return render(request, 'content/mypage.html', {'graphic': graphic})

def main(request):
    games = []
    username = request.user.username
    if (username == "" or username == None or user_coll.find({'_id':username}).count() == 0):
        informs = collection.find({}, {'_id': 0}).limit(6).sort('date', -1)
    else:
        min1 = []
        min2 = []

        pipelines = list()
        pipelines.append({'$unwind': "$games"})
        pipelines.append({'$unwind': "$games.genre"})
        pipelines.append({'$project': {'_id': 1, 'test': "$games.genre"}})
        pipelines.append({'$group': {'_id': "$_id", 'genres': {'$push': "$test"}}})
        pipelines.append({'$match': {'_id': username}})

        matrix = np.empty((0, 10))
        forCount = ['Action', 'Adventure', 'Casual', 'Indie', 'Massively Multiplayer', 'Racing', 'RPG', 'Simulation',
                    'Sports', 'Strategy']
        results = user_coll.aggregate(pipelines)
        for result in results:
            user = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])
            for i in range(len(result['genres'])):
                for j in range(len(forCount)):
                    if (result['genres'][i] == forCount[j]):
                        user[0][j] = user[0][j] + 1
            matrix = np.append(matrix, user, axis=0)

        del pipelines[-1]
        pipelines.append({'$match': {'_id': {'$ne':username}}})
        results = user_coll.aggregate(pipelines)

        for result in results:
            user = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])
            for i in range(len(result['genres'])):
                for j in range(len(forCount)):
                    if (result['genres'][i] == forCount[j]):
                        user[0][j] = user[0][j] + 1
            matrix = np.append(matrix, user, axis=0)

        for i in range(1, len(matrix)):
            corr = pearsonr(matrix[0], matrix[i])
            if (i == 1):
                min1 = [i, corr]
                min2 = min1
            elif (i > 1):
                if (min1[1][1] > corr[1]):
                    min2 = min1
                    min1 = [i, corr]
                elif (min2[1][1] > corr[1]):
                    min2 = [i, corr]

        max = 0
        for i in range(len(forCount)):
            avg = (matrix[min1[0]][i]+matrix[min2[0]][i])/2
            if (max < avg):
                max = i

        informs = collection.find({'genre': {'$all': [forCount[max]]}}, {'_id': 0}).limit(6).sort('date', -1)

    for inform in informs:
        games.append(inform)
    return render(request, 'content/index.html', {'games':games})

def like(request):
    like_games = []
    if (user_coll.find({'_id':request.user.username}).count() != 0):
        results = user_coll.find_one({'_id': request.user.username})['games']
        for result in results:
            like_games.append(result)
    return render(request, 'content/like.html',{'like_games':like_games})

def remove(request):
    user = request.user.username
    game_genre = []
    like_games = []
    if (request.method == 'POST'):
        game_name = request.POST.get('gameName')
        game_Img = request.POST.get('gameImg')
        tempgame_genre = request.POST.get('gameGenre')

        try:
            tempgame_genre = re.sub("\'|\[|\]| |temp", '', tempgame_genre)
            tempStr = tempgame_genre.split(',')
            for temp in tempStr:
                game_genre.append(temp)
        except:
            pass

        user_coll.update(
            {'_id' : user},
            {'$pull': {'games':{"title" : game_name, "img" : game_Img, "genre" : game_genre }}}
        )
    results = user_coll.find_one({'_id': request.user.username})['games']
    for result in results:
        like_games.append(result)        
    
    return render(request, 'content/like.html',{'like_games':like_games})

def glist(request):
    PAGE_ROW_COUNT = 10
    PAGE_DISPLAY_COUNT = 5
    games = []
    searching = ""
    if (request.method == 'POST'):
        searching = request.POST.get('searching')
    informs = collection.find({'title': {'$regex': searching, '$options': 'i'}}, {'_id': 0}).sort('date', -1)
    for inform in informs:
        games.append(inform)

    paginator = Paginator(games, PAGE_ROW_COUNT)
    pageNum = request.GET.get('pageNum')

    totalPageCount = paginator.num_pages

    try:
        member_list = paginator.page(pageNum)
    except PageNotAnInteger:
        member_list = paginator.page(1)
        pageNum = 1
    except EmptyPage:
        member_list = paginator.page(paginator.num_pages)
        pageNum = paginator.num_pages

    pageNum = int(pageNum)

    startPageNum = 1 + ((pageNum-1) / PAGE_DISPLAY_COUNT) * PAGE_DISPLAY_COUNT
    endPageNum = startPageNum + PAGE_DISPLAY_COUNT - 1
    if (totalPageCount < endPageNum):
        endPageNum = totalPageCount

    bottomPages = range(int(startPageNum), int(endPageNum) + 1)

    return render(request, 'content/gamelist.html',
                  {
                      'games': member_list,
                      'pageNum': int(pageNum),
                      'bottomPages': bottomPages,
                      'totalPageCount': int(totalPageCount),
                      'startPageNum': int(startPageNum),
                      'endPageNum': int(endPageNum)
                  })

def genrelist(request):
    global genre
    PAGE_ROW_COUNT = 10
    PAGE_DISPLAY_COUNT = 5
    games = []
    searching = ""
    tempGenre = ""
    if (request.method == 'POST'):
        tempGenre = request.POST.get('genre')
        searching = request.POST.get('searching')
    if (tempGenre != '' and tempGenre != None):
        genre = tempGenre
    if (searching == None):
        searching = ''

    informs = collection.find({'title': {'$regex': searching, '$options': 'i'}, 'genre': {'$all': [genre]}}, {'_id': 0}).sort('date', -1)
    for inform in informs:
        games.append(inform)

    paginator = Paginator(games, PAGE_ROW_COUNT)
    pageNum = request.GET.get('pageNum')

    totalPageCount = paginator.num_pages

    try:
        member_list = paginator.page(pageNum)
    except PageNotAnInteger:
        member_list = paginator.page(1)
        pageNum = 1
    except EmptyPage:
        member_list = paginator.page(paginator.num_pages)
        pageNum = paginator.num_pages

    pageNum = int(pageNum)

    startPageNum = 1 + ((pageNum-1) / PAGE_DISPLAY_COUNT) * PAGE_DISPLAY_COUNT
    endPageNum = startPageNum + PAGE_DISPLAY_COUNT - 1
    if (totalPageCount < endPageNum):
        endPageNum = totalPageCount

    bottomPages = range(int(startPageNum), int(endPageNum) + 1)

    return render(request, 'content/genrelist.html',
                  {
                      'games': member_list,
                      'pageNum': int(pageNum),
                      'bottomPages': bottomPages,
                      'totalPageCount': int(totalPageCount),
                      'startPageNum': int(startPageNum),
                      'endPageNum': int(endPageNum),
                      'genre': genre
                  })

def game(request):
    global game_name
    global tempgame_genre
    global tempgame_publ
    game = []
    game_genre = []
    game_pub = []
    game_img = ""
    checkUpdate = False
    if (request.method == 'POST'):
        game_name = request.POST.get('gameName')
        game_img = request.POST.get('gameImg')
        tempgame_genre = request.POST.get('gameGenre')
        tempgame_publ = request.POST.get('gamePublisher')
        delete_check = request.POST.get('deleteCheck')
    if (game_img != "" and game_img != None):
        checkUpdate = True
    nameStr = '^' + game_name + '$'

    informs = collection.find({'title': {'$regex': nameStr}}).limit(1)
    # siteinform = othersites.find({'_id': {'$regex': game_name, '$options': 'i'}}).limit(1)
    
    for inform in informs:
        game = inform
    try:
        tempgame_genre = re.sub("\'|\[|\]| |temp", '', tempgame_genre)
        tempStr = tempgame_genre.split(',')
        for temp in tempStr:
            game_genre.append(temp)
    except:
        pass
    temppub = ""
    try:
        tempgame_publ = re.sub("\'|\[|\]| |temp|\(Mac\)|\(Linux\)", '', tempgame_publ)
        tempstr = tempgame_publ.split(',')
        for temp in tempstr:
            match = re.match('Ubisoft', temp)
            if (match or re.match('Assassin', game_name)):
                temp = "Ubisoft"
            if (temp == temppub):
                continue
            game_pub.append(temp)
            temppub = temp
    except:
        pass

    other_page = []
    other_prices = []
    for temp in game['prices']:
        if (temp['normal_price'] == -1):
            continue
        elif (temp['sale_price'] == -1):
            other_prices.append(temp['normal_price'])
            other_page.append(temp['store_name'])
        else:
            other_prices.append(temp['sale_price'])
            other_page.append(temp['store_name'])

    fig = plt.figure()
    ax1 = fig.add_subplot(1,1,1)
    ax1.bar(other_page, other_prices, align='center', width=0.2, color='#ff6666')

    buffer2 = io.BytesIO()
    canvas2 = pylab.get_current_fig_manager().canvas
    canvas2.draw()
    pilImage2 = PIL.Image.frombytes("RGB", canvas2.get_width_height(), canvas2.tostring_rgb())
    pilImage2.save(buffer2, "PNG")
    graphic2 = buffer2.getvalue()
    graphic2 = base64.b64encode(graphic2)
    graphic2 = graphic2.decode('utf-8')

    # a = game[0]['prices']

    user = request.user.username
    user_check = user_coll.find({'_id':user, 'games.title': game_name}).count()
    if (checkUpdate and delete_check == '0'):
        if(user_coll.find({'_id':user}).count() == 0 ):
            user_coll.insert_one({'_id': user, 'games': [{'title': game_name, 'img': game_img, 'genre':game_genre, 'publisher':game_pub}]})
        else:
            user_coll.update_one({'_id': user}, {'$push': {'games': {'title': game_name, 'img': game_img, 'genre':game_genre, 'publisher':game_pub}}})
        
        user_check = user_coll.find({'_id': user, 'games.title': game_name}).count()
    elif (delete_check == '1'):
        user_coll.update_one({'_id': user}, {'$pull': {'games': {'title': game_name, 'img': game_img, 'genre':game_genre, 'publisher':game_pub}}})
        user_check = user_coll.find({'_id': user, 'games.title': game_name}).count()

    return render(request, 'content/gamedetail.html', {'game': game, 'usered':user,
                                                       'userCheck': user_check, 'test': game_genre, 'graphic': graphic2})

