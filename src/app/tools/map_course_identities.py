import requests 
import json
import logging
from functools import reduce

'''Tool for fetching identities for course codes and for mapping them to their
respective course code'''

def request_course_identities():
    required_data = {
        "Identity": "6359fd0c-1bbe-496a-8998-4fefc5cd18de",
        "Values": ["null"]
    }
    res = requests.post("https://opentimetable.dcu.ie/broker/api/CategoryTypes/241e4d36-60e0-49f8-b27e-99416745d98d/Categories/Filter?pageNumber=1", json=required_data, headers=HEADERS)
    d = json.loads(res.text)

    results = []
    results.append(d['Results'])

    total_pages = int(d['TotalPages'])
    logging.info('Found %s total pages', total_pages)
    for i in range(2, total_pages + 1):
        logging.debug("retrieving identities for course modules - %s", i)
        res = requests.post("https://opentimetable.dcu.ie/broker/api/CategoryTypes/241e4d36-60e0-49f8-b27e-99416745d98d/Categories/Filter?pageNumber="+str(i), json=required_data, headers=HEADERS)
        if res.status_code != 200:
            logging.critical("Could not load page %s! Not all identities may have been captured", i)
        d = json.loads(res.text)
        results.append(d['Results'])
    logging.info('Pulled results for %s total pages', total_pages)
    return reduce(lambda x,y :x+y, results)


def build_identity_map(identities_lis):
    id_map = {}
    for identity in identities_lis:
        id_map[identity['Name']] = identity['Identity']
    return id_map