from django.urls import path
from myapp import views

app_name = 'myapp'

urlpatterns = [
    path('', views.home, name='home'),
    path('test/', views.test, name='test'),
    path('rubybot/', views.rubybot, name='rubybot'),
    path('naver/', views.naver, name='naver'),
    path('storage/', views.storage, name='storage'),
]
