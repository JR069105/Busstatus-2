import requests
import csv
import tempfile
from datetime import datetime
from pytz import timezone

CSV_URL = 'https://docs.google.com/spreadsheets/d/1p9LjBNkZvti6k_9rV5rc7Bs9oFfLLLCPgvTCIJxvMy4/export?format=csv'

def fetch_data():
    data = requests.get(CSV_URL)
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        f.write(data.content)
    with open(f.name) as temp:
        rows = [row for row in csv.reader(temp)][2:]
        
    return rows
    
def find_index_for_date(data, date):
    # convert to m/d, like 5/4
    formatted_date = f'{date.month}/{date.day}'
    try:
        return data[0].index(formatted_date)
    except:
        # if not present, it may be present in a different format
        alternative_date = f'{date.month}/{date.day}/{date.year}'
        matching = [date for date in data[0] if date.strip().startswith(alternative_date)]
        if len(matching) == 0:
            # if no matches, return None
            return None
        return data[0].index(matching[0])
    
def get_schools(data):
    return [row[0] for row in data[1:]]

def get_data_for_index(data, index):
    responses = {}
    for row in data[1:]:
        # if the school name exists
        if len(row[0]) > 0:
            responses[row[0]] = row[index].split('\n')
            
    return responses
    
# high schools that don't match the pattern of having "High" in the name
HIGH_SCHOOL_OVERRIDE = ["DTSOI", "Archer"]
    
def group_schools(schools):
    schools = [school.strip() for school in schools]
    
    # the key words a school name has in it to designate its type.
    codes = {
        "elementary": "Elem",
        "middle": "MS",
        "junior": "Junior",
        "high": "High"
    }
    
    grouped_schools =  {key: {school.strip(): school.lower().replace(' ', '_') for school in schools if code in school} for key, code in codes.items()}
    
    for school in HIGH_SCHOOL_OVERRIDE:
        grouped_schools["high"][school.strip()] = school.lower().replace(' ', '_')
    
    return grouped_schools

def process_datum(datum):
    processed = []
    nobuses = True
    for value in datum:
        value = value.lower().replace('\\', '/')
        flags = {'morning': False, "afternoon": False}
        if value.endswith('pm'):
            flags["afternoon"] = True
        elif value.endswith('am'):
            flags["morning"] = True
            
        value = value.replace("pm", "").replace("am", "").strip()
        if len(value) == 0:
            continue

        if flags["morning"]:
            nobuses = False
            processed.append(f'Bus {value} canceled in the morning')
        elif flags["afternoon"]:
            processed.append(f'Bus {value} canceled in the afternoon')
            nobuses = False
        else:
            processed.append(f'Bus {value} canceled all day')
            nobuses = False
    if nobuses == True:
        processed.append('All buses running')
    return processed

def process_data(data):
    return {key.lower().replace(' ', '_'): process_datum(value) for key, value in data.items()}
    
def reverse_schools(data):
    megadict = {}
    for section in data.values():
        for key, value in section.items():
            megadict[value] = key
            
    return megadict
    
def scrape_data():
    data = fetch_data()
    
    schools_raw = get_schools(data)
    schools = group_schools(schools_raw)
    index = find_index_for_date(data, datetime.now())
    try:
        results = get_data_for_index(data, index)
    except:
        return {
            "schools": schools,
            "data": {i: ['No Data Found'] for i in reverse_schools(schools)},
            "reverse_schools": reverse_schools(schools),
            "last_updated": datetime.now(tz=timezone('America/Chicago'))
        }
    results = get_data_for_index(data, index)
    results = process_data(results)
    return {
        "schools": schools,
        "data": results,
        "reverse_schools": reverse_schools(schools),
        "last_updated": datetime.now(tz=timezone('America/Chicago'))
    }
