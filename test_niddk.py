import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
url = "https://www.niddk.nih.gov/search?q=Creatinine+what+is+it+kidney"
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')
for a in soup.find_all('a', href=True):
    if 'creatinine' in a['href'].lower() or 'kidney' in a['href'].lower():
        print(a['href'])
