import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd
import sqlite3
import re
from datetime import datetime

TR_REQ_TIME_INTERVAL = 0.2


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.OnReceiveChejanData.connect(self._receive_chejan_data)
        self.OnReceiveRealData.connect(self._receive_real_data)

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()

    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)
        elif rqname == "opw00001_req":
            self._opw00001(rqname, trcode)
        elif rqname == "opw00018_req":
            self._opw00018(rqname, trcode)
        elif rqname == "opt10001_req":
            self._opt10001(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _receive_real_data(self, jcode, rtype, rdata):
            self.real_print(jcode,8019)

    def _set_real_reg(self, screen, codelist, fidlist, rtype):
        ret = self.dynamicCall("SetRealReg(QString,QString,QString,QString)", screen,codelist,fidlist,rtype)
        return ret

    def _set_real_remove(self, screen, delcode):
        ret = self.dynamicCall("SetRealRemove(QString, QString",screen, delcode)
        return ret

    def real_print(self,jcode,fid):
        real = self.dynamicCall("GetCommRealData(QString,Int)",jcode,fid)
        print(real)

    '''def _opt10001(self, rqname, trcode):
        now = datetime.now()
        date = str(now.year) + str(now.month) + str(now.day)
        open = self._comm_get_data(trcode,"",rqname,0, "시가")
        high = self._comm_get_data(trcode, "", rqname, 0, "고가")
        low = self._comm_get_data(trcode, "", rqname, 0, "저가")
        close = self._comm_get_data(trcode, "", rqname, 0, "현재가")
        volume = self._comm_get_data(trcode, "", rqname, 0, "거래량")
        price_rate = self._comm_get_data(trcode, "" , rqname, 0, "등락율")
        volume_rate = self._comm_get_data(trcode, "", rqname, 0 , "거래대비")
    
        open = str(abs(int(open)))
        high = str(abs(int(high)))
        low = str(abs(int(low)))
        close = str(abs(int(close)))
        volume = str(abs(int(volume)))
        volume_rate = str(abs(float(volume_rate)))
        sql = "INSERT INTO _039490 VALUES ("
        sql = sql + "'" + date + "','" + open + "','" + high + "','" + low + "','" + close + "','" + volume + "','" + price_rate + "','" + volume_rate + "')"
        con = sqlite3.connect("c:/Users/H/Desktop/stock.db")
        cursor = con.cursor()
        cursor.execute(sql)
        con.commit()
        con.close()
    '''
    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        print(data_cnt)
        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")
            if len(self.ohlcv['date']) != 0 :
                price_rate = self.ohlcv['close'][-1] / float(close)
                price_rate = (price_rate - 1 ) * 100
                price_rate = round(price_rate, 2)
                self.ohlcv['price_rate'].append(price_rate)

                volume_rate = (self.ohlcv['volume'][-1] / float(volume)) * 100
                volume_rate = round(volume_rate,2)
                self.ohlcv['volume_rate'].append(volume_rate)


            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString", [rqname, screen_no, acc_no, order_type,code, quantity, price, hoga, order_no])

    def get_chejan_data(self,fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        print(gubun)
        print(self.get_chejan_data(9203))
        print(self.get_chejan_data(302))
        print(self.get_chejan_data(900))
        print(self.get_chejan_data(901))

    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    @staticmethod
    def change_format(data):
        strip_data = data.lstrip('-0')
        if strip_data == '' or strip_data == '.00' :
            strip_data = '0'

        format_data = format(int(strip_data), ',d')
        if data.startswith('-'):
            format_data = '-' + format_data

        return format_data

    @staticmethod
    def change_format2(data):
        strip_data = data.lstrip('-0')

        if strip_data == '':
            strip_data = '0'

        if strip_data.startswith('.'):
            strip_data = '0' + strip_data

        if data.startswith('-'):
            strip_data = '-' + strip_data

        return strip_data

    def reset_opw00018_output(self):
        self.opw00018_output = {'single' : [], 'multi' : []}

    def get_server_gubun(self):
        ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
        return ret

    def _opw00001(self, rqname, trcode):
        d2_deposit = self._comm_get_data(trcode, "",rqname,0, "d+2추정예수금")
        self.d2_deposit = Kiwoom.change_format(d2_deposit)

    def _opw00018(self, rqname, trcode):

        #single data
        total_purchase_price = self._comm_get_data(trcode,"",rqname,0,"총매입금액")
        total_eval_price = self._comm_get_data(trcode, "", rqname, 0, "총평가금액")
        total_eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, 0, "총평가손익금액")
        total_earning_rate = self._comm_get_data(trcode, "", rqname, 0, "총수익률(%)")
        estimated_deposit = self._comm_get_data(trcode,"",rqname,0, "추정예탁자산")

        self.opw00018_output['single'].append(Kiwoom.change_format(total_purchase_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_profit_loss_price))
        total_earning_rate = Kiwoom.change_format2(total_earning_rate)
        '''
        if self.get_server_gubun():
            total_earning_rate = float(total_earning_rate) / 100
            total_earning_rate = str(total_earning_rate)
        '''
        self.opw00018_output['single'].append(total_earning_rate)
        self.opw00018_output['single'].append(Kiwoom.change_format(estimated_deposit))
        #multi data
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            name = self._comm_get_data(trcode, "", rqname, i, "종목명")
            code = self._comm_get_data(trcode,"",rqname,i,"종목번호")
            quantity = self._comm_get_data(trcode, "", rqname, i, "보유수량")
            having_rate = self._comm_get_data(trcode, "", rqname, i, "보유비중(%)")
            purchase_price = self._comm_get_data(trcode, "", rqname, i, "매입가")
            current_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, i, "평가손익")
            earning_rate = self._comm_get_data(trcode, "", rqname, i, "수익률(%)")
            buy_reason = "미정"

            quantity = Kiwoom.change_format(quantity)
            purchase_price = Kiwoom.change_format(purchase_price)
            current_price = Kiwoom.change_format(current_price)
            eval_profit_loss_price = Kiwoom.change_format(eval_profit_loss_price)
            earning_rate = Kiwoom.change_format2(earning_rate)
            self.opw00018_output['multi'].append([name,code,quantity,having_rate,purchase_price, current_price, eval_profit_loss_price, earning_rate,buy_reason])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()
    kiwoom.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': [], 'price_rate' : [], 'volume_rate' : []}
    '''
    # opt10081 TR 요청
    kiwoom.set_input_value("종목코드", "039490")
    kiwoom.set_input_value("기준일자", "20190809")
    kiwoom.set_input_value("수정주가구분", 1)
    kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")

    while kiwoom.remained_data == True:
        time.sleep(TR_REQ_TIME_INTERVAL)
        kiwoom.set_input_value("종목코드", "039490")
        kiwoom.set_input_value("기준일자", "20190809")
        kiwoom.set_input_value("수정주가구분", 1)
        kiwoom.comm_rq_data("opt10081_req", "opt10081", 2, "0101")

    kiwoom.ohlcv['price_rate'].append(0)
    kiwoom.ohlcv['volume_rate'].append(0)
    print(kiwoom.ohlcv)
    df = pd.DataFrame(kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume', 'price_rate', 'volume_rate'], index=kiwoom.ohlcv['date'])

    con = sqlite3.connect("c:/Users/H/Desktop/stock.db")
    df.to_sql('_039490', con, if_exists='replace')

    kiwoom.set_input_value("종목코드", "039490")
    kiwoom.comm_rq_data("opt10001_req","opt10001",0,"0101")
    '''


