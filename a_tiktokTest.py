# -*- coding: utf-8 -*-

from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import CommentEvent, ConnectEvent
from PyQt5 import QtCore, QtWidgets
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import  QFileDialog
from PyQt5.QtCore import  QFile,QTextStream
from utils import date_format
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QEventLoop,QTimer
from selenium_tiktok import TikTokBot
class WorkerComment(QObject):
    data_received = pyqtSignal(dict)

    def __init__(self, commentTable, tiktokTable,ui_main_window):
        super().__init__()
        self.commentTable = commentTable
        self.tiktokTable = tiktokTable
        self.ui_main_window = ui_main_window
    def run_comment(self):
    # Wait until commentTable has data
        while self.commentTable.rowCount() == 0:
            loop = QEventLoop()
            QTimer.singleShot(1000, loop.quit)
            loop.exec_() 

        comment_data, tiktok_data = self.get_row_data(self.commentTable, self.tiktokTable,self.comment_complete)

        self.data_received.emit({"comment_data": comment_data, "tiktok_data": tiktok_data})
        username = tiktok_data.get("tiktokID", "")
        password = tiktok_data.get("pass", "")
        time = comment_data.get("time", "")
        print(username)
        tiktok_bot_instance = TikTokBot(username, password)
        
        new_job_value = int(tiktok_data.get("job", 0)) + 1
        self.ui_main_window.update_tiktok_table_job_column(0, new_job_value)

        

        new_status_value = "done"
        self.ui_main_window.update_comment_table_status_column(0, new_status_value)
    def comment_complete(self, message):
        print(message)
        
    def get_row_data(self, comment_table, tiktok_table):
        comment_data = {}
        tiktok_data = {}

        if comment_table.rowCount() > 0:
            row_index = 0  # You can modify this to get a different row if needed
            for col_index in range(comment_table.columnCount()):
                item = comment_table.item(row_index, col_index)
                if item:
                    header_text = comment_table.horizontalHeaderItem(col_index).text()
                    comment_data[header_text] = item.text()

        if tiktok_table.rowCount() > 0:
            row_index = 0  # You can modify this to get a different row if needed
            for col_index in range(tiktok_table.columnCount()):
                item = tiktok_table.item(row_index, col_index)
                if item:
                    header_text = tiktok_table.horizontalHeaderItem(col_index).text()
                    tiktok_data[header_text] = item.text()

        return comment_data, tiktok_data


class WorkerRunLive(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    comment_received = QtCore.pyqtSignal(pd.DataFrame)
    connect_worker = QtCore.pyqtSignal()
    def __init__(self):
        super().__init__()
        self.comment_df = pd.DataFrame(columns=["comment","current_time"])
        self.starttime = None
        self.unique_id = None 

    def set_unique_id(self, unique_id):
        self.unique_id = unique_id

    def set_starttime(self, starttime_str):
        try:
            # Convert the starttime string to datetime
            self.starttime = datetime.strptime(starttime_str, "%H:%M:%S")
        except ValueError:
            print("Invalid starttime format")

    def run_live_client(self):
        if self.starttime is None:
            print("Start time not set. Aborting.")
            return
        client: TikTokLiveClient = TikTokLiveClient(unique_id=self.unique_id)
        # starttime = datetime.strptime("00:00:28", "%H:%M:%S")
        

        @client.on("connect")
        async def on_connect(_: ConnectEvent):
            print("Connected to Room ID:", client.room_id)

        async def on_comment(event: CommentEvent):
            current_time = datetime.now()
            # user = event.user.nickname
            comment = event.comment
            displaytime = str(current_time - self.starttime).split(', ')[1]


            self.comment_df.loc[len(self.comment_df)] = [comment, current_time]

            # print(f"{user} -> {comment}")
            # print(self.comment_df)

            self.emit_comment_received()

        client.add_listener("comment", on_comment)

        client.run()
        self.finished.emit()

    def get_comment_df(self):
        return self.comment_df

    def emit_comment_received(self):
        self.comment_received.emit(self.comment_df)
        self.connect_worker.emit()

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1119, 844)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 1101, 791))
        self.groupBox.setObjectName("groupBox")
        self.tiktokTab = QtWidgets.QTabWidget(self.groupBox)
        self.tiktokTab.setGeometry(QtCore.QRect(10, 30, 1081, 751))
        self.tiktokTab.setObjectName("tiktokTab")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.tiktokTable = QtWidgets.QTableWidget(self.tab)
        self.tiktokTable.setGeometry(QtCore.QRect(10, 50, 1051, 661))
        self.tiktokTable.setObjectName("tiktokTable")
        self.tiktokTable.setColumnCount(4)
        self.tiktokTable.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tiktokTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tiktokTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tiktokTable.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tiktokTable.setHorizontalHeaderItem(3, item)
        self.addAccountButton = QtWidgets.QPushButton(self.tab)
        self.addAccountButton.setGeometry(QtCore.QRect(20, 10, 81, 31))
        self.addAccountButton.setObjectName("addAccountButton")
        self.linkLive = QtWidgets.QLineEdit(self.tab)
        self.linkLive.setEnabled(True)
        self.linkLive.setGeometry(QtCore.QRect(142, 9, 221, 31))
        self.linkLive.setText("")
        self.linkLive.setObjectName("linkLive")
        self.linkReup = QtWidgets.QLineEdit(self.tab)
        self.linkReup.setEnabled(True)
        self.linkReup.setGeometry(QtCore.QRect(410, 10, 221, 31))
        self.linkReup.setText("")
        self.linkReup.setObjectName("linkReup")
        self.runButton = QtWidgets.QPushButton(self.tab)
        self.runButton.setGeometry(QtCore.QRect(670, 10, 91, 31))
        self.runButton.setObjectName("runButton")
        self.tiktokTab.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.commentTable = QtWidgets.QTableWidget(self.tab_2)
        self.commentTable.setGeometry(QtCore.QRect(10, 50, 1051, 661))
        self.commentTable.setObjectName("commentTable")
        self.commentTable.setColumnCount(3)
        self.commentTable.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.commentTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.commentTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.commentTable.setHorizontalHeaderItem(2, item)
        self.timeDelay = QtWidgets.QLineEdit(self.tab_2)
        self.timeDelay.setGeometry(QtCore.QRect(80, 9, 121, 31))
        self.timeDelay.setObjectName("timeDelay")
        self.starttime = QtWidgets.QLineEdit(self.tab_2)
        self.starttime.setGeometry(QtCore.QRect(250, 9, 121, 31))
        self.starttime.setObjectName("starttime")
        self.tiktokTab.addTab(self.tab_2, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1119, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tiktokTab.setCurrentIndex(0)
        #setWidth commentTable
        self.commentTable.setColumnWidth(0, 640)
        self.commentTable.setColumnWidth(1, 200)
        self.commentTable.setColumnWidth(2, 200)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        #setWidth tiktokTable
        self.tiktokTable.setColumnWidth(0,300)
        self.tiktokTable.setColumnWidth(1,200)
        self.tiktokTable.setColumnWidth(2,130)
        self.tiktokTable.setColumnWidth(3,400)
        #Add tiktok account
        self.addAccountButton.clicked.connect(self.add_tiktok_from_file)
        self.tiktok_columns = [ "tiktokID", "pass","job"]
        self.comment_columns = ["comment","time","status"]
        #workerRunLive
        self.thread = QtCore.QThread()
        self.runButton.clicked.connect(self.start_worker_run_live_thread)
        self.worker_run_live = WorkerRunLive()
        
        self.runButton.clicked.connect(self.start_woker_comment_thread)
        
        self.woker_comment = WorkerComment(self.commentTable, self.tiktokTable, self)

        self.loaded_comment_rows = set()

    def update_tiktok_table_job_column(self, row_index, new_job_value):
        item = QtWidgets.QTableWidgetItem()
        item.setText(str(new_job_value))
        self.tiktokTable.setItem(row_index, self.tiktok_columns.index("job"), item)

    def update_comment_table_status_column(self, row_index, new_status_value):
        item = QtWidgets.QTableWidgetItem()
        item.setText(str(new_status_value))
        self.commentTable.setItem(row_index, self.comment_columns.index("status"), item)

        # Disable the row if the status is "done"
        if new_status_value.lower() == "done":
            for col_index in range(self.commentTable.columnCount()):
                item = self.commentTable.item(row_index, col_index)
                if item:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEnabled)



    def start_woker_comment_thread(self):
        if self.woker_comment:
            self.woker_comment.data_received.connect(self.handle_data_received)
            self.woker_comment_thread = QtCore.QThread()
            self.woker_comment.moveToThread(self.woker_comment_thread)
            self.woker_comment_thread.started.connect(self.woker_comment.run_comment)
            self.woker_comment_thread.finished.connect(self.woker_comment_thread.quit)
            self.woker_comment_thread.finished.connect(self.woker_comment.deleteLater)
            self.woker_comment_thread.finished.connect(self.woker_comment_thread.deleteLater)
            self.woker_comment_thread.start()

    def handle_data_received(self, data):
        comment_data = data.get("comment_data", {})
        tiktok_data = data.get("tiktok_data", {})

        print("Comment Data:", comment_data)
        print("Tiktok Data:", tiktok_data)

    def start_worker_run_live_thread(self):
        if self.worker_run_live and self.thread.isRunning():
            print("Thread is already running. Aborting.")
            return
        if not self.worker_run_live:
            self.worker_run_live = WorkerRunLive()

        self.worker_run_live.comment_received.connect(self.load_data_to_comment_table)
        self.worker_run_live.finished.connect(self.load_data_to_comment_table)
        # self.worker_run_live.connect_worker.connect(self.start_worker_comment_thread)
        # self.worker_run_live.finished.connect(self.start_worker_comment_thread)
        
        starttime_str = self.starttime.text()
        self.worker_run_live.set_starttime(starttime_str)

        unique_id = self.linkLive.text()
        self.worker_run_live.set_unique_id(unique_id)

        self.timeDelay.setEnabled(False)
        self.starttime.setEnabled(False)
        self.linkLive.setEnabled(False)

        # if self.thread.isRunning():
        self.thread = QtCore.QThread()
        self.worker_run_live.moveToThread(self.thread)
        self.thread.started.connect(self.worker_run_live.run_live_client)
        # self.thread.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.worker_run_live.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    
    def load_time_comment(self):
        df_data = self.worker_run_live.get_comment_df()
        time_delay_str = self.timeDelay.text()
        
        try:
           
            time_delay_seconds = int(time_delay_str)
        except ValueError:
            print("Invalid time delay format")
            return
        time= df_data['current_time'] + time_delay_seconds
        return time
    
    def cleanup_after_comment_posted(self):
        # This method will be called when the comment posting is complete
        print("Comment posting complete!")

    def load_data_to_comment_table(self):
        df_data = self.worker_run_live.get_comment_df()
        time_delay_str = self.timeDelay.text()

        try:
            time_delay_seconds = int(time_delay_str)
        except ValueError:
            print("Invalid time delay format")
            return

        for row_index, row_data in enumerate(df_data.values):
            # Check if the row has already been loaded
            if row_index in self.loaded_comment_rows:
                continue

            # Add the row index to the set of loaded rows
            self.loaded_comment_rows.add(row_index)

            self.commentTable.insertRow(row_index)
            for col_index, col_data in enumerate(row_data):
                try:
                    if col_index == 0:
                        pass
                    elif col_index == 1:
                        col_data = pd.to_datetime(col_data)
                        col_data = col_data + pd.to_timedelta(time_delay_seconds, unit='s')
                        col_data = col_data.strftime(date_format)
                    elif col_index == 2:
                        col_data = "pending"
                except pd.errors.ParserError as e:
                    print(f"Error parsing datetime at row {row_index}, col {col_index}: {e}")
                    continue

                item = QtWidgets.QTableWidgetItem(str(col_data))
                self.commentTable.setItem(row_index, col_index, item)

            # Set the status column to "pending"
            item_status = QtWidgets.QTableWidgetItem("pending")
            self.commentTable.setItem(row_index, 2, item_status)
            item_status.setTextAlignment(QtCore.Qt.AlignCenter)
        
        # self.commentTable.resizeColumnsToContents()
                
     #addTiktokAcount
    def add_tiktok_from_file(self):
        # Open file Dialog
        file_name, _ = QFileDialog.getOpenFileName(None, "Open File", "", "All Files (*);;Text Files (*.txt)")
        
        # Read file and import to data table
        if file_name:
            self.label.setText(str(file_name))

            file = QFile(file_name)

            if file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(file)
                facebook_accounts_content = stream.readAll()
                # remove first and last space
                facebook_accounts_content = facebook_accounts_content.strip()

                account_lines = facebook_accounts_content.split('\n')

                accounts = self.file_preprocessing(account_lines)

                # Add data to the data table
                self.add_accounts_to_table(accounts)
                
                file.close()
            else:
                print(f"Error opening file: {file.errorString()}")
    def file_preprocessing(self, account_lines: list):
        self.accounts = []
        for index, account_line in enumerate(account_lines):
            account_values = account_line.split('|')
            account_obj = {
                "tiktokID": account_values[0], 
                "pass": account_values[1],
                "job": "0",
                
                }
            self.accounts.append(account_obj)
        return self.accounts
    def add_accounts_to_table(self, accounts):
        try:
            self.tiktokTable.setRowCount(len(accounts))
            __sortingEnabled = self.tiktokTable.isSortingEnabled()

            for row_index, account_data in enumerate(accounts):
                self.add_row(row_index, account_data)

            # Set the "job" column to 0 for all rows
            for row_index in range(len(accounts)):
                item = QtWidgets.QTableWidgetItem()
                item.setText("0")
                self.tiktokTable.setItem(row_index, self.tiktok_columns.index("job"), item)

            self.tiktokTable.setSortingEnabled(__sortingEnabled)
            print('Added accounts successfully!')
        except Exception as error:
            print(error)

    def add_row(self, row_index, data):
        _translate = QtCore.QCoreApplication.translate
        for column_index, key in enumerate(self.tiktok_columns):
            value = data.get(key, "")

            
            item = QtWidgets.QTableWidgetItem()
            item.setText(_translate("MainWindow", str(value)))
            self.tiktokTable.setItem(row_index, column_index, item) 
  

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.groupBox.setTitle(_translate("MainWindow", "TIKTOK"))
        item = self.tiktokTable.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "tiktokID"))
        item = self.tiktokTable.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "pass"))
        item = self.tiktokTable.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "job"))
        item = self.tiktokTable.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "status"))
        self.addAccountButton.setText(_translate("MainWindow", "Add account"))
        self.linkLive.setPlaceholderText(_translate("MainWindow", "Input link tiktok live"))
        self.linkReup.setPlaceholderText(_translate("MainWindow", "Input link tiktok live reup"))
        self.runButton.setText(_translate("MainWindow", "Run"))
        self.tiktokTab.setTabText(self.tiktokTab.indexOf(self.tab), _translate("MainWindow", "Tiktok accounts"))
        item = self.commentTable.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "comment"))
        item = self.commentTable.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "time"))
        item = self.commentTable.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "status"))
        self.timeDelay.setPlaceholderText(_translate("MainWindow", "input time delay"))
        self.starttime .setPlaceholderText(_translate("MainWindow", "input start time"))
        self.tiktokTab.setTabText(self.tiktokTab.indexOf(self.tab_2), _translate("MainWindow", "Comment"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
