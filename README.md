# HTrader
Repository for private project that is concerned with stock trade

HSeek 과 연결된 프로젝트이다.
키움증권 API와 연동되어 있다.
'파이썬으로 배우는 알고리즘 트레이딩' 을 참고, 변형, 추가하며 프로젝트 진행하였다.
가장 주요 기능은 매수해야하는 목록과 매도하는 목록을 Text 파일로 입력받아
그 데이터를 기반으로 자동으로 주식 트레이딩을 하는 것이다.
그 목록은 HSeek에서 찾아서 만드는 것을 목표로 프로젝트 진행중이다.

그 외에 HTrader에 부가적인 기능으로는 프로그램안에서 수동 주문을 진행할 수 있다.
또한 현재 가지고 있는 주식 목록들과 각 종목의 수익률, 보유 비중등을 확인할 수 있으며
전체 현금과 주식 보유분을 따져 수익률을 확인할 수 있다.

또한 매수해야하는 목록과 매도해야하는 목록도 같이 볼 수 있으며, 자동거래, 수동거래시에 거래 목록이 데이터베이스에 저장된다.

다음은 데이터베이스와 각 소스코드에 해당하는 Manual 이다.

DataBase 이름 HBase

buy_inform table - 매수한 종목들에 대한 기록을 담고 있는 테이블

column		매수날짜 매수시각	종목명		종목코드	매수근거

sell_inform table - 매도한 종목들에 대한 기록을 담고 있는 테이블

column 매수날짜 매수시각 매도시각 종목명 종목코드 보유량 보유비중 매입가 현재가 평가손익 수익률 매수근거 매도근거

* Kiwoom.py 

Kiwoom 클래스 

_create_kiwoom_instance(self) : 키움 ProgID 연결

_set_signal_slots(self) : OnEvent , OnReceive 이벤트 함수 연결

comm_connect(self): 키움 로그인 연결

_event_conncet(self, err_code) : 로그인 이벤트 발생 처리하는 메서드

get_code_list_by_market(self,market) : 마켓번호로 종목 코드 리스트를 반환

get_master_code_name(self,code) : 코드명으로 종목 이름 반환

get_connect_state(self) : 연결 정보 반환

set_input_value(self,id,value) : 정보 요청 시 input 설정

comm_rq_data(self,rqname,trcode,next,screen_no) : 데이터 요청

_comm_get_data(self,code,real_type,field_name,index,item_name) : 데이터 가져오기

_get_repeat_cnt : 가져올 데이터의 개수 반환

_receive_tr_data(self,screen_no,rqname,trcode,record_name,next,unused1,unused2,unused3,unused4) : receive 이벤트 발생시에 처리하는 메서드

_receive_real_data(self,jcode,rtype,rdata) : 실시간 데이터 Receive 이벤트 처리

_set_real_reg(self,screen,codelist,fidlist,rtype) : 실시간 데이터 정보 등록

_set_real_remove(self,screen,delcode) : 실시간 데이터 정보 삭제

_opt10081(self,rqname,trcode) : 종목의 일봉 정보를 가져옴

date,open,high,low,close,volume 정보를 가져옴

send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no) : 주문을 요청

get_chejan_data(self, fid) : fid 에 따른 체결잔고 데이터 가져온다.

_receive_chejan_data(self,gubun,item_cnt,fid_list): 체결잔고 데이터를 출력한다.

@staticmethod
change_format(data): 입력된 문자열 왼쪽에 존재하는 ‘-‘ 또는 ‘0’ 을 제거하고 천의 자리마다 콤마를 추가한 문자열로 변경한다. / change_foramt2(data) : 수익률에 대한 포맷 변경

_opw00018(self,rqname,trcode): 
single data 로는
총매입금액, 총평가금액, 총평가손익금액, 총수익률(%), 추정예탁자산의 데이터를 가져온다

multi data 로는
보유종목에 대한 종목명, 보유수량, 매입가, 현재가, 평가손익, 수익률(%) 의 데이터를 가져온다.

_opw0001(self,rqname,trcode) : d+2 추정 예수금의 데이터를 가져온다
	모의투자일 때는 총 수익률 의 값을 100으로 나눈후 출력되도록 해야한다

	get_server_gubun() : 실제 서버인지 모의투자 서버인지 구분

reset_opw00018_output() : 데이터를 가져오기위한 딕셔너리를 초기화한다.





* HTrader.py

MyWindow 클래스

send_order(self) : 프로그램에서 텍스트 박스 정보를 이용하여 수동 주문하고, 주문 정보를 데이터 베이스에 저장

code_change(self) : 종목 코드를 종목 명으로 변환하여 보여줌

timeout(self) : Time 이벤트와 연결되어 현재 키움 API 연결상태와 시각을 보여줌

link_btn(self) : 매수,매도 목록, 현재 보유 종목 목록 상의 종목 코드와 연결된 버튼을 누르면 네이버, 다음 증권에 해당 종목 정보를 불러옴

check_balance(self) : 현재 보유허고 있는 주식의 보유량,보유비중,매입가,현재가,평가손익,수익률,매수근거를 불러와 보여주며, d+2 예수금과 총매입가, 총평가액, 총손익, 총손익률과 이에 따른 추정자산까지 확인할 수 있다.

timeout2(self) : Time 이벤트와 연결되어 check_balance를 실시간으로 불러온다.

load_buy_sell_list(self) : 매수해야 하는 목록, 매도해야 하는 목록 텍스트 파일을 불러와 표로 보여준다.

trade_stocks(self): 현재 작성되어 있는 매수해야하는 목록과 매도해야 하는 목록을 바탕으로 자동으로 매수,매도 진행 후 그 결과를 DB에 저장하고 텍스트 파일을 업데이트 한다.






