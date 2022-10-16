from datetime import datetime
import os
import time
import sys
import requests


def test_threshold(county_dict, thresh):
    """ given a dict of county data, return True if any county with 
    outage fraction above thresh, False otherwise"""
    for key in county_dict:
        if county_dict[key] > thresh:
            return True
    return False

def print_formatted(county_dict, thresh, codes, counties_per_line):
    """Given county outage data in a dict, format and print it. """
    outline = ""
    county_count = 0

    for key, val in  sorted(county_dict.items(), key = lambda x:x[0]):
        try:
            ccode = codes[key]
        except KeyError: # if county not in code dict, uppercase first 3 char
            ccode = key.upper()[0:3]
        # format county item as code followed by percent outage
        item = "{:} ({:2.1f}%)".format(ccode, 100*val)
        if county_dict[key] > thresh:
            # above threshold, add ANSI escape codes for red terminal text
            item = "\033[31;1;4m" + item + "\033[0m"
        outline += item + "  "
        county_count += 1
        if county_count > counties_per_line:
            print(outline)
            outline = ""
            county_count = 0
    # BUGFIX: add this line here
    print(outline)


def get_utility_data(utl_url):
    """ return formatted utility name with number of customers""" 

    
def get_data(api_url):
    """get data from given url, return as dict of outage percentages
    keyed by county name"""

    response = requests.get(api_url)
    # might want to check for response == 200 here but YOLO

    data_dict = {}
    for resp_dict in response.json():
        #print(resp_dict)

        outage_f = float(resp_dict['CustomersOut'])
        customer_f = float(resp_dict['CustomersTracked'])
        if customer_f > 0.0:
            data_dict[resp_dict['CountyName']] = outage_f/customer_f
        else:
            data_dict[resp_dict['CountyName']] = 0.0

    return(data_dict)


def print_customers(utl_url):
    response = requests.get(utl_url)    
    rj = response.json()[0]
    
    print("{}".format(rj['UtilityName']))
    print("Customers: {}".format(rj['CustomersTracked']))
    print("Utility Outages: {}".format(rj['CustomersOut']))
    print("Last Updated Time: {}".format(rj['LastUpdatedDateTime']))

county_codes = {
    "Alameda": "ALA",
    "Alpine": "ALP",
    "Amador": "AMA",
    "Butte": "BUT",
    "Calaveras": "CAL",
    "Colusa": "COL",
    "Contra Costa": "CON",
    "Del Norte": "DEL",
    "El Dorado": "DOR",
    "Fresno": "FRE",
    "Glenn": "GLE",
    "Gwinnett": "GWI",
    "Humboldt": "HUM",
    "Kern": "KER",
    "Kings": "KIN",
    "Lake": "LAK",
    "Lassen": "LAS",
    "Los Angeles": "LOS",
    "Madera": "MAD",
    "Marin": "MAR",
    "Mariposa": "MAR",
    "Mendocino": "MEN",
    "Merced": "MER",
    "Monterey": "MON",
    "Napa": "NAP",
    "Nevada": "NEV",
    "Placer": "PLA",
    "Plumas": "PLU",
    "Sacramento": "SAC",
    "San Benito": "SBN",
    "San Francisco": "S-F",
    "San Joaquin": "S-J",
    "San Luis Obispo": "SLO",
    "San Mateo": "S-M",
    "Santa Barbara": "S-B",
    "Santa Clara": "S-C",
    "Santa Cruz": "CRZ",
    "Shasta": "SHA",
    "Sierra": "SIE",
    "Siskiyou": "SIS",
    "Solano": "SOL",
    "Sonoma": "SON",
    "Stanislaus": "STA",
    "Sutter": "SUT",
    "Tehama": "TEH",
    "Trinity": "TRI",
    "Tulare": "TUL",
    "Tuolumne": "TUO",
    "Unknown": "UNK",
    "Ventura": "VEN",
    "Yolo": "YOL",
    "Yuba": "YUB" }


#### Everything happens here


# first change to home directory so auth file is local 
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# store authorization key in local file so we
# don't check it in to github
#authkey_file = '/home/pi/gith/powerscraper/authkey.txt'
authkey_file = 'authkey.txt'
# read in auth key from file 
try:
    with open('authkey.txt') as fp:
        authkey = fp.read()
except FileNotFoundError:
    print('authorization key file not found:\ncreate "{}" with api key'.format(authkey_file))
    exit()
authkey = authkey.strip()

# Create JSON API url from authkey. 
# texas is utility 380, PGE is utility 760
api_url="https://poweroutage.us/api/json_v1.6/countybyutility?key={}&utilityid=760".format(authkey)

# create utility info URL from authkey
utl_url="https://poweroutage.us/api/json_v1.6/utility?key={}&utilityid=760".format(authkey)

# print this many counties per line
counties_per_line = 5
# use this threshold for outages
thresh = 0.1  

# extract the data from the urls
county_dict = get_data(api_url)


# print the top decoration text

print_customers(utl_url)

# print the formatted county data
print("\n\nCounty Outages:")
print_formatted(county_dict, thresh, county_codes, counties_per_line)
print("\n\n")


if test_threshold(county_dict, thresh):
    print("   **POWER OFF** (ABOVE THRESHOLD)")
    # set the GPIO to turn the power off here
else:
    print("   **POWER ON** (BELOW THRESHOLD)")
    # set the GPIO to turn the power on here