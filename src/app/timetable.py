import requests 
import json
import logging
import datetime
from resources.course_identities import identities

global HEADERS
HEADERS = {
    "Authorization": "basic T64Mdy7m[",
    "Content-Type" : "application/json; charset=utf-8",
    "credentials": "include",
    "Referer" : "https://opentimetable.dcu.ie/",
    "Origin" : "https://opentimetable.dcu.ie/"
}


def parse_date(date_str):
    year = int(date_str[:4])
    month = int(date_str[5:7])
    day = int(date_str[8:10])
    return datetime.datetime(year, month, day).date()

def get_start_week(week_lis, week):
    """
        Gets date of the current or next week
    """
    curr = datetime.datetime.now().date()
    if week == 2:
        curr += datetime.timedelta(days=7)
    i = 0 
    while curr not in week_lis and i < 14:
        curr = curr - datetime.timedelta(days=1)
        i += 1
    return curr

def get_weeks(): 
    """
        Gets the available weeks from opentimetables
    """
    res = requests.get("https://opentimetable.dcu.ie/broker/api/viewOptions", headers=HEADERS)
    weeks = json.loads(res.text)['Weeks']
    week_lis = []
    for i in range(len(weeks)):
        s = weeks[i]['FirstDayInWeek']
        week = parse_date(s)
        week_lis.append(week)
    return week_lis

def load_template(name='template.json'):
    """
        Used as a template when sending a request to the website
    """
    with open('resources/template.json', 'r') as f:
        template = json.load(f)
    
    return template

def build_template(template, course_code, weekstart, weekday):
    """
        For sending a POST request to website
    """
    template['CategoryIdentities'][0] = course_code
    template['ViewOptions']['Days'][0]['DayOfWeek'] = weekday
    
    weekstart = str(weekstart).split(" ")
    weekstart = "-".join(weekstart) + "T00:00:00.000Z"
    template['ViewOptions']['Weeks'][0]['FirstDayInWeek'] = weekstart
    return template

def request_events(course_code, data):
    """
        Getting a response from website
    """
    res = requests.post("https://opentimetable.dcu.ie/broker/api/categoryTypes/241e4d36-60e0-49f8-b27e-99416745d98d/categories/events/filter", json=data, headers=HEADERS)
    if res.status_code != 200:
        logging.critical("Unable to get request for course with code: %s", course_code)
        return("Unable to access timetable.")
    else:
        logging.debug("Succesfully got request for course with code: %s", course_code)
        result = json.loads(res.text)
        ongoing = result[0]['CategoryEvents']
        return ongoing

def to_string(classes):
  s = ""
  if classes == []:
      return s
  for cls in classes:
    s += cls['name'] + "<br>"
    s += cls['event_type'] + "<br>"
    if cls['location'] is not None:
        s += cls['location'] + "<br>"
    s += "Start:" + cls['start'] + "<br>"
    s += "Ends:" + cls['end'] + "<br><br>"
  
  return s.strip()


def get_timetable(course, weekday, week):
    week_lis = get_weeks()
    weekstart = get_start_week(week_lis, week)

    try:
        course_code = identities[course]
    except KeyError:
        return("This is not a valid course / the course was not found. :(")
    template = load_template()
    required_data = build_template(template, course_code, weekstart, weekday)
    ongoing = request_events(course_code, required_data)
    classes = []
    for event in ongoing:
      tmp = {}
      module_name = event['ExtraProperties'][0]['Value']
      event_type = event['EventType']
      location = event['Location']
      start = event['StartDateTime'].split("T")[1][:5]
      end = event['EndDateTime'].split("T")[1][:5]
      tmp['name'] = module_name
      tmp['event_type'] = event_type
      tmp['location'] = location
      tmp['start'] = start
      tmp['end'] = end
      classes.append(tmp)


    classes.sort(key=lambda x:x['start'])
    all_cls = to_string(classes)
    return all_cls
