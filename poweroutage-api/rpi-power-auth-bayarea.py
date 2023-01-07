from datetime import datetime
import requests
from colorama import init, Fore, Style
import os
import time
from time import sleep
import sys
import argparse
import socket
import csv
from operator import itemgetter





# set this true to use Rpi hardware
USE_PI = False


if USE_PI:
    import RPi.GPIO as GPIO


# global variables, could do this better!


# filename of list of cities to display
city_list_fname = '20230106_good_city_list.csv'

fileName = 'power-relations-slash_log.txt'

# use this threshold for outages
thresh = 0.1


cities_per_line = 6
chars_per_city = 13

# wait this many seconds between county queries so we don't jam the server
nice_wait = 1.0




# list of IDs for the none counties in the Bay Area
county_ids = [2910, 2912, 2916, 2921, 2939, 2927, 2929, 2931, 2932]

# lists of good cities IDs and abbreviations, indexed in parallel
good_byutilityid = []
good_abbrs = []


total_cust = 0
total_outs = 0


def query_cities(good_cities_ID, nice_wait=1.0):
    ''' returns list of city dicts for each cityId in good_cities list
    nice_wait is the time to sleep between county requests so we don't
    hammer the server'''

    # list of city dicts for each CityId in good_cities:
    cities_list = []
    # get list of cities in each county in Bay Area
    for county in county_ids:

        cities_url="https://poweroutage.us/api/json_v1.6/citybyutility?key={}&Countyid={}".format(authkey,county)
        #print(cities_url)
        city_response = requests.get(cities_url)
        if nice_wait > 0.:
            print("waiting to be nice")
            time.sleep(nice_wait)
        for resp_dict in city_response.json():
            #print(resp_dict)
#             print("{}, {}, {}, {}, {}, {}, {}".format(resp_dict['CustomersTracked'],
#                                                   resp_dict['CityByUtilityId'],
#                                                   resp_dict['CityId'],
#                                                   resp_dict['CountyId'],
#                                                   resp_dict['UtilityId'],
#                                                   resp_dict['CityName'],
#                                                   resp_dict['CityName'][0:4].upper()
# ))


            if int(resp_dict['CityByUtilityId']) in good_cities_ID:
                if int(resp_dict['UtilityId']) != 760:
                    #Wierdo cities and unknown have utilties that are not PGE
                    #print("rejecting")
                    #print(resp_dict)
                    break
                cindex = good_cities_ID.index(resp_dict['CityByUtilityId'])
                abbr = good_abbrs[cindex]
                resp_dict['abbr'] = abbr
                #print("adding {} {}".format(resp_dict['CityName'], abbr))
                cities_list.append(resp_dict)
    #sorted_cities = sorted(cities_list, key=itemgetter('CityName')) 
    sorted_cities = sorted(cities_list, key=itemgetter('abbr')) 
    return sorted_cities

def print_city_data(sorted_cities, thresh):
    global total_cust, total_outs
    city_count = 0
    total_cust  = 0
    total_outs  = 0
    above_thresh = False
    outline = ""
    for city in sorted_cities:

        # format county item as code followed by percent outage
        #item = "{:} ({:4.1f}%)".format(abbr, 100*outratio)
        abbr  = city['abbr']
        outage_i = int(city['CustomersOut'])
        customer_i = int(city['CustomersTracked'])
        if customer_i > 0:
            outratio = float(outage_i)/float(customer_i)
        else:
            outratio = 0.0

        total_cust += customer_i
        total_outs += outage_i
        
        item = "{:4} ({:3.1f}%)".format(abbr, 100*outratio)

        # compute number of spaces so all line up
        pad = chars_per_city - len(item)

        if outratio >= thresh:
            above_thresh = True
            # above threshold, add ANSI escape codes for red terminal text
            item = Fore.RED + item + Style.RESET_ALL

        # pad with spaces so all line up
        outline += item + " "*pad
            
        city_count += 1
        if city_count >= cities_per_line:
            print_and_log(outline)
            outline = ""
            city_count = 0
    print_and_log(outline)
    return(above_thresh)


def print_and_log(to_log):
    # Print to string
    print(to_log)

    # Format and output to log
    to_log = to_log.replace(Fore.RED, '').replace(Style.RESET_ALL, '')
    with open(fileName, 'a') as f:
        f.write(to_log + '\n')


def print_customers():
    """ print utility information retrieved from API"""
    #response = requests.get(utl_url)    
    #rj = response.json()[0]
    
    #print("{}".format(rj['UtilityName']))
    print("Customers: {}".format(total_cust))
    print("Utility Outages: {}".format(total_outs))
    #print("Last Updated Time: {}".format(rj['LastUpdatedDateTime']))


def checkForConnection(host, portNo):
    success = True
    try:
        s = socket.create_connection((host, portNo), 2)
        s.close()
    except:
        success = False
    return success




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


    #read list of good cities, need the CityByUtilityIds and abbreviations
    with open(city_list_fname, newline='') as csvfile:
        citycodes = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in citycodes:
            good_byutilityid.append(int(row[1]))    
            good_abbrs.append(row[6].strip())
            #print(',-'.join(row))

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
        thresh = args.t

    if args.p:
        path = args.p

    if USE_PI:
        RELAY = 18 # BCM 18, GPIO.1 physical pin 12
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RELAY,GPIO.OUT)
        GPIO.output(RELAY,GPIO.LOW)

    try:
        while True:

            sorted_cities = query_cities(good_byutilityid, nice_wait)
            #print_and_log("\n\nCounty Outages:")
            above_threshold = print_city_data(sorted_cities, thresh)

            print_and_log("\n")
            print_customers()
            print_and_log("\n")

            
            if above_threshold:
                print_and_log("**POWER OFF** (ABOVE THRESHOLD)")
                if USE_PI:
                    GPIO.output(RELAY, GPIO.HIGH)
            else:
                print_and_log("**POWER ON** (BELOW THRESHOLD)")
                if USE_PI:
                    GPIO.output(RELAY, GPIO.LOW)
            sleep(300.0 - len(county_ids)*nice_wait)

    except KeyboardInterrupt:
        print_and_log("interrupted")

    if USE_PI:
        GPIO.cleanup()
    exit(0)
