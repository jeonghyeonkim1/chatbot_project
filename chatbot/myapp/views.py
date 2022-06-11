from django.shortcuts import render
import pymysql
import pymysql.cursors
from functools import reduce
import sys
sys.path.append('../')
from crawl.crawl import Crawl

DB_HOST = "localhost"
DB_USER = "myuser118"
DB_PASSWORD = "1234"
DB_NAME = "mydb118"

crawl = Crawl()


def home(req):
    return render(req, 'home.html')

def rubybot(req):
    return render(req, 'rubybot.html')

def ppukkubot(req):
    return render(req, 'ppukkubot.html')

def pstorage(req):
    return render(req, 'pstorage.html')
    
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

        # 주식 조회 목록
        sql = f'''
                select * from chatbot_view ORDER BY date DESC
            '''
        with database.cursor() as cursor:
            cursor.execute(sql)
            chatbot_view = cursor.fetchall()
            content['chatbot_view'] = chatbot_view

         # 날짜별 환율 목록
        sql = f'''
                select * from chatbot_eor ORDER BY view DESC
            '''
        with database.cursor() as cursor:
            cursor.execute(sql)
            chatbot_eor = cursor.fetchall()
            content['chatbot_eor'] = chatbot_eor

        # 오늘의 증시 목록
        sql = f'''
                select * from chatbot_stock_today ORDER BY view DESC
            '''
        with database.cursor() as cursor:
            cursor.execute(sql)
            chatbot_stock_today = cursor.fetchall()
            content['chatbot_stock_today'] = chatbot_stock_today

        # 거래 목록
        sql = f'''
                select * from chatbot_order ORDER BY date DESC
            '''
        with database.cursor() as cursor:
            cursor.execute(sql)
            chatbot_order = cursor.fetchall()
            content['chatbot_order'] = chatbot_order

        # 보유주 리스트
        sql = f'''
                select code, name, sum(sum), sum(total) from (select code, name, sum(amount) as sum, sum(amount * price) as total from chatbot_order where amount > 0 and cancel = 0 group by name UNION select code, name, sum(amount), -1 * sum(amount * price) from chatbot_order where amount < 0 and cancel = 0 group by name) as a group by name having sum(sum) > 0
            '''
        with database.cursor() as cursor:
            cursor.execute(sql)
            chatbot_own = cursor.fetchall()
            eor = float(crawl.eor())
            List = reduce(lambda a, b: a.append(int(crawl.search_engine(b[0])['가격'].replace(',', '') if crawl.search_engine(b[0])['코드']
                in crawl.korea_id else int(float(crawl.search_engine(b[0])['가격']) * eor)) * int(b[2])) or a, chatbot_own, [])
            content['chatbot_own'] = [(chatbot_own[i][0], chatbot_own[i][1], int(
                chatbot_own[i][2]), int(chatbot_own[i][3]), List[i], f'{(List[i] / int(chatbot_own[i][3]) * 100) - 100:.2f}%') for i in range(len(chatbot_own))]
            content['chatbot_total'] = sum([int(total) for code, name, cnt, total in chatbot_own])
            content['chatbot_current_total'] = sum(List)
            content['chatbot_profit_loss'] = sum(List) - content['chatbot_total']

    except Exception as e:
        print(e)

    finally:
        if database is not None:
            database.close()

    return render(req, 'storage.html', content)

def del_view(req, table):
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
                delete from {table}
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

def send_ppukku(req):
    print(req.GET)
    # content = {}
    
    # if req['intent_id'] == 'a95d62d3-14af-418d-9446-18badadac937':
    #     intent = '메뉴추천'
    # elif req['intent_id'] == '2fb157ca-7d1a-4751-894b-96d2eacf3bd7':
    #     intent = '맛집추천'
    # else:
    #     intent = '인사'


    # database = None
    # try:
    #     database = pymysql.connect(
    #         host=DB_HOST,
    #         user=DB_USER,
    #         passwd=DB_PASSWORD,
    #         db=DB_NAME,
    #         charset='utf8'
    #     )

    #     # 주식 조회 목록
    #     sql = '''
    #             INSERT INTO danbee_query VALUES ('%s', '%s', '%s', '%s')
    #         ''' % (intent, req['input'], req['answer'], req['session_id'])
            
    #     with database.cursor() as cursor:
    #         cursor.execute(sql)
    #         print('저장')
    #         database.commit()

    # except Exception as e:
    #     print(e)

    # finally:
    #     if database is not None:
    #         database.close()

    return render(req, 'ppukkubot.html')