from bs4 import BeautifulSoup
from urllib.request import urlopen
import argparse
import socket
from time import sleep

import RPi.GPIO as GPIO

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
        #BUGFIX
    print(outline)

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


def checkForConnection(host, portNo):
    """
    Description:
        Checks to see if there is a connection to the specified website
    Inputs:
        host - The name or IP address of the server to test a connection to
        portNo - The port number to use for the connection
    Return:
        Boolean - True if connection was successful
    """
    success = True

    # Try and connect to the server, timeout after 2 seconds
    try:
        s = socket.create_connection((host, portNo), 2)
        s.close()
    # An exception will be raised if the connection fails
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
    counties_per_line = 5
    # use this threshold for outages
    thresh = 0.10
    raspPi = False

    # Set up path arguement
    parser = argparse.ArgumentParser(description='Arguments for runtime')
    parser.add_argument('--t', help='Threshold to be used', type=float, required=False)
    args = parser.parse_args()

    while not checkForConnection('www.google.com', '80'):
        # Sleep for 5 seconds
        sleep(5)

    if args.t:
        thresh = args.t

    if raspPi:
        RELAY = 18 # BCM 18, GPIO.1 physical pin 12
    else:
        RELAY = 37

    # Relay is connected NORMALLY CLOSED so gpio.cleanup() leaves it SET.
    # set RELAY TRUE to TURN OFF
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RELAY,GPIO.OUT)
    # power on on startup
    GPIO.output(RELAY, GPIO.LOW)

    try:
        while True:
            # extract the data from the urls
            county_dict, text = get_data(url)

            # print the top decoration text
            print_customers(text)

            # print the formatted county data
            print("\n\nCounty Outages:")
            print_formatted(county_dict, thresh, county_codes, counties_per_line)
            print("\n\n")

            if test_threshold(county_dict, thresh):
                print("   **POWER OFF** (ABOVE THRESHOLD) \n\n")
                # set the GPIO to turn the power off here
                GPIO.output(RELAY, GPIO.HIGH)
            else:
                print("   **POWER ON** (BELOW THRESHOLD) \n\n")
                # set the GPIO to turn the power on here
                GPIO.output(RELAY, GPIO.LOW)
            sleep(300.0)
            #print_outline()

    except KeyboardInterrupt:
        print("interrupted")

    try:
        GPIO.cleanup()               # clean up after yourself
    except RuntimeWarning:
        print('Caught warning')

    exit(0)
