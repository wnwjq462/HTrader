import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *
import webbrowser
import sqlite3
import pandas as pd
from datetime import datetime

form_class = uic.loadUiType("htrader.ui")[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.trade_stocks_done = False
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()

        # Database 연결
        self.con = sqlite3.connect("HBase.db")
        self.cursor = self.con.cursor()

        #보유종목현황 / 선정 종목 버튼 리스트
        self.btn_list1 = []
        self.btn1_num = 0
        self.btn_list2 = []
        self.btn2_num = 0

        #현재 시간을 알려주기 위한 Timer
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)

        #실시간 잔고 및 보유종목 현황을 보여주기 위한 Timer
        self.timer2 = QTimer(self)
        self.timer.start(5000)
        self.timer.timeout.connect(self.timeout2)

        #종목코드 입력
        self.lineEdit.textChanged.connect(self.code_change)
        #계좌번호 출력
        accounts_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))
        accounts = self.kiwoom.get_login_info("ACCNO")
        accounts_list = accounts.split(';')[0:accounts_num]
        self.comboBox.addItems(accounts_list)
        #주문버튼 / 잔고 조회 버튼
        self.pushButton.clicked.connect(self.send_order)
        self.pushButton_2.clicked.connect(self.check_balance)
        #선정 종목 정보 출력
        self.load_buy_sell_list()


        #self.kiwoom._set_real_reg("6000", "8121773611", "8019", "0")



    def send_order(self):
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소' : 4}
        hoga_lookup = {'지정가' : "00", '시장가' : "03"}

        account = self.comboBox.currentText()
        order_type = self.comboBox_2.currentText()
        code = self.lineEdit.text()
        name = self.kiwoom.get_master_code_name(code)
        hoga = self.comboBox_3.currentText()
        num = self.spinBox.value()
        price = self.spinBox_2.value()

        current_time = QTime.currentTime().toString()
        now = datetime.now()
        current_date = str(now.year)+'-'+str(now.month)+'-'+str(now.day)

        if order_type == '신규매수' :
            sql = "INSERT INTO buy_inform VALUES("
            sql = sql + "'" +current_date + "'"+ "," + "'"+ current_time + "'"+"," + "'"+name + "'"+"," + "'"+code + "'"+"," + "'수동주문'" + ")"
            self.cursor.execute(sql)
            self.con.commit()
        elif order_type == '신규매도' :
            sql = "INSERT INTO sell_inform VALUES("
            #buy_inform 에서 데이터가져오기
            df = pd.read_sql("SELECT * FROM buy_inform",self.con,index_col = None)
            df_num = len(df)

            for i in range(df_num-1,-1,-1) :
                if df.loc[i,"종목명"] == name :
                    buy_date = df.loc[i,"매수날짜"]
                    buy_time = df.loc[i,"매수시각"]
                    buy_reason = df.loc[i,"매수근거"]
                    break

            #보유종목현황에서 데이터가져오기
            item_count = len(self.kiwoom.opw00018_output['multi'])
            for j in range(item_count):
                row = self.kiwoom.opw00018_output['multi'][j]
                if row[0] == name :
                    sql = sql + "'" + buy_date + "','" + buy_time + "','" + current_date+"','" + current_time + "','" + row[0] + "','" + row[1] + "','" + row[2] + "','" + row[3] + "','" + row[4] + "','" + row[5] +"','" + row[6] +"','" + row[7] + "','" + buy_reason + "'," + "'수동주문'" + ")"
                    #delete_sql = "DELETE FROM buy_inform WHERE 종목명 = "
                    #delete_sql = delete_sql + "'" + name + "'"
                    self.cursor.execute(sql)
                    #self.cursor.execute(delete_sql)
                    self.con.commit()
                    break
        self.kiwoom.send_order("send_order_req","0101",account,order_type_lookup[order_type],code, num, price, hoga_lookup[hoga],"")

    def code_change(self):
        code = self.lineEdit.text()
        name = self.kiwoom.get_master_code_name(code)
        self.lineEdit_2.setText(name)

    def timeout(self):
        market_start_time = QTime(9,0,0)
        current_time = QTime.currentTime()

        if current_time > market_start_time and self.trade_stocks_done is False :
            self.trade_stocks()
            self.trade_stocks_done = True

        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.get_connect_state()
        if state == 1:
            state_msg = "서버 연결 중"
        else :
            state_msg = "서버 미 연결 중"

        self.statusbar.showMessage(state_msg + " | " + time_msg)

    def link_btn(self):
        naver_url = "https://finance.naver.com/item/fchart.nhn?code="
        daum_url = "https://finance.daum.net/quotes/"
        sender = self.sender()
        code = sender.text()
        daum_url = daum_url + code + "#chart"
        webbrowser.open_new(daum_url)
        code = re.findall('\d+', code)[0]
        naver_url = naver_url + code
        webbrowser.open_new(naver_url)

    def check_balance(self):
        self.kiwoom.reset_opw00018_output()
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]


        #opw00018
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")

        #opw00001
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req","opw00001",0,"2000")

        #balance
        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.tableWidget.setItem(0,0,item)

        for i in range(1,6):
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i-1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
            self.tableWidget.setItem(0,i,item)

        self.tableWidget.resizeRowsToContents()

        #Item list
        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.tableWidget_2.setRowCount(item_count)
        for j in range(item_count):
            row = self.kiwoom.opw00018_output['multi'][j]
            for i in range(len(row)):
                if i == 1 :
                    self.btn_list1.append(QPushButton(self.tableWidget_2))
                    self.btn_list1[self.btn1_num].setText(row[i])
                    self.btn_list1[self.btn1_num].clicked.connect(self.link_btn)
                    self.tableWidget_2.setCellWidget(j,i,self.btn_list1[self.btn1_num])
                    self.btn1_num += 1
                else :
                    item = QTableWidgetItem(row[i])
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
                    self.tableWidget_2.setItem(j,i,item)

        self.tableWidget_2.resizeRowsToContents()

    def timeout2(self):
        if self.checkBox.isChecked():
            self.check_balance()

    def load_buy_sell_list(self):
        f = open("buy_list.txt",'rt', encoding='UTF8')
        buy_list = f.readlines()
        f.close()

        f = open("sell_list.txt", 'rt', encoding='UTF8')
        sell_list = f.readlines()
        f.close()

        row_count = len(buy_list) + len(sell_list)
        self.tableWidget_3.setRowCount(row_count)

        #buy list
        for j in range(len(buy_list)):
            row_data = buy_list[j]
            split_row_data = row_data.split(';')

            for i in range(len(split_row_data)):
                if i==1 :
                    self.btn_list2.append(QPushButton(self.tableWidget_2))
                    self.btn_list2[self.btn2_num].setText(split_row_data[i].rstrip())
                    self.btn_list2[self.btn2_num].clicked.connect(self.link_btn);
                    self.tableWidget_3.setCellWidget(j, i, self.btn_list2[self.btn2_num])
                    self.btn2_num += 1
                else :
                    item = QTableWidgetItem(split_row_data[i].rstrip())
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
                    self.tableWidget_3.setItem(j,i,item)

        #sell list
        for j in range(len(sell_list)):
            row_data = sell_list[j]
            split_row_data = row_data.split(';')

            for i in range(len(split_row_data)):
                if i==1 :
                    self.btn_list2.append(QPushButton(self.tableWidget_2))
                    self.btn_list2[self.btn2_num].setText(split_row_data[i].rstrip())
                    self.btn_list2[self.btn2_num].clicked.connect(self.link_btn);
                    self.tableWidget_3.setCellWidget(len(buy_list)+j, i, self.btn_list2[self.btn2_num])
                    self.btn2_num += 1
                else :
                    item = QTableWidgetItem(split_row_data[i].rstrip())
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
                    self.tableWidget_3.setItem(len(buy_list) + j, i, item)

        self.tableWidget_3.resizeRowsToContents()

    def trade_stocks(self):
        hoga_lookup = {'지정가' : "00", '시장가': "03"}

        f = open("buy_list.txt",'rt', encoding='UTF8')
        buy_list = f.readlines()
        f.close()

        f = open("sell_list.txt",'rt', encoding='UTF8')
        sell_list = f.readlines()
        f.close()

        #acoount
        account = self.comboBox.currentText()

        #Current Time and Date Check
        current_time = QTime.currentTime().toString()
        now = datetime.now()
        current_date = str(now.year) + '-' + str(now.month) + '-' + str(now.day)

        #buy list
        for row_data in buy_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[3]
            code = split_row_data[1]
            name = split_row_data[2]
            num = split_row_data[4]
            price = split_row_data[5]
            buy_reason = split_row_data[7]

            if split_row_data[6].rstrip() == '매수전':
                sql = "INSERT INTO buy_inform VALUES("
                sql = sql + "'" + current_date + "'" + "," + "'" + current_time + "'" + "," + "'" + name + "'" + "," + "'" + code + "','" + buy_reason+ "')"
                self.cursor.execute(sql)
                self.con.commit()
                self.kiwoom.send_order("send_order_req","0101",account,1,code,num,price,hoga_lookup[hoga],"")

        #sell list
        for row_data in sell_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[3]
            code = split_row_data[1]
            name = split_row_data[2]
            num = split_row_data[4]
            price = split_row_data[5]
            sell_reason = split_row_data[7]

            if split_row_data[6].rstrip() == '매도전':
                sql = "INSERT INTO sell_inform VALUES("
                # buy_inform 에서 데이터가져오기
                df = pd.read_sql("SELECT * FROM buy_inform", self.con, index_col=None)
                df_num = len(df)
                for i in range(df_num - 1, -1, -1):
                    if df.loc[i, "종목명"] == name:
                        buy_date = df.loc[i, "매수날짜"]
                        buy_time = df.loc[i, "매수시각"]
                        buy_reason = df.loc[i, "매수근거"]
                        break

                # 보유종목현황에서 데이터가져오기
                item_count = len(self.kiwoom.opw00018_output['multi'])
                for j in range(item_count):
                    row = self.kiwoom.opw00018_output['multi'][j]
                    if row[0] == name:
                        sql = sql + "'" + buy_date + "','" + buy_time + "','" + current_date + "','" + current_time + "','" + \
                              row[0] + "','" + row[1] + "','" + row[2] + "','" + row[3] + "','" + row[4] + "','" + row[
                                  5] + "','" + row[6] + "','" + row[7] + "','" + buy_reason + "','" + sell_reason + "')"
                        # delete_sql = "DELETE FROM buy_inform WHERE 종목명 = "
                        # delete_sql = delete_sql + "'" + name + "'"
                        self.cursor.execute(sql)
                        # self.cursor.execute(delete_sql)
                        self.con.commit()
                        break


                self.kiwoom.send_order("send_order_req", "0101", account, 2, code, num, price, hoga_lookup[hoga], "")

        #buy / sell list replace
        for i, row_data in enumerate(buy_list):
            buy_list[i] = buy_list[i].replace("매수전","주문완료")

        for i, row_data in enumerate(sell_list):
            sell_list[i] = sell_list[i].replace("매도전","주문완료")

        #file update
        f = open("buy_list.txt",'wt',encoding='UTF8')
        for row_data in buy_list :
            f.write(row_data)
        f.close()

        f = open("sell_list.txt",'wt',encoding='UTF8')
        for row_data in sell_list :
            f.write(row_data)
        f.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
    myWindow.con.close()