from selenium import webdriver
import time
import pandas as pd
import os
from datetime import datetime as dt


def tracking(track):
    driver.get(f'https://www.ups.com/track?loc=ru_RU&tracknum={track}&requester=WT/trackdetails')
    time.sleep(SLEEP)

    # обход 30-секундной задержки на сайте при первом запуске
    try:
        elem = driver.find_element_by_id('stApp_error_alert_list0').text
        if elem == 'Сейчас мы не можем выполнить ваш запрос. Пожалуйста, повторите попытку позднее.':
            time.sleep(30)
            driver.get(f'https://www.ups.com/track?loc=ru_RU&tracknum={track}&requester=WT/trackdetails')
            time.sleep(SLEEP)
    except:
        None

    try:
        elem = driver.find_element_by_tag_name('track-details-estimation')
        status = elem.find_element_by_tag_name('p').text

        try:
            elem = driver.find_element_by_class_name('ups-progress_row.ups-progress_current_row.ups-progress_row_no_animate.ng-star-inserted')
            stat_0 = elem.text.split('\n')[1]
        except:
            stat_0 = 'Доставлено'

        print(stat_0)
        print(status)
        if test == 1:
            print('Code 003')
    except:
        try:
            elem = driver.find_element_by_id('stApp_error_alert_list0').text
            if elem.split('.')[0] == 'UPS не удалось найти детали отправления по этому номеру для отслеживания':
                row = pd.DataFrame({'track': [track], 'status': ['Невозможно отследить отправление'],
                                    'city': ['-'], 'index': ['-'], 'place': ['-'], 'name': ['-']})
                return row
            print(f'{elem} ({track})')
        except:
            elem = driver.find_element_by_id('stApp_statusErrorText').text

        if elem.split('.')[0] == 'Введенный вами номер для отслеживания недействителен':
            row = pd.DataFrame({'track': [track], 'status': ['Трек-номер недействителен'],
                                'city': ['-'], 'index': ['-'], 'place': ['-'], 'name': ['-']})
        else:
            row = pd.DataFrame({'track': [track], 'status': ['Невозможно отследить трек'],
                                'city': ['-'], 'index': ['-'], 'place': ['-'], 'name': ['-']})

        return row

    week_day = status.split(',')[0]
    # if ':' in status:
    #     week_day = status.split(': ')[1].split(',')[0]
    # else:
    #     week_day = status.split(',')[0]

    # Если уже выпущено для доставки
    if status.split()[-1] == 'дня':
        #status = 'Выпущен для доставки сегодня'

        try:
            city = driver.find_element_by_id('stApp_txtAddress').text
        except:
            city = '-'

        row = pd.DataFrame({'track': [track], 'status': [f'{stat_0}: {status}'],
                            'city': [city], 'index': ['-'], 'place': ['-'], 'name': ['-']})
        return row

    # Если экспресс-отправление
    elif week_day in ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']:
        month = ('Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь',
                 'Ноябрь', 'Декабрь')

        status = status.split(', ')[1].split(' в ')
        date_ = status[0].split(' ')
        # if ':' in status:
        #     date_ = status[0].split(': ')[1].split(' ')
        # else:
        #     date_ = status[0].split(' ')

        try:
            city = driver.find_element_by_id('stApp_txtAddress').text

        except:
            city = '-'

        if date_[-2:] == ['до', '12:00']:
            row = pd.DataFrame({'track': [track], 'status': [f'Express: {status[0]}'],
                                'city': [city], 'index': ['-'], 'place': ['-'], 'name': ['-']})
            return row

        month_num = str(month.index(date_[0]) + 1)
        if len(month_num) == 1:
            month_num = '0' + month_num

        date_ = f'{date_[1]}.{month_num}.2021'
        time_ = status[1]
        status_f = f'Доставлено {date_} в {time_}'

        try:
            place = status[2]

        except:
            place = '-'

        # если не удается найти кому вручено, тогда ищет, где оставлено
        try:
            name = driver.find_element_by_id('stApp_valReceivedBy').text
            name = name.split('\n')[0]

        except:
            name = '-'

        row = pd.DataFrame({'track': [track], 'status': [status_f], 'city': [city],
                            'index': ['-'], 'place': [place], 'name': [name]})
        print(row)
        return row
    #
    else:
        print(track)
        try:
            status = driver.find_element_by_class_name('ups-icon_size_xs').text
            row = pd.DataFrame({'track': [track], 'status': [status], 'city': ['WARNING'],
                                'index': ['WARNING'], 'place': ['WARNING'], 'name': ['WARNING']})
        except:
            status = 'В пути'
            try:
                city = driver.find_element_by_id('stApp_txtAddress').text

            except:
                city = '-'

            row = pd.DataFrame({'track': [track], 'status': [status], 'city': [city],
                                'index': ['WARNING'], 'place': ['-'], 'name': ['-']})

        print(row)
        return row


def start():

    #base = pd.read_excel(FROM, na_filter=False)#, dtype={'date': 'date'})#.fillna(0)
    base = pd.read_xml(FROM, na_filter=False)
    base = base.loc[(base['date'].dt.date < dt.now().date()) & (base['track'] != '')]
    #print(base)

    tab = pd.DataFrame({'track': [], 'status': [], 'city': [],
                        'index': [], 'place': [], 'name': []})

    # Создаем новый файл csv
    with open(TO, 'w') as file:
        file.truncate()
        file.write(',track,status,city,index,place,name,n,date,note\n')

    # Поиск треков
    for n, track in enumerate(base['track']):
        print(n, track)
        try:
            row = tracking(track)
        except:
            row = pd.DataFrame({'track': [track], 'status': ['NaN'], 'city': ['NaN'],
                               'index': '[NaN]', 'place': ['NaN'], 'name': ['NaN']})
        tab = pd.concat([tab, row], sort='True')
        row = pd.merge(left=row, right=base.iloc[[n]], left_on='track', right_on='track')


        row.to_csv(TO, mode='a', header=False, encoding='Windows-1251')
        # нужно ли вести лог
        row['now'] = [dt.now()]
        row.to_csv(TO_RESERVE, mode='a', header=False, encoding='Windows-1251')


    base = pd.merge(left=base, right=tab, left_on='track', right_on='track')
    print(base)

def time_out(minutes, seconds=None):
    # если передали лишь одно значение, считать его секундами
    if seconds is None:
        seconds = minutes

        if type(minutes) == str and ':' in minutes:
            seconds = seconds.replace(' ', '').split(':')
            minutes, seconds = map(int, seconds)

        else:
            exit('error item time_out')
    seconds = minutes * 60 + seconds

    for i in reversed(range(1, seconds + 1)):
        print(f'\r{i // 60}:{(i % 60):02}', end='')
        time.sleep(1)

    print()


options = webdriver.ChromeOptions()
#options.add_argument('headless')
#pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)

#FROM = 'E:/ZAPROS/UPS_tracks.xlsx'
FROM = 'Shipment(октябрь2021).xml'
TO = os.path.join(os.getcwd(), 'UPS_results.csv')
TO_RESERVE = os.path.join(os.getcwd(), 'UPS_results_log.csv')
#FROM = 'E:/ZAPROS/UPS_tracks_statistic.xlsx'
#TO = os.path.join(os.getcwd(), 'UPS_results_statistic.csv')
SLEEP = 5


a = 0
while a == 0:
    #driver = webdriver.Chrome(os.path.join(os.getcwd(), 'chromedriver'), options=options)
    driver = webdriver.Chrome()#'chromedriver', options=options)
    start()
    driver.quit()
    time_out('2:3')
    a += 1










