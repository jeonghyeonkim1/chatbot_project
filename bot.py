import threading
import json
import re
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

try:
    database = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8'
    )

    sql = '''
        select * from chatbot_stock
    '''

    with database.cursor() as cursor:
        cursor.execute(sql)
        content = cursor.fetchall()
        code_to_event = {a: c for a, b, c in content}

except Exception as e:
    print(e)


finally:
    if database is not None:
        database.close()

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

        if 'Word' in recv_json_data:
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

            database = None
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

        elif query.strip() in crawl.foreign_id + crawl.foreign_name + crawl.korea_id + crawl.korea_name:
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

            ner_predicts = [(x, 'B_STOCK') if x in code_to_event and y != 'B_STOCK' else (x, y) for x, y in [(a, 'O') if a not in code_to_event.values() and b == 'B_STOCK' else (a, b) for a, b in [(i, 'B_COUNT') if re.match(r'^\d+주$', i) != None and j != 'B_COUNT' else (i, j) for i, j in ner.predict(query)]]]
            ner_tags = [j for i, j in ner_predicts if j == 'B_STOCK' or j == 'B_COUNT']


        print("의도 :", intent_name)
        print("개체명 :", ner_predicts)

        if ner_tags.count('B_STOCK') > 1:
            message = json.dumps({"Answer": "종목을 하나만 입력해달라 냥!!!"})

            conn.send(message.encode())
            return
        elif ner_tags.count('B_COUNT') > 1:
            message = json.dumps({"Answer": "갯수를 하나만 입력해달라 냥!!!"})

            conn.send(message.encode())
            return


        try:
            f = FindAnswer(db)
            answer_text = f.search(intent_name, ner_tags)
            answer = f.tag_to_word(ner_predicts, answer_text)

        except:
            answer = "DB에서 정보를 찾을 수 없다 냥!!!!!"

        send_json_data_str = {
            "Query": query,
            "Answer": answer,
            # "Intent": intent_name,
            # "NER": str(ner_predicts),
        }

        database = None
        try:
            database = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                passwd=DB_PASSWORD,
                db=DB_NAME,
                charset='utf8'
            )

            sql = ''

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

                        sql = '''
                            INSERT chatbot_view(code, name, price, hp, lp, yp, mp, total_mp, tc, max_p, min_p, amount, graph) 
                            values(
                            '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'
                            )
                        ''' % (
                                result["코드"],
                                result["종목"],
                                result["가격"],
                                result["고가"],
                                result["저가"],
                                result["전일종가"],
                                result["시가"] if "시가" in result else "",
                                result["시가총액"] if "시가총액" in result else "",
                                result["거래대금"] if "거래대금" in result else "",
                                result["상한가"] if "상한가" in result else "",
                                result["하한가"] if "하한가" in result else "",
                                result["거래량"],
                                result["그래프"]
                            )

            elif intent_name == '환율 계산':
                send_json_data_str["eor"] = crawl.eor()

                sql = '''
                    INSERT chatbot_eor(eor) 
                    values(
                    '%s'
                    )
                ''' % (send_json_data_str["eor"])

            elif intent_name == '오늘의 증시 조회':
                send_json_data_str["stock_today"] = crawl.stock_today()

                sql = '''
                    INSERT chatbot_stock_today(
                        kospi_rate,
                        kospi_change,
                        kospi_per,
                        kospi_graph,
                        kosdaq_rate,
                        kosdaq_change,
                        kosdaq_per,
                        kosdaq_graph,
                        kospi200_rate,
                        kospi200_change,
                        kospi200_per,
                        kospi200_graph
                    ) VALUES (
                        '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'
                    )
                ''' % (
                    send_json_data_str["stock_today"]["KOSPI"]["지수"],
                    send_json_data_str["stock_today"]["KOSPI"]["변화"],
                    send_json_data_str["stock_today"]["KOSPI"]["변화퍼센트"],
                    send_json_data_str["stock_today"]["KOSPI"]["그래프"],
                    send_json_data_str["stock_today"]["KOSDAQ"]["지수"],
                    send_json_data_str["stock_today"]["KOSDAQ"]["변화"],
                    send_json_data_str["stock_today"]["KOSDAQ"]["변화퍼센트"],
                    send_json_data_str["stock_today"]["KOSDAQ"]["그래프"],
                    send_json_data_str["stock_today"]["KOSPI200"]["지수"],
                    send_json_data_str["stock_today"]["KOSPI200"]["변화"],
                    send_json_data_str["stock_today"]["KOSPI200"]["변화퍼센트"],
                    send_json_data_str["stock_today"]["KOSPI200"]["그래프"]
                )
            elif intent_name == '인기 종목':
                send_json_data_str["hot"] = crawl.top_today()
            elif intent_name == '매수' or intent_name == '매도':
                b_stock = [i for i, j in ner_predicts if j == 'B_STOCK'][0]
                b_count = [i for i, j in ner_predicts if j == 'B_COUNT'][0][:-1]

                result = crawl.search_engine(b_stock)

                if intent_name == '매도':
                    sql = f'''
                        select sum(amount) from chatbot_order where code = '{result['코드']}'
                    '''
                    with database.cursor() as cursor:
                        cursor.execute(sql)
                        all_count = cursor.fetchone()[0]

                    if all_count == None or all_count < int(b_count):
                        send_json_data_str = {"Answer": "보유주가 부족해서 매도가 불가능하다 냥!!"}
                        message = json.dumps(send_json_data_str)

                        conn.send(message.encode())
                        return

                sql = '''
                    INSERT chatbot_order(code, name, amount, price) 
                    values(
                    '%s', '%s', '%s', '%s'
                    )
                ''' % (
                    result['코드'],
                    result['종목'],
                    int(b_count) if intent_name == '매수' else -1 * int(b_count),
                    int(re.sub('[^\d]', '', result['가격'])) if intent_name == '매수' else -1 * int(re.sub('[^\d]', '', result['가격']))
                )

            elif intent_name == '취소':
                pass

            
            if sql != '':
                sql = sql.replace("'None'", "null")

                with database.cursor() as cursor:
                    cursor.execute(sql)
                    print('저장')
                    database.commit()

        except Exception as e:
            print(e)

        finally:
            if database is not None:
                database.close()

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

















