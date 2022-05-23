import threading
import json

from config.DatabaseConfig import *
from utils.Database import Database
from utils.BotServer import BotServer
from utils.Preprocess import Preprocess
from models.intent.IntentModel import IntentModel
from models.ner.NerModel import NerModel
from utils.FindAnswer import FindAnswer


# 전처리 객체 생성
p = Preprocess(
    word2index_dic='train_tools/dict/chatbot_dict.bin',
    userdic='utils/user_dic.tsv'
)

# 의도 파악 모델
intent = IntentModel(
    model_name='models/intent/intent_model.h5',
    preprocess=p
)

# 개체명 인식 모델
ner = NerModel(
    model_name='models/ner/ner_model.h5',
    preprocess=p
)


# 클라이언트 요청을 수행하는 함수 (쓰레드에 담겨 실행될거임)
def to_client(conn, addr, params):
    db = params['db']
    
    try:
        db.connect()  # DB 연결
        
        # 데이터 수신 (클라이언트로부터 데이터를 받기 위함)
        # conn 은 챗봇 클라이언트 소켓 객체 ( 이 객체를 통해 클라이언트 데이터 주고 받는다 )
        read = conn.recv(2048)  # recv() 는 수신 데이터가 있을 때 까지 블로킹, 최대 2048 바이트만큼 수신
                                # 클라이언트 연결이 끊어지거나 오류발생시 블로킹 해제되고 None 리턴
        print('===========================')
        print('Connection from: %s' % str(addr))
        
        if read is None or not read:
            # 클라이언트 연결이 끊어지거나, 오류가 있는 경우
            print('클라이언트 연결 끊어짐')
            exit(0)  # 종료

        
        # 수신된 데이터(json) 을 파이썬 객체로 변환
        recv_json_data = json.loads(read.decode())
        print("데이터 수신 :", recv_json_data)
        query = recv_json_data['Query']
        
        # 의도 파악
        intent_predict = intent.predict_class(query)
        intent_name = intent.labels[intent_predict]
        
        # 개체명 파악
        ner_predicts = ner.predict(query)
        ner_tags = ner.predict_tags(query)

        # 답변 검색, 분석된 의도와 개체명을 이용해 학습 DB 에서 답변을 검색
        try:
            f = FindAnswer(db)
            answer_text, answer_image = f.search(intent_name, ner_tags)
            answer = f.tag_to_word(ner_predicts, answer_text)

        except:
            answer = "죄송해요 무슨 말인지 모르겠어요. 조금 더 공부 할게요."
            answer_image = None

        # 검색된 답변데이터와 함께 앞서 정의한 응답하는 JSON 으로 생성
        send_json_data_str = {
            "Query": query,
            "Answer": answer,
            "AnswerImageUrl": answer_image,
            "Intent": intent_name,
            "NER": str(ner_predicts)
        }

        # json 텍스트로 변환. 하여 전송
        message = json.dumps(send_json_data_str)
        conn.send(message.encode())  # utf-8 인코딩하여 클라이언트에 전송

    except Exception as ex:
        print(ex)
        
    finally:
        if db is not None:  # DB 연결 끊기
            db.close()
        conn.close()   # 클라이언트와의 연결도 끊음
        
    # 함수가 종료되면 쓰레드고 끝남
        
if __name__ == '__main__':
    # 질문/답변 학습 디비 연결 객체 생성
    db = Database(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db_name=DB_NAME
    )
    print("DB 접속")    
    
    port = 5050
    listen = 100
    
    # 봇 서버 동작
    bot = BotServer(port, listen)
    bot.create_sock()
    print("bot start")

    # 무한루프를 돌면서 챗봇 클라이언트의 요청(연결)을 기다린다(리스닝!)
    while True:
        conn, addr = bot.ready_for_client()  # 서버 연결 요청이 서버에서 수락되면, 
        # ↓ 곧바로 챗봇 클라이언트 서비스 요청 처리하는 쓰레드 생성
    
        params = {
            "db": db
        }
        client = threading.Thread(target=to_client, args=(
            conn, # 클라이언트 연결 소켓
            addr, # 클라이언트 연결 주소 정보
            params  # 쓰레드 내부에서 DB 에 접근할수 있도록 넘겨줌
        ))
        
        client.start()   # 쓰레드 시작. 위 target 함수가 별도의 쓰레드에 실려 실행된다.

















