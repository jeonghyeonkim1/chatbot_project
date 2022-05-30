from bs4 import BeautifulSoup
import requests
from datetime import datetime

class Crawl:
    def __init__(self):
        self.url = 'https://finance.naver.com/'

    def stock_today(self):
        kospi = BeautifulSoup(requests.get(self.url).text,
                              'html.parser').select_one(".kospi_area")
        kosdaq = BeautifulSoup(requests.get(
            self.url).text, 'html.parser').select_one(".kosdaq_area")
        kospi200 = BeautifulSoup(requests.get(
            self.url).text, 'html.parser').select_one(".kospi200_area")

        dic = {
            'kospi': {
                '종목': kospi.select_one(".blind").text.strip(),
                '지수': kospi.select_one(".num").text.strip(),
                '변화': kospi.select_one(".num2").text.strip(),
                '변화%': kospi.select_one(".num3").text.strip(),
                '그래프': kospi.select_one("img[alt='코스피지수 상세보기']").attrs['src'],
                '날짜': datetime.now()
            },
            'kosdaq': {
                '종목': kosdaq.select_one(".blind").text.strip(),
                '지수': kosdaq.select_one(".num").text.strip(),
                '변화': kosdaq.select_one(".num2").text.strip(),
                '변화%': kosdaq.select_one(".num3").text.strip(),
                '그래프': kosdaq.select_one("img[alt='코스닥지수 상세보기']").attrs['src'],
                '날짜': datetime.now()
            },
            'kospi200': {
                '종목': kospi200.select_one(".blind").text.strip(),
                '지수': kospi200.select_one(".num").text.strip(),
                '변화': kospi200.select_one(".num2").text.strip(),
                '변화%': kospi200.select_one(".num3").text.strip(),
                '그래프': kospi200.select_one("img[alt='코스피200지수 상세보기']").attrs['src'],
                '날짜': datetime.now()
            }
        }

        return dic

    def search_korea(self, query):
        try:
            url = self.url + f'item/main.naver?code={query}'

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
                '거래대금': rate_info[6].text.strip(),
                '날짜': datetime.now()
            }

            return dic
        except:
            return "옳바르지 않은 종목명 혹은 지수명이거나 정보가 없습니다."

    def search_foriegn(self, query):
        try:
            url = f'https://search.naver.com/search.naver?query={query}+주가'

            res = BeautifulSoup(requests.get(url).text, 'html.parser').select_one(
                'body .api_subject_bx')

            dic = {
                '종목': res.select_one('span.stk_nm').text.strip(),
                '가격': res.select_one('span.spt_con strong').text.strip(),
                '전일종가': res.select_one('li.pcp dd').text.strip(),
                '고가': res.select_one('li.hp dd').text.strip(),
                '거래량': res.select_one('li.vl dd').text.strip(),
                '저가': res.select_one('li.lp dd').text.strip(),
                '거래대금': res.select_one('li.frr dd').text.strip(),
                '시가총액': res.select_one('li.cp strong').text.strip(),
                '그래프': res.select_one('img._stock_chart').attrs['src'],
                '날짜': datetime.now()
            }

            return dic
        except:
            return "옳바르지 않은 종목명이거나 정보가 없습니다."

    def eor():
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
