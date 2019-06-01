from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib import messages
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
database = client.project
collection = database.steam

game_name = ""
genre = ""

# Create your views here.
class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

def login(request):
    return render(request, 'registration/login.html')

def main(request):
    games = []
    informs = collection.find({}, {'_id':0}).limit(6)
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
            {username : user},
            {$pull: {'like':{title: game_name}}})
    return render(request, 'content/like.html', {'game': game_name})

def list(request):
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
    if (request.method == 'POST'):
        game_name = request.POST.get('gameName')
    return render(request, 'content/test.html', {'game': game_name})

