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


# set this true to use Rpi/vim hardware
USE_HW = True
USE_VIM = True # false to use RPI hardware
USE_RPI = False

# don't set both true!
assert(not(USE_VIM and USE_RPI))

# global variables, could do this better!


# filename of list of cities to display
# use command line option "--city-csv <fname.csv>" to override
city_list_fname = '20230106_good_city_list.csv'

# log file name
fileName = 'power-relations-slash_log.txt'

# use this threshold for outages
# use command line option "-t <thresh>" to override
thresh = 0.1

# number of cities to print per line
# use command line option "--n <number>" to override
cities_per_line = 6


#  Field width, in characters, for each city
# use command line option "--pad <nchars>" to override
# note this will not truncate fields so will not look pretty for n < 12!
chars_per_city = 13

# wait this many seconds between county queries so we don't jam the server
# use command line option "--wait <seconds>" to override
nice_wait = 1.0


# list of county IDs in bay area, from csv downloaded from this URL
# (California is state ID 6)
# https://poweroutage.us/api/csv/county?key=[Api Key]&stateid=6

# 2910 Alameda 	
# 2912 Contra Costa
# 2916 Marin
# 2921 Napa 	
# 2939 San Francisco
# 2927 San Mateo
# 2929 Santa Clara     	
# 2931 Solano
# 2932 Sonoma

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
            #print("waiting to be nice")
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


def print_and_log(to_log, end=None):
    # Print to string
    if end is None:
        print(to_log)
        end = "\n"
    else:
        print(to_log, end)

    # Format and output to log
    to_log = to_log.replace(Fore.RED, '').replace(Style.RESET_ALL, '')
    with open(fileName, 'a') as f:
        f.write(to_log + end)


def print_customers(thresh):
    """ print utility information retrieved from API"""
    #rj = response.json()[0]

    # get data from PGE for timestamp
    utl_url="https://poweroutage.us/api/json_v1.6/utility?key={}&utilityid=760".format(authkey)
    response = requests.get(utl_url)    
    rj = response.json()[0]
    update_time = str(rj['LastUpdatedDateTime']).replace("T", " ")
    update_str = "Last Updated Time (UTC): {}".format(update_time)
    
    #print("{}".format(rj['UtilityName']))
    print_and_log("Customers: {}  Utility Outages: {}".format(total_cust, total_outs))
    print_and_log("City Outage Threshold: {:4.1f}%".format(100.0*thresh))
    print_and_log(update_str, end = " ")
    print_and_log(time.strftime("Current Time: %H:%M:%SZ", time.gmtime()), end=" ")


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

    # Initialize colorama
    init()

    # Set up path arguement
    parser = argparse.ArgumentParser(description='Arguments for runtime')
    parser.add_argument('--p', help='Path to executable directory', type=str, required=False)
    parser.add_argument('--t', help='Threshold to be used', type=float, required=False)

    parser.add_argument('--city-csv', help='List of cities to consider, in CSV format with CityByUtiltyId', type=str, required=False)

    parser.add_argument('--n', help='Number of cities to print per line', type=int, required=False)

    parser.add_argument('--wait', help='Time to wait between database queries, in seconds', type=float, required=False)

    parser.add_argument('--pad', help='Pad city fields to this number of characters', type=int, required=False)

    parser.add_argument('--hw', dest='hw', action='store_true', help='Connect and control power hardware (default)')

    parser.add_argument('--no_hw', dest='hw', action='store_false', help="Don't connect to hardware")
    parser.set_defaults(hw=True)

    args = parser.parse_args()

    
    # While we can't ping google
    while not checkForConnection('www.google.com', '80'):
        # Sleep for 5 seconds
        sleep(5)

    if args.t is not None:
        thresh = args.t
        
    if args.wait is not None:
        nice_wait = args.wait

    if args.p is not None:
        path = args.p

    if args.city_csv is not None:
        city_list_fname = args.city_csv
        
    if args.n is not None:
        cities_per_line = args.n

    if args.pad is not None:
        chars_per_city = args.pad
        if chars_per_city < 12:
            print("Warning on --pad: at least 12 characters needed")

    USE_HW = args.hw

    if USE_HW:

        import RPi.GPIO as GPIO

        if USE_RPI:
            RELAY_PIN = 18 # BCM 18, GPIO.1 physical pin 12
        elif USE_VIM:
            RELAY_PIN = 37

        # Relay is connected NORMALLY CLOSED so gpio.cleanup() leaves it SET.
        # set RELAY_PIN TRUE to TURN OFF
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(RELAY_PIN,GPIO.OUT)
        # power on on startup
        GPIO.output(RELAY_PIN, GPIO.LOW)


    #read list of good cities, need the CityByUtilityIds and abbreviations
    with open(city_list_fname, newline='') as csvfile:
        citycodes = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in citycodes:
            good_byutilityid.append(int(row[1]))    
            good_abbrs.append(row[6].strip())
        
    try:
        if True:

            sorted_cities = query_cities(good_byutilityid, nice_wait)

            #for c in sorted_cities:
            #    print(f"{c['abbr']}:{c['LastUpdatedDateTime']}")


            #print_and_log("\n\nCounty Outages:")
            above_threshold = print_city_data(sorted_cities, thresh)

            print_and_log("\n")
            print_customers(thresh)
            print_and_log("\n")

            
            if above_threshold:
                print_and_log("**POWER OFF** (ABOVE THRESHOLD)", end="")
                if USE_HW:
                    GPIO.output(RELAY_PIN, GPIO.HIGH)
            else:
                print_and_log("**POWER ON** (BELOW THRESHOLD)", end="")
                if USE_HW:
                    GPIO.output(RELAY_PIN, GPIO.LOW)
            #sleep(300.0 - len(county_ids)*nice_wait)

    except KeyboardInterrupt:
        print_and_log("interrupted")

        if USE_HW:
            try:
                GPIO.cleanup()               # clean up after yourself
            except RuntimeWarning:
                print('Caught warning')

        exit(0)
