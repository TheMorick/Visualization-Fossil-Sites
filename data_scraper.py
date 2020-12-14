import wikipedia
from bs4 import BeautifulSoup as bs

page = wikipedia.WikipediaPage('List of fossil sites')
soup = bs(page.html(), 'html.parser')

table = soup.find(attrs = ['wikitable', 'sortable'])
headers = [child.text[:-1] for child in table.tr.contents if child != '\n']
headers.append("Latitude")
headers.append("Longitude")


entries = [entry for entry in table.tr.fetchNextSiblings()]
start = 0
stop = len(entries)
data = [[child.text for child in entries[i].contents if child != '\n'] for i in range(start,stop)]
for entry in data:
    entry[-1] = entry[-1][:-1]

for i in range(start,stop):
    coordinates_found = True
    try:
        new_page = wikipedia.page(entries[i].find('a'))
    except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError):
        coordinates_found = False
    if coordinates_found:
        try:
            coords = new_page.coordinates
            lat = float(coords[0])
            lon = float(coords[1])
        except KeyError:
            coordinates_found = False
    if not coordinates_found:
        lat = "NA"
        lon = "NA"
    data[i - start].append(lat)
    data[i - start].append(lon)

for row in data:
    print(row)

    #Open file
f = open("fossil_sites_raw.csv", "w")

    #Write headers into file
s = ""
for head in headers:
    s = s + head + ","
s = s[:-1] + '\n'
f.write(s)

    #Write data into file
for row in data:
    s = ""
    for col in row:
        s = s + str(col) + ","
    s = s[:-1] + '\n'
    f.write(s)

f.close()

