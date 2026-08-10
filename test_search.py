import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

url = "https://vsearch.nlm.nih.gov/vivisimo/cgi-bin/query-meta?v%3Aproject=medlineplus&v%3Asources=medlineplus-bundle&query=Hemoglobin+A1C+HbA1c+test"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

print("MEDLINEPLUS LINKS:")
for a in soup.find_all('a', href=True):
    href = a['href']
    if 'medlineplus.gov' in href:
        print(href)

url_ada = "https://diabetes.org/search?keywords=Understanding+A1C"
resp_ada = requests.get(url_ada, headers=headers)
soup_ada = BeautifulSoup(resp_ada.text, 'html.parser')
print("\nADA LINKS:")
for a in soup_ada.find_all('a', href=True):
    href = a['href']
    if href.startswith('/'):
        print(href)

