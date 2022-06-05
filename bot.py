import threading
import json
import re
import pandas as pd
import pymysql
import pymysql.cursors

from config.DatabaseConfig import *
from utils.Database import Database
from utils.BotServer import BotServer
from utils.Preprocess import Preprocess
from models.intent.IntentModel import IntentModel
from models.ner.NerModel import NerModel
from utils.FindAnswer import FindAnswer
from crawl.crawl import Crawl

p1 = Preprocess(
    word2index_dic='train_tools/dict/chatbot_dict_intent.bin',
    userdic='utils/user_dic.tsv'
)

p2 = Preprocess(
    word2index_dic='train_tools/dict/chatbot_dict_ner.bin',
    userdic='utils/user_dic.tsv'
)

intent = IntentModel(
    model_name='models/intent/intent_model.h5',
    preprocess=p1
)

ner = NerModel(
    model_name='models/ner/ner_model.h5',
    preprocess=p2
)

crawl = Crawl()

event_list = pd.read_excel('./data/종목.xlsx')['name'].tolist() + pd.read_excel('./data/종목.xlsx')['id'].tolist()

def to_client(conn, addr, params):
    db = params['db']
    try:
        db.connect()
        
        read = conn.recv(4096)
        print('===========================')
        print('Connection from: %s' % str(addr))
        
        if read is None or not read:
            print('클라이언트 연결 끊어짐')
            exit(0)

        
        recv_json_data = json.loads(read.decode())
        print("데이터 수신 :", recv_json_data)
        query = recv_json_data['Query']

        send_json_data_str = {}

        # 숫자 + 주 를 숫자 + 개로 변환
        # if re.search(r'\d+주', query) != None:
        #     query = query.replace(
        #         re.search(r'\d+주', query).group(), re.search(r'\d+주', query).group()[:-1] + '개')
        if 'Word' in recv_json_data:
            try:
                database = pymysql.connect(
                    host=DB_HOST,
                    user=DB_USER,
                    passwd=DB_PASSWORD,
                    db=DB_NAME,
                    charset='utf8'
                )

                sql = f'''
                        select * from chatbot_word where word = '{recv_json_data['Word']}'
                    '''
                with database.cursor() as cursor:
                    cursor.execute(sql)

                    send_json_data_str['Answer'] = f"{recv_json_data['Word']}에 대한 설명이다냥"
                    send_json_data_str['explain'] = cursor.fetchone()

            except Exception as e:
                print(e)

            finally:
                if database is not None:
                    database.close()

            message = json.dumps(send_json_data_str)
            conn.send(message.encode())
            return


        elif 'Selection' in recv_json_data:
            intent_name = '특정 주가 조회'
            ner_predicts = [(query, 'B_STOCK')]
            ner_tags = ['B_STOCK']

        elif re.search(r'용어|단어', query.strip()) != None:
            send_json_data_str = {
                "Answer": "어떤 용어가 궁금하냥?"
            }

            try:
                database = pymysql.connect(
                    host=DB_HOST,
                    user=DB_USER,
                    passwd=DB_PASSWORD,
                    db=DB_NAME,
                    charset='utf8'
                )

                sql = '''
                    select * from chatbot_word
                '''

                with database.cursor() as cursor:
                    cursor.execute(sql)

                    send_json_data_str['word'] = [i[0] for i in cursor.fetchall()]
            
            except Exception as e:
                print(e)


            finally:
                if database is not None:
                    database.close()

            message = json.dumps(send_json_data_str)
            conn.send(message.encode())
            return

        elif query.strip() in event_list:
            send_json_data_str = {
                "Answer": "해당 종목으로 뭘 하고 싶냥?",
                "event": query.strip(),
                "list": ["정보 조회", "매수", "매도", "취소"]
            }

            message = json.dumps(send_json_data_str)
            conn.send(message.encode())
            return

        else:
            intent_predict = intent.predict_class(query)
            intent_name = intent.labels[intent_predict]

            ner_predicts = ner.predict(query)
            ner_tags = ner.predict_tags(query)


        print("의도 :", intent_name)
        print("개체명 :", ner_predicts)

        try:
            f = FindAnswer(db)
            answer_text = f.search(intent_name, ner_tags)
            answer = f.tag_to_word(ner_predicts, answer_text)

        except:
            answer = "내가 모르는 말이다 냥... 미안하냥!!"


        send_json_data_str = {
            "Query": query,
            "Answer": answer,
            "Intent": intent_name,
            "NER": str(ner_predicts),
        }

        if intent_name == '특정 주가 조회':
            stock = None
            for word, cls in ner_predicts:
                if cls == "B_STOCK" and stock == None:
                    stock = word
            
            if stock == None:
                send_json_data_str["Answer"] = "종목명을 정확하게 알려달라냥"
            else:
                result = crawl.search_engine(stock)

                if type(result) == str:
                    send_json_data_str["Answer"] = result
                elif type(result) == list and len(result) > 1:
                    send_json_data_str["Answer"] = "조회하고 싶은 항목을 선택해달라 냥"
                    send_json_data_str["many"] = result
                else:
                    send_json_data_str["information"] = result
        elif intent_name == '환율 계산':
            send_json_data_str["eor"] = crawl.eor()
        elif intent_name == '오늘의 증시 조회':
            send_json_data_str["stock_today"] = crawl.stock_today()
        elif intent_name == '인기 종목':
            send_json_data_str["hot"] = crawl.top_today()

        message = json.dumps(send_json_data_str)

        conn.send(message.encode())

    except Exception as ex:
        print(ex)
        
    finally:
        if db is not None:
            db.close()
        conn.close()
        
        
if __name__ == '__main__':
    db = Database(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db_name=DB_NAME
    )
    print("DB 접속")
    
    port = 5050
    listen = 100
    
    bot = BotServer(port, listen)
    bot.create_sock()
    print("bot start")

    while True:
        conn, addr = bot.ready_for_client()
    
        params = {
            "db": db
        }
        client = threading.Thread(target=to_client, args=(
            conn,
            addr,
            params
        ))
        
        client.start()

















