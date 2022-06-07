from django.shortcuts import render
import pymysql
import pymysql.cursors

DB_HOST = "localhost"
DB_USER = "myuser118"
DB_PASSWORD = "1234"
DB_NAME = "mydb118"


def home(req):
    return render(req, 'home.html')

def test(req):
    return render(req, 'test.html')

def rubybot(req):
    return render(req, 'rubybot.html')

def urambot(req):
    return render(req, 'urambot.html')

def storage(req):
    content = {}

    database = None
    try:
        database = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASSWORD,
            db=DB_NAME,
            charset='utf8'
        )

        sql = f'''
                select * from chatbot_view
            '''
        with database.cursor() as cursor:
            cursor.execute(sql)
            chatbot_view = cursor.fetchall()
            content['chatbot_view'] = chatbot_view

        sql = f'''
                select * from chatbot_eor
            '''
        with database.cursor() as cursor:
            cursor.execute(sql)
            chatbot_eor = cursor.fetchall()
            content['chatbot_eor'] = chatbot_eor

        sql = f'''
                select * from chatbot_stock_today
            '''
        with database.cursor() as cursor:
            cursor.execute(sql)
            chatbot_stock_today = cursor.fetchall()
            content['chatbot_stock_today'] = chatbot_stock_today

    except Exception as e:
        print(e)

    finally:
        if database is not None:
            database.close()

    return render(req, 'storage.html', content)

def del_view(req):
    database = None
    try:
        database = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASSWORD,
            db=DB_NAME,
            charset='utf8'
        )

        sql = f'''
                delete from chatbot_view
            '''
        with database.cursor() as cursor:
            cursor.execute(sql)
            print('삭제')
            database.commit()

    except Exception as e:
        print(e)

    finally:
        if database is not None:
            database.close()

    return render(req, 'storage.html')
