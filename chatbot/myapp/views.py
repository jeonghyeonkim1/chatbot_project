from django.shortcuts import render


def home(request):
    return render(request, 'home.html')

def test(request):
    return render(request, 'test.html')

def kakao(request):
    return render(request, 'kakao.html')

def naver(request):
    return render(request, 'naver.html')

def login(request):
    return render(request, 'login.html')
    
def join(request):
    return render(request, 'join.html')

def search(request):
    return render(request, 'search.html')

def notice(request):
    return render(request, 'notice.html')

def service(request):
    return render(request, 'service.html')

def mypage(request):
    return render(request, 'mypage.html')