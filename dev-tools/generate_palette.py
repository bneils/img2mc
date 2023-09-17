#!/usr/bin/env python3

# This was made to automate the process of grabbing the color palette from the Mojang wiki.

from bs4 import BeautifulSoup
import requests
import os
import sys

def download_palette():
    doc = requests.get('https://minecraft.fandom.com/wiki/Map_item_format')
    if doc.status_code != 200:
        sys.stderr.write("Couldn't access wiki with status code %d.\n" % doc.status_code)
        return

    soup = BeautifulSoup(doc.text, 'html.parser')
    table = soup.find('table', {'class': 'wikitable sortable stikitable'})
    colors = []
    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')

        # the third column contains the rgb pair
        color = [int(c) for c in cols[2].text.split(', ') if c.strip().isdecimal()]
        
        # handle transparent edge case
        if not color:
            colors.extend(['255'] * 12)
        else:
            # expand palette for gradients
            for multiplier in (180, 220, 255, 135):
                colors.extend([str(c * multiplier // 255) for c in color])

    with open(os.path.join(os.path.dirname(__file__), 'palette.csv'), 'w') as f:
        f.write(','.join(colors))

if __name__ == "__main__":
    download_palette()
