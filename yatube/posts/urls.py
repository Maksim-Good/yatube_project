# ice_cream/urls.py
from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    # Главная страница
    path('', views.index , name='first'),
    path('groups/', views.groups),
    path('group_list.html', views.group_list),
    path('group/<slug:any_slug>', views.group_posts),

] 