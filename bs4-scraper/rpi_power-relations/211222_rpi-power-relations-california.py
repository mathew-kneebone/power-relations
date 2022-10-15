from bs4 import BeautifulSoup
from urllib.request import urlopen
from datetime import datetime
from colorama import init, Fore, Style 
import time
from time import sleep
import sys
import argparse
import socket
import RPi.GPIO as GPIO

fileName = 'my_log.txt'

def test_threshold(county_dict, thresh):
    """ given a dict of county data, return True if any county with 
    outage fraction above thresh, False otherwise"""
    for key in county_dict:
        if county_dict[key] > thresh:
            return True
    return False


def print_and_log(to_log):
    # Print to string
    print(to_log)

    # Format and output to log
    to_log = to_log.replace(Fore.RED, '').replace(Style.RESET_ALL, '')
    with open(fileName, 'a') as f:
        f.write(to_log + '\n')


def print_formatted(county_dict, thresh, codes, counties_per_line):
    """Given county outage data in a dict, format and print it. """
    outline = ""
    county_count = 0

    for key, val in sorted(county_dict.items(), key = lambda x:x[0]):
        try:
            ccode = codes[key]
        except KeyError: # if county not in code dict, uppercase first 3 char
            ccode = key.upper()[0:3]
        # format county item as code followed by percent outage
        item = "{:} ({:2.1f}%)".format(ccode, 100*val)
        if county_dict[key] > thresh:
            # above threshold, add ANSI escape codes for red terminal text
            item = Fore.RED + item + Style.RESET_ALL
        outline += item + "  "
        county_count += 1
        if county_count > counties_per_line:
            print_and_log(outline)
            outline = ""
            county_count = 0
    # BUGFIX: add this line here
    print_and_log(outline)


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
        try:
            num = float(d[2].replace(",",""))
            denom = float(d[1].replace(",",""))
        except ValueError:
            print_and_log("error converting outage values")
        else:
            if denom > 0:
                data_dict[d[0]] = num/denom
            else:
                print_and_log("zero customers in county:" + d[0])
    return(data_dict, text)


def print_customers(text):
    for line in text.splitlines():
        if line[0:10] == "Pacific Ga" and len(line) > 40:
            print_and_log(line)
        if line[0:10] == "Customers ":
            print_and_log(line)
        if line[0:10] == "Utility Ou":
            print_and_log(line)
        if line[0:10] == "Last Updat":
            print_and_log(line)

def checkForConnection(host, portNo):
    success = True
    try:
        s = socket.create_connection((host, portNo), 2)
        s.close()
    except:
        success = False
    return success

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
if __name__ == '__main__':
    # 380 is Texas, 760 is PG&E
    url = "https://poweroutage.us/area/utility/760"
    # print this many counties per line
    counties_per_line = 4
    # use this threshold for outages
    thresh = 0.1

    # Initialize colorama
    init()

    # Set up path arguement
    parser = argparse.ArgumentParser(description='Arguments for runtime')
    parser.add_argument('--p', help='Path to executable directory', type=str, required=False)
    parser.add_argument('--t', help='Threshold to be used', type=float, required=False)
    args = parser.parse_args()

    # While we can't ping google
    while not checkForConnection('www.google.com', '80'):
        # Sleep for 5 seconds
        sleep(5)

    if args.t:
        threshold = args.t

    if args.p:
        path = args.p

    RELAY = 18 # BCM 18, GPIO.1 physical pin 12
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY,GPIO.OUT)
    GPIO.output(RELAY,GPIO.LOW)

    try:
        while True:
            county_dict, text = get_data(url)
            print_customers(text)
            print_and_log("\n\nCounty Outages:")
            print_formatted(county_dict, thresh, county_codes, counties_per_line)
            print_and_log("\n\n")

            if test_threshold(county_dict, thresh):
                print_and_log("**POWER OFF** (ABOVE THRESHOLD)")
                GPIO.output(RELAY, GPIO.HIGH)
            else:
                print_and_log("**POWER ON** (BELOW THRESHOLD)")
                GPIO.output(RELAY, GPIO.LOW)
            sleep(300.0)

    except KeyboardInterrupt:
        print_and_log("interrupted")

    GPIO.cleanup()
    exit(0)
