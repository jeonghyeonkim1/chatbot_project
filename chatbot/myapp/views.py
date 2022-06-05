from django.shortcuts import render
import pandas as pd


def home(req):
    return render(req, 'home.html')

def test(req):
    return render(req, 'test.html')

def rubybot(req):
    return render(req, 'rubybot.html')

def urambot(req):
    return render(req, 'urambot.html')

def storage(req):
    return render(req, 'storage.html')


