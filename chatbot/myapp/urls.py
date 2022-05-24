from django.urls import path
from myapp import views

app_name = 'myapp'

urlpatterns = [
    path('', views.home, name='home'),
    path('test/', views.test, name='test'),
    path('kakao/', views.kakao, name='kakao'),
    path('naver/', views.naver, name='naver'),
    path('login/', views.login, name='login'),
    path('join/', views.join, name='join'),
    path('search/', views.search, name='search'),
    path('notice/', views.notice, name='notice'),
    path('service/', views.service, name='service'),
    path('mypage/', views.mypage, name='mypage'),
]
