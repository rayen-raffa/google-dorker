"""Google dorker 1.0

Usage:
  dorker.py <domain> <file-name> <pages> <processes>
  dorker.py (-h | --help)
  dorker.py --version

Arguments:
  <domain>        Domain to be Searched
  <file-name>     File containing strings to search in url (located inside wordlists folder)
  <pages>         Number of pages
  <processes>     Number of parallel processes

Options:
  -h --help     Show this screen
  --version     Show version

"""

import requests
import re
import sys
import os
import csv
import json
from docopt import docopt
from bs4 import BeautifulSoup
from time import time as timer
from functools import partial
from multiprocessing import Pool
from urllib.parse import unquote


# Reading credentials' file
def read_credentials():
    # Credentials' file path
    CRED_FILE = './config.csv'

    if (not os.path.isfile(CRED_FILE)):
        print('Error : Config file {} missing ! Exiting ..')
        sys.exit()

    credentials = {
        'current': None,
        'total': 0
    }
    with open(CRED_FILE) as csv_file:
        lines = csv.DictReader(csv_file)
        for row in lines:
            if (not credentials['current']):
                credentials['current'] = 0
            # Add (id, key) pair to dictionary
            credentials[str(credentials['total'])] = row
            credentials['total'] += 1
        print(json.dumps(credentials, sort_keys=True, indent=4))
        print('\nFound {} id,key pairs.'.format(credentials['total']))
    return credentials

# Search the dork string and retrieve urls
def get_urls(search_string,API_KEY,CSE_ID,start):
    temp = []
    url = 'https://www.googleapis.com/customsearch/v1'
    payload = {'key':API_KEY, 'cx':CSE_ID, 'q': search_string, 'start': start}
    # my_headers = {'User-agent': 'Mozilla/11.0'}
    r = requests.get(url, params=payload) #, headers=my_headers
    print(r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    divtags = soup.find_all('div', class_='kCrYT')

    for div in divtags:
        try:
            temp.append(re.search('url\?q=(.+?)\&sa', div.a['href']).group(1))
        except:
            continue
    return temp

# Join search terms in a single dork string
def create_dork_string(domain, file_name):

    file_path = './wordlists/{}'.format(file_name)

    if not os.path.isfile(file_path):
        print('File "' +file_path+ '" does not exist')
        sys.exit()

    try:
        dork_string = ''

        # Read the contents of file and create a search string
        with open(file_path) as fp:
            for line in fp:
                if dork_string == '':
                    dork_string = 'inurl:' + line.strip()
                    continue
                dork_string += ' OR inurl:' + line.strip()
        return 'site:' + domain + ' ' + dork_string
    except:
        print('Error occured while reading file')
        sys.exit()


def main():
    start = timer()
    result = []

    # Command line interface
    arguments = docopt(__doc__, version='Google dorker 1.0')

    # Get input
    domain = arguments['<domain>']
    file_name = arguments['<file-name>']
    pages = arguments['<pages>']
    processes = int(arguments['<processes>'])

    # Create search string
    search = create_dork_string(domain, file_name)

    # Multi-Processing
    make_request = partial(get_urls, search)
    pagelist = [str(x*10) for x in range(0, int(pages))]
    with Pool(processes) as p:
        tmp = p.map(make_request, pagelist)
    for x in tmp:
        result.extend(x)
    
    # Remove duplicate urls
    result = list(set(result))
    
    print(*result, sep='\n')
    print('\nTotal URLs Scraped : %s ' % str(len(result)))
    print('Script Execution Time : %s ' % (timer() - start, ))


if __name__ == '__main__':
    # main()
    credentials = read_credentials()