from django.urls import path
from myapp import views

app_name = 'myapp'

urlpatterns = [
    path('', views.home, name='home'),
    path('rubybot/', views.rubybot, name='rubybot'),
    path('ppukkubot/', views.ppukkubot, name='ppukkubot'),
    path('storage/', views.storage, name='storage'),
    path('ppukku_storage/', views.ppukku_storage, name='ppukku_storage'),
    path('del_view/<table>', views.del_view, name='del_view')
]
