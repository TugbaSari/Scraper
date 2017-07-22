#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import re
import time
from bs4 import BeautifulSoup
import pymssql


def get_url(url):
    user_agent = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50' \
                 ' Safari/537.36'
    cookies = 'fonts-loaded=true; D_SID=77.173.107.119:QVHcF5yDc3L9dBYng9oLUH6mQ07NxHQIw1a8t+vQvSM; cookiesAccepted' \
              '_7=7; __gads=ID=aa02815676f3a0bc:T=1487608772:S=ALNI_MZiZg-XmNrsRrz8yaMFURyVuX2D0A; ' \
              'optimizelySegments=%7B%222412520823%22%3A%22gc%22%2C%222418030621%22%3A%22false%22%2C%222440830614%2' \
              '2%3A%22referral%22%2C%222447000113%22%3A%22none%22%7D; optimizelyBuckets=%7B%7D; __utma=72423812.72556' \
              '0531.1487608774.1487608833.1489058073.2; __utmz=72423812.1489058073.2.2.utmcsr=kettner.nl|utmccn=(ref' \
              'erral)|utmcmd=referral|utmcct=/; cookiesAccepted_8=8; websitePreference=websitePreference=desktop; .A' \
              'SPXANONYMOUS=fd6BiLW3PIka0iWlvPTbBV50sfOGp0qvWWtvGxtVUjGtsIVynbk0p0QL77sFa7RMlsRE_x-yLFTaZihpqFTn7es' \
              'fskHayzmjfATsuHL0nbfEmLkuJ0NTMHebhrgU_dHFZ3ndAwa_dy_aQhTG_XywuzRKm-41; rtb-platform=adx; html-class' \
              'es=js supports-placeholder; satisfaction-survey-chance=0.18418120554843; lzo=n=%2fnieuwbouw%2frot' \
              'terdam%2f&k=%2fkoop%2frotterdam%2f%2b5km%2f&h=%2fhuur%2frotterdam%2fnoordereiland%2f0-1250%2f; o' \
              'ptimizelyEndUserId=oeu1487608772610r0.9368169747906676; INLB=01-002; D_IID=3F17F5B2-A7DE-3D1F-90B3-' \
              '4934F8E118FF; D_UID=A6200E0C-261B-337C-8F14-FDDED1BE4598; D_ZID=4374F40C-E30F-3E9B-A19A-9324258A9BD' \
              'F; D_ZUID=7E528153-E88A-3544-9805-AD734A1DA3C9; D_HID=9474DCDE-6436-3607-A62A-F4696047F32A; SNLB2=1' \
              '2-001; _ga=GA1.2.725560531.1487608774; _gid=GA1.2.722868711.1499798508'
    headers = {'User-Agent': user_agent, 'Cookie': cookies}
    response = urllib2.urlopen(urllib2.Request(url, None, headers))
    html = response.read()
    dom = BeautifulSoup(html, "html.parser")
    return dom

area_regex = re.compile('\d{4}\s[a-zA-Z]+\s([a-zA-Z\s]+)')
amount_regex = re.compile(ur'\u20AC\s(\d+.\d+)\s\w.\w.')
nrooms_regex = re.compile('(\d+)\s\w+')
living_aream2_regex = re.compile(ur'(\d+)\sm\u00B2')
plot_sizem2_regex = re.compile(ur'(\d+)\sm\u00B2')
id_regex = re.compile('huis-(\d+)')


def get_text(what):
    return what.find(text=True).strip()


def get_group_from_regex(regex, what, default_value, group_num=1):
    match = regex.search(what)
    return match.group(group_num) if match is not None else default_value


def get_name(detail_page):
    name_elements = detail_page.findAll('h3')
    return get_text(name_elements[0]) if len(name_elements) == 1 else ''


def get_construction_year(detail_page):
    year = detail_page.find_all('dt', text='Year of construction')
    year_range = detail_page.find_all('dt', text='Construction period')
    if len(year) == 1:
        return int(get_text(year[0].findNext('dd')))
    elif len(year_range) == 1:
        range_match = re.search(r'(\d+)-(\d+)', get_text(year_range[0].findNext('dd')))
        if range_match is not None:
            start_year = int(range_match.group(1))
            end_year = int(range_match.group(2))
            return int((start_year + end_year) / 2)
    return 0


def get_address(detail_page):
    address_elements = detail_page.findAll('small')
    if len(address_elements) == 1:
        address_text = get_text(address_elements[0])
        return get_group_from_regex(area_regex, address_text, '')
    return ''


def get_price(detail_page):
    price_elements = detail_page.findAll('span', {"class": "search-result-price"})
    if len(price_elements) == 1:
        price_text = get_text(price_elements[0])
        return int(get_group_from_regex(amount_regex, price_text, '0').replace(',', ''))
    return 0


def get_rooms(detail_page):
    rooms_elements = detail_page.findAll('ul', {"class": "search-result-kenmerken"})
    if len(rooms_elements) == 1 and rooms_elements[0].findAll('li')[1] is not None:
        room_text = get_text(rooms_elements[0].findAll('li')[1])
        return int(get_group_from_regex(nrooms_regex, room_text, '0'))
    return 0


def get_living_area(detail_page):
    living_area_elements = detail_page.findAll('span', {"title": "Living area"})
    if len(living_area_elements) == 1:
        living_area_text = get_text(living_area_elements[0])
        return int(get_group_from_regex(living_aream2_regex, living_area_text, '0'))
    return 0


def get_plot_size(detail_page):
    plot_size_elements = detail_page.findAll('span', {"title": "Plot size"})
    if len(plot_size_elements) == 1:
        plot_size_text = get_text(plot_size_elements[0])
        return int(get_group_from_regex(plot_sizem2_regex, plot_size_text, '0'))
    return 0


def get_house_kinds(detail_page):
    kinds_elements = detail_page.find_all('dt', text='Kind of house')
    if len(kinds_elements) == 1 and kinds_elements[0].findNext('dd') is not None:
        return get_text(kinds_elements[0].findNext('dd')).split(',')
    return []


def get_building_type(detail_page):
    type_elements = detail_page.find_all('dt', text='Building type')
    if len(type_elements) == 1 and type_elements[0].findNext('dd') is not None:
        return get_text(type_elements[0].findNext('dd'))
    else:
        return ''


def get_type_of_roof(detail_page):
    roof_elements = detail_page.find_all('dt', text='Type of roof')
    if len(roof_elements) == 1 and roof_elements[0].findNext('dd') is not None:
        return get_text(roof_elements[0].findNext('dd'))
    else:
        return ''


def get_energy_label(detail_page):
    label_elements = detail_page.findAll('span', {"class": "energielabel"})
    return get_text(label_elements[0]) if len(label_elements) == 1 else ''


def get_agent(detail_page):
    agent_elements = detail_page.findAll('span', {"class": "search-result-makelaar-name"})
    return get_text(agent_elements[0]) if len(agent_elements) == 1 else ''


db = None


def save_house(house_to_save):
    global db
    if db is None:
        db = pymssql.connect(server='localhost\SQL2014', user='ts', password='test', database='funda')
    cursor = db.cursor()
    query = 'insert into houses (house_id, name, area, price, rooms) ' \
            'values (%(id)s, %(name)s, %(area)s, %(price)s, %(rooms)s)'
    cursor.execute(query, house_to_save)
    db.commit()
    cursor.close()


houses = []

page_number = 1
search_url = 'http://www.funda.nl/en/koop/rotterdam/+5km'

while True:
    search_url_with_page = search_url if page_number == 1 else search_url + '/p' + str(page_number)
    page = get_url(search_url_with_page)
    all_houses = page.find_all('li', class_='search-result')
    for house in all_houses:
        time.sleep(1)
        link = 'http://www.funda.nl' + house.findAll('a')[3].get('href')
        detail = get_url(link)
        id_house = id_regex.search(link).group(1)

        h = {
             'id': int(id_house),
             'name': get_name(detail),
             'area': get_address(detail),
             'price': get_price(detail),
             'rooms': get_rooms(detail),
             'living_area': get_living_area(detail),
             'plot_area': get_plot_size(detail),
             'agent': get_agent(detail),
             'kind': get_house_kinds(detail),
             'type': get_building_type(detail),
             'age': get_construction_year(detail),
             'roof_type': get_type_of_roof(detail),
             'energy_label': get_energy_label(detail)
        }

        houses.append(h)
        save_house(h)

    page_number = page_number + 1
    next_button = page.findAll('span', class_='pagination-next-label')
    if page_number > 3:  # len(next_button) == 0:
        break
