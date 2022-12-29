from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.template import loader

# Главная страница
def index(request):
    # Загружаем шаблон;
    # шаблоны обычно хранят в отдельной директории.
    template = 'posts/index.html'
    text = "Это главная страница проекта Yatube"
    context = {
        'text' : text,
    }
    return render(request, template, context) 


# Страница со списком мороженого
def groups(request, any_slug):
    return HttpResponse(f'Мороженое номер {any_slug}') 

def group_list(request):
    template = 'posts/group_list.html'
    text = "Здесь будет информация о группах проекта Yatube"
    context = {
        'text' : text,
    }
    return render(request, template, context) 

def group_posts(request, any_slug):
    template = f'posts/{any_slug}'
    return render(request, template) 