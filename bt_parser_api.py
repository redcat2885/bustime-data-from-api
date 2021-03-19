import requests
import datetime as dt
from geojson import Feature, FeatureCollection, Point, dump
from bs4 import BeautifulSoup

today = dt.datetime.today().strftime('%Y-%m-%d')
HOST = 'https://www.bustime.ru'
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
              'application/signed-exchange;v=b3;q=0.9',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/87.0.4280.141 Safari/537.36'}
features = []


def post_ajax(city: str, uid: str = '', bus_id: str = 0, date: str = today):
    """
    get point data from bustime.ru

    :param city: str  # city of search
    :param uid: str  # vehicle unique id
    :param bus_id: str  # route id
    :param date: str  # date of search
    :return: list  # with dicts of data
    """

    data = {'city_slug': city,
            'uid': uid,
            'bus_id': bus_id,
            'day': date}
    return requests.Session().post(HOST+'/ajax/transport/', data=data)


def get_html(url, params=''):
    """
    gets html from url
    """

    req = requests.get(url, headers=HEADERS, params=params)
    return req


def get_bus_list(html):
    """
    gets list of bus routes from html
    """
    soup = BeautifulSoup(html)
    bus_dict = {}
    for option in soup.find_all('option'):
        bus_dict[option['value']] = option.text
    return bus_dict


def geojsonize(json: dict, date: str):
    """
    makes geojson feature from json
    :param json: dict  # json of one point
    :param date: str  # date of point
    :return: geojson.Feature
    """
    point = Feature(geometry=Point((json["lon"],
                                    json["lat"])),
                    properties={"uid": json['uniqueid'],
                                "timestamp": json['timestamp'],
                                "date": date,
                                "bus_id": json["bus_id"],
                                # "route_id": bus_dict[str(json["bus_id"])],  КИРИЛЛИЦА
                                "heading": json["heading"],
                                "speed": json["speed"],
                                "direction": json["direction"],
                                # "gosnum": json["gosnum"],  КИРИЛЛИЦА
                                "bortnum": json["bortnum"]})
    return point


host_html = get_html(HOST)

soup = BeautifulSoup(host_html.text)
res = soup.find(class_="ui search selection dropdown").find_all(class_="item")

bt_cities = {}

for i in range(len(res)):
    bt_cities[res[i].getText().strip('\n ')] = res[i]['href']

for key, value in bt_cities.items():
    print(key)

city = str(input('Введите название города (название точно как в списке!) '))

print('Сегодня', today)

date_span_valid = False

while not date_span_valid:
    date_span = int(input('Введите период анализа (начиная с сегодняшнего дня, максимум - 7 дней): '))
    if 7 >= date_span > 0:
        print('Период анализа =', date_span, 'дней')
        date_span_valid = True
    else:
        print('Введите подходящий период')

date_list = []  # делаем список нужных дат

for i in range(date_span):
    date_list.append(str(dt.date.today() - i * dt.timedelta(days=1)))
    print(date_list)

CITY_URL = HOST.rstrip('/') + '/' + bt_cities[city] + '/' + 'transport/'+date_list[0]+'/'
city_html = get_html(CITY_URL)
print(CITY_URL)

bus_dict = get_bus_list(city_html.text)
print(bus_dict)

for date in date_list:
    print(date)
    json_list = []
    for key, value in bus_dict.items():
        json_list += post_ajax(bt_cities[city].strip('/'), bus_id=key, date=date).json()
        print(key)
    for point in json_list:
        features.append(geojsonize(point, date))

feature_collection = [FeatureCollection(features)]

with open(bt_cities[city].strip('/') + '_' + date_span + '.geojson',
          'w', encoding='utf-8') as f:
    dump(feature_collection[0], f, ensure_ascii=False)
