from bs4 import BeautifulSoup
from urllib.request import urlopen
from datetime import datetime
import time
import sys

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
    for key in county_dict:
        try:
            ccode = codes[key]
        except KeyError: # if county not in code dict, uppercase first 3 char
            ccode = key.upper()[0:3] 
        # format county item as code followed by percent outage
        item = "{:} ({:2.1f}%)".format(ccode, 100*county_dict[key])
        if county_dict[key] > thresh:
            # above threshold, add ANSI escape codes for red terminal text
            item = "\033[31;1;4m" + item + "\033[0m"
        outline += item + "  "
        county_count += 1
        if county_count > counties_per_line:
            print(outline)
            outline = ""
            county_count = 0

def get_data(url):
    """scrape outatage data from given url, return as list and county dict"""
    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text()

    table = soup.find("table", { "class" : "table-striped" })

    data = []
    #table_body = table.find('tbody')

    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        eldata = [ele for ele in cols if ele]
        if len(eldata) == 3:
            data.append(eldata)

    # extract county data from tables
    data_dict = {}
    for d in data:
        #print("{}, ".format(d[0]),end="")
        try:
            num = float(d[2].replace(",",""))
            denom = float(d[1].replace(",",""))
        except ValueError:
            print("error converting outage values")
        else:
            if denom > 0:
                data_dict[d[0]] = num/denom
            else:
                print("zero customers in county:" + d[0])
    return(data_dict, text)


def print_customers(text):
    for line in text.splitlines():
        if line[0:10] == "Pacific Ga" and len(line) > 40:
            print(line)
        if line[0:10] == "Customers ":
            print(line)
        if line[0:10] == "Utility Ou":
            print(line)
        if line[0:10] == "Last Updat":
            print(line)

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

# 380 is Texas, 760 is PG&E
url = "https://poweroutage.us/area/utility/760"
# print this many counties per line
counties_per_line = 5
# use this threshold for outages
thresh = 0.01   


# extract the data from the urls
county_dict, text = get_data(url)

# print the top decoration text
print_customers(text)

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