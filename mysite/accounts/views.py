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
import math

client = MongoClient('localhost', 27017)
database = client.project
collection = database.games
othersites = database.othersite
user_coll = database.user

game_name = ""
genre = ""
tempgame_genre = "temp"

font_name = font_manager.FontProperties(fname='c:/Windows/Fonts/malgun.ttf').get_name()
rc('font', family=font_name)

# Create your views here.
class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

def login(request):
    return render(request, 'registration/login.html')

def main(request):
    games = []
    username = request.user.username
    if (username == "" or username == None or user_coll.find().count() == 0):
        informs = collection.find({}, {'_id': 0}).limit(6)
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

        for i in range(len(matrix)):
            result = 0.0
            sum = 0
            for j in range(len(matrix[i])):
                if (matrix[0][j] == 0):
                    continue
                print(forCount[j], matrix[0][j])
                temp = matrix[0][j] - matrix[i][j]
                sum = sum + temp ** 2
            result = math.sqrt(float(sum))
            if (i == 1):
                min1 = [i, result]
                min2 = min1
            elif (i > 1):
                if (min1[1] > result):
                    min1 = [i, result]
                    min2 = min1
                elif (min2[1] > result):
                    min2 = [i, result]

        max = 0
        for i in range(len(forCount)):
            avg = (matrix[min1[0]][i]+matrix[min2[0]][i])/2
            if (max < avg):
                max = i

        informs = collection.find({'genre': {'$all': [forCount[max]]}}, {'_id': 0}).limit(6)

    for inform in informs:
        games.append(inform)
    return render(request, 'content/index.html', {'games':games})

def like(request):
    like_games = []
    if (user_coll.find().count() != 0):
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
    informs = collection.find({'title': {'$regex': searching, '$options': 'i'}}, {'_id': 0})
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

    informs = collection.find({'title': {'$regex': searching, '$options': 'i'}, 'genre': {'$all': [genre]}}, {'_id': 0})
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
                      'endPageNum': int(endPageNum)
                  })

def game(request):
    global game_name
    global tempgame_genre
    other_page = []
    other_prices = []
    game = []
    game_genre = []
    game_img = ""
    checkUpdate = False
    if (request.method == 'POST'):
        game_name = request.POST.get('gameName')
        game_img = request.POST.get('gameImg')
        tempgame_genre = request.POST.get('gameGenre')
        delete_check = request.POST.get('deleteCheck')
    if (game_img != "" and game_img != None):
        checkUpdate = True
    nameStr = '^' + game_name + '$'

    informs = collection.find({'title': {'$regex': nameStr}}).limit(1)
    siteinform = othersites.find({'_id': {'$regex': game_name, '$options': 'i'}}).limit(1)
    
    for inform in informs:
        game = inform
    try:
        tempgame_genre = re.sub("\'|\[|\]| |temp", '', tempgame_genre)
        tempStr = tempgame_genre.split(',')
        for temp in tempStr:
            game_genre.append(temp)
    except:
        pass

    informsForG = collection.find({'title': {'$regex': nameStr, '$options':'i'}}).limit(1)
    for inform in informsForG:
        other_page.append(inform['prices'][0]['store_name'])
        other_prices.append(inform['prices'][0]['sale_price'])
    siteinformForG = othersites.find({'_id': {'$regex': nameStr, '$options': 'i'}}).limit(1)
    for sitein in siteinformForG:
        for temp in sitein['prices']:
            if (temp['normal_price'] == -1):
                continue
            elif (temp['sale_price'] == -1):
                other_prices.append(temp['normal_price'])
            else:
                other_prices.append(temp['sale_price'])
            other_page.append(temp['store_name'])

    bar(other_page, other_prices, align='center', width=0.3, color='#ff6666')

    buffer = io.BytesIO()
    canvas = pylab.get_current_fig_manager().canvas
    canvas.draw()
    pilImage = PIL.Image.frombytes("RGB", canvas.get_width_height(), canvas.tostring_rgb())
    pilImage.save(buffer, "PNG")
    graphic = buffer.getvalue()
    graphic = base64.b64encode(graphic)
    graphic = graphic.decode('utf-8')

    user = request.user.username
    user_check = user_coll.find({'_id':user, 'games.title': game_name}).count()
    if (checkUpdate and delete_check == '0'):
        if(user_coll.find({'_id':user}).count() == 0 ):
            user_coll.insert_one({'_id': user, 'games': [{'title': game_name, 'img': game_img, 'genre':game_genre}]})
        else:
            user_coll.update_one({'_id': user}, {'$push': {'games': {'title': game_name, 'img': game_img, 'genre':game_genre}}})
        
        user_check = user_coll.find({'_id': user, 'games.title': game_name}).count()
    elif (delete_check == '1'):
        user_coll.update_one({'_id': user}, {'$pull': {'games': {'title': game_name, 'img': game_img, 'genre':game_genre}}})
        user_check = user_coll.find({'_id': user, 'games.title': game_name}).count()

    return render(request, 'content/gamedetail.html', {'game': game, 'usered':user,
                                                       'userCheck': user_check, 'test': game_genre, 'sites': siteinform, 'graphic': graphic})

