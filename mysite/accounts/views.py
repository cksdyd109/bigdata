from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import re
import numpy as np
import math
from django.contrib import messages
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
database = client.project
collection = database.games
othersites = database.othersite
user_coll = database.user

game_name = ""
genre = ""
tempgame_genre = "temp"


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
    if (username == "" or username == None):
        informs = collection.find({}, {'_id': 0}).limit(6)
    else:
        min1 = []
        min2 = []
        pipelines = list()
        pipelines.append({'$unwind': "$games"})
        pipelines.append({'$unwind': "$games.genre"})
        pipelines.append({'$project': {'_id': 1, 'test': "$games.genre"}})
        pipelines.append({'$group': {'_id': "$_id", 'genres': {'$push': "$test"}}})
        pipelines.append({'$match': {'_id':username}})

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
    # database = client.project
    # collection = database.user
    # like_games = []
    # results = collection.find_one({id: request.user.username})['like']
    # for result in results:
    #     like_games.append(result)
    return render(request, 'content/like.html')

def remove(request):
    user = request.user.username
    if (request.method == 'POST'):
        game_name = request.POST.get('gameName')

        collection.update(
            {'username' : user},
            {'$pull': {'like':{'title': game_name}}})
    return render(request, 'content/like.html', {'game': game_name})

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

    user = request.user.username
    user_check = user_coll.find({'_id':user, 'games.title': game_name}).count()
    if (checkUpdate and delete_check == '0'):
        if (user_coll.find({'_id': user}).count() == 0):
            user_coll.insert_one({'_id': user, 'games': [{'title': game_name, 'img': game_img, 'genre': game_genre}]})
        else:
            user_coll.update_one({'_id': user},
                                 {'$push': {'games': {'title': game_name, 'img': game_img, 'genre': game_genre}}})
        user_check = user_coll.find({'_id': user, 'games.title': game_name}).count()
    elif (delete_check == '1'):
        user_coll.update_one({'_id': user}, {'$pull': {'games': {'title': game_name, 'img': game_img, 'genre':game_genre}}})
        user_check = user_coll.find({'_id': user, 'games.title': game_name}).count()

    return render(request, 'content/gamedetail.html', {'game': game, 'usered':user,
                                                       'userCheck': user_check, 'test': game_genre, 'sites': siteinform})

