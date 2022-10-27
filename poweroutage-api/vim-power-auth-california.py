from datetime import datetime
import requests
from colorama import init, Fore, Style
import os
import time
from time import sleep
import sys
import argparse
import socket

# this true to use Vim hardware
USE_VIM = False


if USE_VIM:
    import RPi.GPIO as GPIO



fileName = 'power-relations_log.txt'

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
        item = "{:} ({:3.1f}%)".format(ccode, 100*val)
        if county_dict[key] > thresh:
            # above threshold, add ANSI escape codes for red terminal text
            item = Fore.RED + item + Style.RESET_ALL
        if val >= 0.1:
            outline += item + " "
        else:
            outline += item + "  "
        county_count += 1
        if county_count > counties_per_line:
            print_and_log(outline)
            outline = ""
            county_count = 0
    # BUGFIX: add this line here
    print_and_log(outline)


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
    """ print utility information retrieved from API"""
    response = requests.get(utl_url)    
    rj = response.json()[0]
    
    print("{}".format(rj['UtilityName']))
    print("Customers: {}".format(rj['CustomersTracked']))
    print("Utility Outages: {}".format(rj['CustomersOut']))
    print("Last Updated Time: {}".format(rj['LastUpdatedDateTime']))


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


    # create API urls
    # store authorization key in local file so we
    # don't check it in to github

    # first change to code directory so auth file is local 
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # (alternatively put full path here...)
    authkey_file = 'authkey.txt'
    # read in auth key from file 
    try:
        with open('authkey.txt') as fp:
            authkey = fp.read()
    except FileNotFoundError:
        print('authorization key file not found:\ncreate "{}" with api key'.format(authkey_file))
        exit()
    # remove newlines and spaces
    authkey = authkey.strip()

    # Create JSON API url from authkey. 
    # texas is utility 380, PGE is utility 760
    # this URL is for customer outages for this utility
    api_url="https://poweroutage.us/api/json_v1.6/countybyutility?key={}&utilityid=760".format(authkey)

    # create utility info URL from authkey
    # this URL is for utility information (name, total cust) for this utility
    utl_url="https://poweroutage.us/api/json_v1.6/utility?key={}&utilityid=760".format(authkey)

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
        print("Using new threshold {}".format(args.t))
        thresh = args.t

    if args.p:
        path = args.p

    print("Using threshold {}".format(thresh))

        
    if USE_VIM:


        # for RasPi:
        #RELAY = 18 # BCM 18, GPIO.1 physical pin 12

        # for VIM
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
            county_dict = get_data(api_url)
            print_customers(utl_url)
            print_and_log("\n\nCounty Outages:")
            print_formatted(county_dict, thresh, county_codes, counties_per_line)
            print_and_log("\n\n")

            if test_threshold(county_dict, thresh):
                print_and_log("**POWER OFF** (ABOVE THRESHOLD)")
                if USE_VIM:
                    GPIO.output(RELAY, GPIO.HIGH)
            else:
                print_and_log("**POWER ON** (BELOW THRESHOLD)")
                if USE_VIM:
                    GPIO.output(RELAY, GPIO.LOW)
            sleep(300.0)

    except KeyboardInterrupt:
        print_and_log("interrupted")

    if USE_VIM:
        try:
            GPIO.cleanup()               # clean up after yourself
        except RuntimeWarning:
            print('Caught warning')
            
    exit(0)
