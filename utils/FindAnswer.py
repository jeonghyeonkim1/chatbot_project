class FindAnswer:
    
    # Database 인스턴스 객체로 생성
    def __init__(self, db):
        self.db = db    # 이 객체를 통해 답변을 검색
        
    # ② 답변 검색
    # 의도명(intent_name) 과 개체명 태그 리스트(ner_tags) 를 이용해 질문의 답변을 검색
    def search(self, intent_name, ner_tags, persona_name):
        # 의도명, 개체명으로 답변 검색
        sql = self._make_query(intent_name, ner_tags, persona_name)
        answer = self.db.select_one(sql)
        
        # 검색되는 답변이 없었으면 의도명만 이용하여 답변 검색
        # 챗봇이 찾는 정확한 조건의 답변이 없는 경우 차선책으로 동일한 의도를 가지는 답변을 검색
        # (의도가 동일한 경우 답변도 유사할 확률이 높다!)      
        if answer is None:
            sql = self._make_query(intent_name, None, persona_name)
            answer = self.db.select_one(sql)
            
        return (answer['answer'], answer['answer_image'])
    
    # ③ 검색 쿼리 생성
    # '의도명' 만 검색할지, 여러종류의 개체명 태그와 함께 검색할지 결정하는 '조건'을 만드는 간단한 함수
    # f'select * from chatbot_query where name = (select name from persona where name={name}) and intent = (select intent from chatbot where intent={intent_name} and ner={ner_tags})'
    def _make_query(self, intent_name, ner_tags, persona_name):
        sql = "select * from chatbot_query"
        if intent_name != None and ner_tags == None:
            sql = sql + \
                f" where name = '{persona_name}' and intent = (select intent from chatbot where intent='{intent_name}') "

        elif intent_name != None and ner_tags != None:
            where = f" where name = '{persona_name}' and intent = (select intent from chatbot where intent='{intent_name}' and ner='{' '.join(ner_tags)}') "
            if (len(ner_tags) > 0):
                where += 'and ('
                for ner in ner_tags:
                    where += f" ner like '%{ner}%' or "
                where = where[:-3] + ')'
            sql = sql + where    
            
        # 동일한 답변이 2개 이상인 경우 랜덤으로 선택
        sql = sql + " order by rand() limit 1"
        return sql       
    
    # ④ NER 태그를 실제 입력된 단어로 치환
    
    # 예를 들어 '자장명 주문할께요' 라는 텍스트가 챗본 엔진에 입력되었다고 합시다.
    # 그러면 챗봇 엔진은 '자장명'을 'B_FOOD 객체명'으로 인식합니다.
    # 이때 검색된 답변이 '{B_FOOD} 주문 처리 완료 되었습니다 주문해주셔서 감사합니다' 라고 한다면,
    # 답변 내용속 '{B_FOOD}' 를 '자장면' 으로 치환해 주는 함수입니다.
    # 치환해야 하는 태그가 더 존재한다면 치환 규칙을 추가하면 됩니다.
    
    def tag_to_word(self, ner_predicts, answer):    
        for word, tag in ner_predicts:

            # 변환해야하는 태그가 있는 경우 추가
            if tag == 'B_STOCK' or tag == 'B_COUNT':
                answer = answer.replace(tag, word)

        answer = answer.replace('{', '')
        answer = answer.replace('}', '')
        return answer