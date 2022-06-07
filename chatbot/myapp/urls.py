from django.urls import path
from myapp import views

app_name = 'myapp'

urlpatterns = [
    path('', views.home, name='home'),
    path('rubybot/', views.rubybot, name='rubybot'),
    path('urambot/', views.urambot, name='urambot'),
    path('storage/', views.storage, name='storage'),
    path('del_view/', views.del_view, name='del_view')
]
