"""
Отслеживание отправлений курьерской солужбы UPS
"""

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import pandas as pd
from datetime import datetime as dt
from selenium.webdriver.common.by import By


class Track:
    def __init__(self, row):
        self.track = row['track']
        self.date = row['date']
        self.comment = row['comments']
        self.index = row['index']
        self.n = row['n']
        self.status = self.get_status(self.track)
        self.new_row = self.get_new_row()

    def __str__(self):
        return f'{self.track} status: {self.status.rstrip(",").replace(",", ", ")}'

    @staticmethod
    def check_elem(elem):
        try:
            return driver.find_element(*elem)
        except NoSuchElementException:
            return False

    def get_status(self, track):
        driver.get(f'https://www.ups.com/track?loc=ru_RU&tracknum={track}&requester=WT/trackdetails')
        if driver.title != 'Отслеживание | UPS - Россия':
            exit('no response')
        driver.implicitly_wait(2)

        check_list = ['st_App_PkgStsMonthNum', 'stApp_ShpmtProg_LVP_milestone_name_0']

        check = 0
        for item in check_list:
            if self.check_elem((By.ID, item)):  # Return object or False
                check = item
                break

        match check:
            # if shipment's delivered
            case 'st_App_PkgStsMonthNum':
                result = self.check_elem((By.ID, 'st_App_PkgStsMonthNum')).text
                result = result.replace(',', '.')
                place = result.split(' в ')
                if len(place) >= 3:
                    result = f'{place[0]} в {place[1]}'
                    place = place[-1]
                else:
                    place = '?'
                city = self.check_elem((By.ID, 'stApp_txtAddress')).text
                name = self.check_elem((By.ID, 'stApp_valReceivedBy')).text
                name = name.split('\n')[0]
                status = f'Доставлено. {result},{city},{place},{name}'
            # if shipment's on road
            case 'stApp_ShpmtProg_LVP_milestone_name_0':
                result = driver.find_element(By.CLASS_NAME, 'ng-star-inserted')
                result = result.find_elements(By.TAG_NAME, 'tr')
                for tr in result:
                    if 'ups-progress_current_row' in tr.get_attribute('class').split():
                        result = tr.text.split('\n')[-1]
                        break
                city = self.check_elem((By.ID, 'stApp_txtAddress')).text
                status = f'{result},{city},,'
            case _:
                status = 'error,' * 3

        return status

    def get_new_row(self):
        new_row = f'\n{self.track},{self.status},{self.index},{self.n},{self.date},{self.comment}'
        return new_row


# timeout between requests
def time_out(seconds):
    if type(seconds) == str and ':' in seconds:
        seconds = seconds.split(':')
        minutes, seconds = map(int, seconds)
        seconds = minutes * 60 + seconds
    else:
        seconds = int(seconds)

    for i in reversed(range(1, seconds + 1)):
        print(f'\r{i // 60}:{(i % 60):02}', end='')
        time.sleep(1)


def start():
    with open('UPS_results.csv', 'w') as file:
        file.write('track,status,index,city,place,name,n,date,comment')
        file.close()

    base = pd.read_excel('test_base.xlsx', na_filter=False)
    if 'index' not in base:
        base['index'] = ''
    print(base)

    for line in base.iterrows():
        a = Track(line[1])
        print(a)
        with open('UPS_results.csv', 'a') as file, open('UPS_results_log.csv', 'a') as file_log:
            file.write(a.new_row)
            file.close()
            file_log.write(a.new_row + ',' + str(dt.now()))
            file_log.close()

    driver.quit()


options = webdriver.ChromeOptions()
#options.add_argument('headless')
pd.set_option('display.expand_frame_repr', False)

while True:
    driver = webdriver.Chrome(options=options)
    start()
    driver.quit()
    time_out('10:00')   # str 'minutes:seconds' or int/str seconds

