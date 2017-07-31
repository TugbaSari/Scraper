#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import re
import sys
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
    # noinspection PyBroadException
    try:
        response = urllib2.urlopen(urllib2.Request(url, None, headers))
        html = response.read()
        dom = BeautifulSoup(html, "html.parser")
        return dom
    except:
        return None

area_regex = re.compile('(\d{4})\s[a-zA-Z]+\s([a-zA-Z\s]+)')
amount_regex = re.compile(ur'\u20AC\s([0-9,.]+)\s')
nrooms_regex = re.compile('(\d+)\s\w+')
living_aream2_regex = re.compile(ur'(\d+)\sm\u00B2')
plot_sizem2_regex = re.compile(ur'(\d+)\sm\u00B2')
id_regex = re.compile('(?:huis|appartement)-(\d+)')
street_regex = re.compile('(.*?)\s*(\d+|$)')
year_regex = re.compile('(\d{4})')


def get_text(what):
    text = what.find(text=True)
    return text.strip() if text is not None else ''


def get_group_from_regex(regex, what, default_value, group_num=1):
    match = regex.search(what)
    return match.group(group_num) if match is not None else default_value


def get_name(detail_page):
    name_elements = detail_page.findAll('h3')
    return get_text(name_elements[0]) if len(name_elements) == 1 else ''


def get_street(name):
    return get_group_from_regex(street_regex, name, '')


def get_construction_year(detail_page):
    # noinspection PyBroadException
    try:
        year = detail_page.find_all('dt', text='Year of construction')
        year_range = detail_page.find_all('dt', text='Construction period')
        if len(year) == 1:
            year_text = get_text(year[0].findNext('dd'))
            return int(get_group_from_regex(year_regex, year_text, 0))
        elif len(year_range) == 1:
            range_match = re.search(r'(\d+)-(\d+)', get_text(year_range[0].findNext('dd')))
            if range_match is not None:
                start_year = int(range_match.group(1))
                end_year = int(range_match.group(2))
                return int((start_year + end_year) / 2)
    except:
        e = sys.exc_info()[0]
        print 'Error while getting construction year %s' % e
        return 0
    return 0


def get_address(detail_page):
    address_elements = detail_page.findAll('small')
    if len(address_elements) == 1:
        address_text = get_text(address_elements[0])
        return get_group_from_regex(area_regex, address_text, '', group_num=2)
    return ''


def get_postcode(detail_page):
    address_elements = detail_page.findAll('small')
    if len(address_elements) == 1:
        address_text = get_text(address_elements[0])
        return get_group_from_regex(area_regex, address_text, '')
    return ''


def get_price(detail_page):
    price_elements = detail_page.findAll('span', {"class": "search-result-price"})
    if len(price_elements) == 1:
        price_text = get_text(price_elements[0])
        return int(get_group_from_regex(amount_regex, price_text, '-1').replace(',', '').replace('.', ''))
    return 0


def get_rooms(detail_page):
    rooms_elements = detail_page.findAll('ul', {"class": "search-result-kenmerken"})
    if len(rooms_elements) == 1 and len(rooms_elements[0].findAll('li')) == 2:
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


def get_house_kind(detail_page):
    kinds_elements = detail_page.find_all('dt', text='Kind of house')
    if len(kinds_elements) == 1 and kinds_elements[0].findNext('dd') is not None:
        return get_text(kinds_elements[0].findNext('dd'))
    return ''


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


def get_ownership(detail_page):
    ownership_elements = detail_page.findAll('dt', text='Ownership situation')
    if len(ownership_elements) == 1 and ownership_elements[0].findNext('dd') is not None:
        ownership_text = get_text(ownership_elements[0].findNext('dd'))
        if "Full" in ownership_text:
            return "O"
        elif "lease" in ownership_text:
            return "L"
        else:
            return ownership_text
    return ''


def get_lease_end_date(detail_page):
    ownership_elements = detail_page.findAll('dt', text='Ownership situation')
    if len(ownership_elements) == 1 and ownership_elements[0].findNext('dd') is not None:
        ownership_text = get_text(ownership_elements[0].findNext('dd'))
        if "lease" in ownership_text:
            lease_regex = re.compile('(\d{2}-\d{2}-\d{4})')
            return get_group_from_regex(lease_regex, ownership_text, '')
    return ''


db = None


def init_db():
    global db
    if db is None:
        db = pymssql.connect(server='localhost\SQL2014', user='ts', password='test', database='funda')


def save_house(house_to_save):
    init_db()
    cursor = db.cursor()
    query = 'insert into houses (house_id, house_type, name, area, street, postcode, price, rooms, living_area, ' \
            'plot_area, agent, type, construction_year, roof_type, energy_label, ownership, lease_end_date) ' \
            'values (%(id)s, %(kind)s, %(name)s, %(area)s, %(street)s, %(postcode)s, %(price)s, %(rooms)s, ' \
            '%(living_area)s, %(plot_area)s, %(agent)s, %(type)s, %(construction_year)s, %(roof_type)s, ' \
            '%(energy_label)s, %(ownership)s, %(lease_end_date)s)'
    cursor.execute(query, house_to_save)
    db.commit()
    cursor.close()


def house_exists(funda_id):
    init_db()
    cursor = db.cursor()
    query = 'select 1 from houses where house_id = %(id)s'
    cursor.execute(query, {'id': funda_id})
    rows = cursor.fetchall()
    cursor.close()
    return len(rows) == 1


page_number = 1
search_url = 'http://www.funda.nl/en/koop/rotterdam/+15km'

while True:
    search_url_with_page = search_url if page_number == 1 else search_url + '/p' + str(page_number)

    print 'Getting search results, page %s' % page_number
    page = get_url(search_url_with_page)
    all_houses = page.find_all('li', class_='search-result')
    for house in all_houses:
        link = ''
        for l in house.findAll('a'):
            if l.has_attr('data-search-result-item-anchor'):
                link = 'http://www.funda.nl' + l.get('href')
                break

        if link == '':
            print 'Could not detect detail link of property %s' % house
            continue

        if id_regex.search(link) is None:
            print 'Could not parse link %s' % link
            continue

        id_house = id_regex.search(link).group(1)

        if house_exists(id_house):
            continue

        print 'Getting detail page for %s' % link
        detail = get_url(link)
        if detail is None:
            continue

        h = {
             'id': int(id_house),
             'name': get_name(house),
             'area': get_address(house),
             'street': get_street(get_name(house)),
             'postcode': get_postcode(house),
             'price': get_price(house),
             'rooms': get_rooms(house),
             'living_area': get_living_area(house),
             'plot_area': get_plot_size(house),
             'agent': get_agent(house),
             'kind': get_house_kind(detail),
             'type': get_building_type(detail),
             'construction_year': get_construction_year(detail),
             'roof_type': get_type_of_roof(detail),
             'energy_label': get_energy_label(detail),
             'ownership': get_ownership(detail),
             'lease_end_date': get_lease_end_date(detail)
        }

        save_house(h)

    page_number = page_number + 1
    next_button = page.findAll('span', class_='pagination-next-label')
    if len(next_button) == 0:  # page_number > 3:  #
        break
