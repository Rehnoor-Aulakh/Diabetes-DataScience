import requests
from bs4 import BeautifulSoup

urls = [
    'https://www.niddk.nih.gov/health-information/diagnostic-tests/a1c-test',
    'https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/prediabetes-insulin-resistance'
]
for u in urls:
    page = requests.get(u)
    print(u, page.status_code)
    soup = BeautifulSoup(page.text, "lxml")
    text = [p.text for p in soup.find_all('p')]
    print(len(text), "paragraphs")
    print(text[:2])
