from bs4 import BeautifulSoup
import requests, os, datetime, pickle
import pandas as pd

class Crawl:
    def __init__(self):
        self.url = 'https://finance.naver.com/'
        
        with open(r'./data/re.bin', 'rb') as f:
            event_to_code = pickle.load(f)
        self.event_to_code = event_to_code
        self.code_to_event = {j:i for i, j in self.event_to_code.items()}
        
        path = r'./data/종목.xlsx'
        data = os.path.join(path)
        df = pd.read_excel(data, index_col=0)

        self.korea = (df[df['type'] == '국내주식']['name'].tolist() + df[df['type'] == '국내주식']['id'].tolist())
        self.foreign = (df[df['type'] == '해외주식']['name'].tolist() + df[df['type'] == '해외주식']['id'].tolist())
        self.foreign_name = df[df['type'] == '해외주식']['name'].tolist()
        self.foreign_id = df[df['type'] == '해외주식']['id'].tolist()
        
    # 서희 할 꺼
    def top_today(self):
        # https://finance.naver.com/
        # id => _topItems1
        # 테이블을 태그까지 통째로 가져와서 return에 넣어주기.
        return  

    def stock_today(self):
        kospi = BeautifulSoup(requests.get(self.url).text,
                              'html.parser').select_one(".kospi_area")
        kosdaq = BeautifulSoup(requests.get(self.url).text,
                               'html.parser').select_one(".kosdaq_area")
        kospi200 = BeautifulSoup(requests.get(self.url).text,
                                 'html.parser').select_one(".kospi200_area")

        dic = {
            'kospi': {
                '종목': kospi.select_one(".blind").text.strip(),
                '지수': kospi.select_one(".num").text.strip(),
                '변화': kospi.select_one(".num2").text.strip(),
                '변화%': kospi.select_one(".num3").text.strip(),
                '그래프': kospi.select_one("img[alt='코스피지수 상세보기']").attrs['src']
            },
            'kosdaq': {
                '종목': kosdaq.select_one(".blind").text.strip(),
                '지수': kosdaq.select_one(".num").text.strip(),
                '변화': kosdaq.select_one(".num2").text.strip(),
                '변화%': kosdaq.select_one(".num3").text.strip(),
                '그래프': kosdaq.select_one("img[alt='코스닥지수 상세보기']").attrs['src']
            },
            'kospi200': {
                '종목': kospi200.select_one(".blind").text.strip(),
                '지수': kospi200.select_one(".num").text.strip(),
                '변화': kospi200.select_one(".num2").text.strip(),
                '변화%': kospi200.select_one(".num3").text.strip(),
                '그래프': kospi200.select_one("img[alt='코스피200지수 상세보기']").attrs['src']
            }
        }

        return dic

    def search_engine(self, query):
        if query in self.korea:      
            query = str(query.encode('euc-kr'))[2:-1].replace('\\x', '%')
            url = f'https://finance.naver.com/search/searchList.naver?query={query}'
            response = requests.get(url)
            dom = BeautifulSoup(response.text, 'html.parser')

            search_list = [(i.text.strip(), i.attrs['href'][-6:])
                           for i in dom.select('td.tit a')]

            if len(search_list) == 0:
                return '검색 결과가 존재하지 않습니다.'
            elif len(search_list) == 1:
                return Crawl().search_korea(self.url + search_list[0][-1])

            return search_list

        elif query in self.foreign:
            alpa = query.replace(" ", "")
            url = f'https://search.naver.com/search.naver?query={alpa}+주가'
            response = requests.get(url)
            dom = BeautifulSoup(response.text, 'html.parser')
                        
            if not dom.find('div', id = '_cs_root'):
                if not query in self.foreign_name or query in self.foreign_id:

                    return '검색 결과가 존재하지 않습니다.'
              
                else:
                    query = Crawl().event_to_code[query]
                    url = f'https://search.naver.com/search.naver?query={query}+주가'

                    return Crawl().search_foriegn(url)
                
            else:
                return Crawl().search_foriegn(url)

        else :
            query = str(query.encode('euc-kr'))[2:-1].replace('\\x', '%')
            url = f'https://finance.naver.com/search/searchList.naver?query={query}'
            response = requests.get(url)
            dom = BeautifulSoup(response.text, 'html.parser')

            search_list = [(i.text.strip(), i.attrs['href'][-6:])
                           for i in dom.select('td.tit a')]

            if len(search_list) == 0:
                return print('검색 결과가 존재하지 않습니다.')
            elif len(search_list) == 1:
                return Crawl().search_korea(self.url + search_list[0][-1])

            return search_list
            
    def search_korea(self, url):
        try:
            res = BeautifulSoup(requests.get(url).text, 'html.parser')
            
            rate_info = res.select('.rate_info td span.blind')

            dic = {
                '종목': res.select_one('div.wrap_company h2 a').text.strip(),
                '가격': res.select_one('p.no_today span.blind').text.strip(),
                '전일': rate_info[0].text.strip(),
                '고가': rate_info[1].text.strip(),
                '상한가': rate_info[2].text.strip(),
                '거래량': rate_info[3].text.strip(),
                '시가': rate_info[4].text.strip(),
                '저가': rate_info[5].text.strip(),
                '하한가': ''.join([i.text.strip() for i in res.select('.rate_info td .sp_txt7 ~ em span')]),
                '거래대금': rate_info[6].text.strip()
            }

            return dic
        except:
            return "옳바르지 않은 종목명이거나 정보가 없습니다."
        
    def search_foriegn(self, url):
        try:                
            response = requests.get(url)
            dom = BeautifulSoup(response.text, 'html.parser')
            res = dom.find('div', id = '_cs_root')
            
            dic = {
                '종목': res.select_one('span.stk_nm').text.strip(),
                '가격': res.select_one('span.spt_con strong').text.strip(),
                '전일종가': res.select_one('li.pcp dd').text.strip(),
                '고가': res.select_one('li.hp dd').text.strip(),
                '거래량': res.select_one('li.vl dd').text.strip(),
                '저가': res.select_one('li.lp dd').text.strip(),
                '거래대금': res.select_one('li.frr dd').text.strip(),
                '시가총액': res.select_one('li.cp strong').text.strip(),
                '그래프': res.select_one('img._stock_chart').attrs['src']
            }

            return dic
        except:
            return "옳바르지 않은 종목명이거나 정보가 없습니다."

    def eor(a):
        url = 'https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        dom = BeautifulSoup(response.text, 'html.parser')
        elements = dom.select(
            '#content > div.section_calculator > table:nth-child(4) > tbody > tr > td:nth-child(1)')
        usd = elements[0].text.strip()
        usd = usd.replace(',', '')
        return float(usd)

    # 환율 계산 함수


    def K_to_U(dollor):
        usd = Crawl().eor()
        krw = usd * dollor
        print(krw)


    def U_to_K(won):
        usd = Crawl().eor()
        dollor = f'{won / usd:.2f}'
        print(dollor)
