import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
url = "https://my.clevelandclinic.org/search?q=Creatinine+blood+test"
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')
main_c = soup.find('main') or soup
print("LINKS:")
for a in main_c.find_all('a', href=True):
    print(a['href'])
