from django.urls import path
from myapp import views

app_name = 'myapp'

urlpatterns = [
    path('', views.home, name='home'),
    path('test/', views.test, name='test'),
    path('kakao/', views.kakao, name='kakao'),
    path('naver/', views.naver, name='naver'),
    path('notice/', views.notice, name='notice'),
]
