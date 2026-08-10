import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
url = "https://www.niddk.nih.gov/search?q=Estimated+GFR+glomerular+filtration+rate"
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')
for a in soup.find_all('a', href=True):
    if '/health-information/' in a['href'] or '/research-funding/' in a['href']:
        print(a['href'])
