################################################################################
##
## BY: MAhmoud Ahmed Elemarati
## PROJECT : Scrapping
## V: 1.0.0
##
################################################################################

import sys
import platform
from PyQt5 import QtCore, QtGui, QtWidgets

import requests
from bs4 import BeautifulSoup

import sqlite3

## ==> SPLASH SCREEN
from UIsplash_screen import Ui_SplashScreen

## ==> MAIN WINDOW
from UImain import Ui_MainWindow

## ==> GLOBALS
counter = 0
rate_str_to_init = {'zero' : 0 , 'One': 1,'Two': 2,'Three':3 ,'Four':4,'Five':5} 
main_url = 'https://books.toscrape.com'
dataBaseCleared = False
#########################################################################################################################################
#########################################################################################################################################
#########################################################################################################################################
#########################################################################################################################################

# My APPLICATION Controller
class MainWindow(QtWidgets.QMainWindow):    

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.controlProgressBar(0)
        self.ui.btn_close.clicked.connect(self.close_clicked)
        self.ui.btn_scrap.clicked.connect(self.scrap_clicked)


    ## ==> Exit Function
    ########################################################################
    def close_clicked(self,event):
        print('-------------- Thank You .. Closing !!! --------------')
        self.close()

    ## ==> Progress FUNCTIONS
    ########################################################################
    def controlProgressBar(self,counter):
        self.ui.progressBar.setValue(counter)

    ## ==> Function
    ########################################################################
    def clearBooks(self,connection=""):
        SQL = """
            DELETE FROM "main"."_0_1_books";
            """
        connection.execute(SQL)
        connection.commit()

    def clearCategories(self,connection=""):
        SQL = """
            DELETE FROM "main"."_0_0_categories";
            """
        connection.execute(SQL)
        connection.commit()

    def clearDB(self,connection=""):
        global dataBaseCleared
        if(dataBaseCleared==False):
            self.clearBooks(connection=connection)
            self.clearCategories(connection=connection)
            dataBaseCleared = True

    def insertCategory(self,category_name="",connection=""):
        SQL = """
            INSERT INTO "main"."_0_0_categories"
            ("cat_name")
            VALUES (?);
            """
        Data = [category_name]
        row = connection.execute(SQL,Data)
        connection.commit()
        return row.lastrowid
    
    def insertBook(self,book_name="",price="",rate="",available_quantity="",cat_id="",connection=""):
        SQL = """
            INSERT INTO "main"."_0_1_books"
            (book_name,price,rate,available_quantity,cat_id)
            VALUES (?,?,?,?,?);
            """
        Data = [book_name,price,rate,available_quantity,cat_id]
        row = connection.execute(SQL,Data)
        connection.commit()
        return row.lastrowid


    def scrap_clicked(self,event):
        print('-------------- Start Scrapping --------------')
        global main_url

        txt_or_DB = str(self.ui.combo_dir.currentText())

        side_categories = self.get_side_categories(url=main_url)
        just_test_no = len(side_categories) ## Test first (n) Categories

        all_cat_no = just_test_no
        current_cat_no = 1

        for categories in side_categories:  
            category_name = categories.get('category_name')
            self.ui.label_loading.setText(f'Scrapping Category || {category_name} || ...')
            percentage = (current_cat_no*100.0)//all_cat_no
            self.controlProgressBar(percentage)
            

            print(f'******************************* {category_name} *******************************')

            if(just_test_no!=0):   

                category_url  = categories.get('link')
                if txt_or_DB=="Text Files":
                    f = open(f'scraped_text/{category_name}.txt', 'w' , encoding='utf8')                
                    self.scrap_books_pages(url=category_url,category_name=category_name,dist=txt_or_DB,f=f)
                    f.close()
                else:
                    conn = sqlite3.connect('scraped_DB/book_scrapping.db')
                    self.clearDB(connection=conn)
                    category_id = self.insertCategory(category_name=category_name,connection=conn)
                    self.scrap_books_pages(url=category_url,category_id=category_id,dist=txt_or_DB,connection=conn)
                    conn.close()

                just_test_no-=1
                    
            else:
                break
                
            current_cat_no+=1

        self.ui.label_loading.setText(f'Scrapping Finished ...')
        self.controlProgressBar(100)
    
    ########################################################################
    ## Function To Get Side-bar Menu
    def get_side_categories(self, url=""):
        global main_url
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        categories_list = soup.find('div', attrs={'class':'side_categories'}).find('ul').find('li').find('ul').find_all('li')
        side_categories=[]
        for link in categories_list:
            https_link = f"{main_url}/{link.find('a').get('href')}"
            category_name = link.find('a').get_text().strip()
            side_categories.append({'link' : https_link , 'category_name' : category_name})
        return side_categories

    ########################################################################
    ########################################################################
    ## Book Details
    def scrap_book_detail(self, url="",category_name="",category_id="",book_name="",price=0,rate=0,dist="",f="",connection=""):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        instock = soup.find('p', attrs={'class':'instock availability'}).get_text().split(' (')
        stock_staus = instock[0].strip()
        available_quantity =  instock[-1].split(')')[0].strip(' available')
        
        line =  f"category_name      : {category_name}\n"
        line += f"book_name          : {book_name}\n"
        line += f"price              : {price}\n"
        line += f"rate               : {rate}\n"
        line += f"stock_staus        : {stock_staus}\n"
        line += f"available_quantity : {available_quantity}\n"
        line += "-----------------------------------------\n"
        line += "-----------------------------------------\n"
        
        print(line)
        if dist=="Text Files":
            f.write(line)
        else:
            self.insertBook(book_name=book_name,price=price,rate=rate,available_quantity=available_quantity,cat_id=category_id,connection=connection)
        

    ########################################################################
    ########################################################################
    ## Scrope Books In Specific Page
    def scrap_books(self ,url="",category_name="",category_id="",dist="",f="",connection=""):
        global main_url
        
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles_books = soup.find_all('article', attrs={'class':'product_pod'})
        
        ## Loop For Each Book
        for book in articles_books:    
            book_detail_url = f"{main_url}/catalogue/{book.find('h3').find('a').get('href').strip('../../../')}"
            book_name = book.find('h3').find('a').get('title')
            price = book.find('p' , attrs={'class':'price_color'}).get_text()[2:]
            rate = rate_str_to_init[book.find('p' , attrs={'class':'star-rating'}).get('class')[-1]]
            
            ## get Book Details Data
            if dist=="Text Files":
                self.scrap_book_detail(url=book_detail_url,category_name=category_name,book_name=book_name,price=price,rate=rate,dist=dist,f=f)
            else:
                self.scrap_book_detail(url=book_detail_url,category_id=category_id,book_name=book_name,price=price,rate=rate,dist=dist,connection=connection)
        return soup

    ########################################################################
    ########################################################################
    ## Scrape Books In Current and next Pages of Categories
    def scrap_books_pages(self, url="",category_name="",category_id="",dist="",f="",connection=""):
        global main_url
        
        print(f"---------------------- pageNo : {1} ---------------------- {url}")
        if dist=="Text Files":
            soup = self.scrap_books(url=url,category_name=category_name,dist=dist,f=f)
        else:
            soup = self.scrap_books(url=url,category_id=category_id,dist=dist,connection=connection)
            
        try:
            #get How Many Pages in the current category
            Last_page = soup.find('li', attrs={'class':'current'}).get_text().strip().strip('Page ').split(' of ')[-1]
            for pageNo in range(2,int(Last_page)+1):
                if(pageNo!=Last_page):            
                    page_subLink = soup.find('li', attrs={'class':'next'}).find('a').get('href')
                    new_page_link = url.replace('index.html',page_subLink,1)
                    print(f"---------------------- pageNo : {pageNo} of {Last_page} ---------------------- {new_page_link}")

                    if dist=="Text Files":
                        self.scrap_books(url=new_page_link,category_name=category_name,dist=dist,f=f)
                    else:
                        soup = self.scrap_books(url=url,category_id=category_id,dist=dist,connection=connection)

        except Exception as e:
            print(e)
            print('---------------------- no-Pages ----------------------')

    
#########################################################################################################################################
#########################################################################################################################################
#########################################################################################################################################
#########################################################################################################################################

# SPLASH SCREEN
class SplashScreen(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_SplashScreen()
        self.ui.setupUi(self)

        ## UI ==> INTERFACE CODES
        ########################################################################

        ## REMOVE TITLE BAR
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)


        ## DROP SHADOW EFFECT
        self.shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QtGui.QColor(0, 0, 0, 60))
        self.ui.dropShadowFrame.setGraphicsEffect(self.shadow)

        ## QTIMER ==> START
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.progress)
        # TIMER IN MILLISECONDS
        self.timer.start(35)

        # CHANGE DESCRIPTION

        # Initial Text
        self.ui.label_description.setText("<strong>WELCOME</strong> TO MY APPLICATION")

        # Change Texts
        QtCore.QTimer.singleShot(1500, lambda: self.ui.label_description.setText("<strong>LOADING</strong> Please Wait"))
        QtCore.QTimer.singleShot(3000, lambda: self.ui.label_description.setText("<strong>LOADING</strong> USER INTERFACE Initialization"))


        ## SHOW ==> MAIN WINDOW
        ########################################################################
        self.show()
        ## ==> END ##

    ## ==> APP FUNCTIONS
    ########################################################################
    def progress(self):

        global counter

        # SET VALUE TO PROGRESS BAR
        self.ui.progressBar.setValue(counter)

        # CLOSE SPLASH SCREE AND OPEN APP
        if counter > 100:
            # STOP TIMER
            self.timer.stop()

            # SHOW MAIN WINDOW
            self.main = MainWindow()
            self.main.show()

            counter = 0
            # CLOSE SPLASH SCREEN
            self.close()

        # INCREASE COUNTER
        counter += 1

#########################################################################################################################################
#########################################################################################################################################
#########################################################################################################################################
#########################################################################################################################################
def run():
    app = QtWidgets.QApplication(sys.argv)
    window = SplashScreen()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run()

