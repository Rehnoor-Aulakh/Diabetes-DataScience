import sys
from scraper.downloader import download_html
from scraper.extractor import extract_main_content
from scraper.markdown_converter import convert_to_markdown

url = "https://medlineplus.gov/lab-tests/hemoglobin-a1c-hba1c-test/"
dl = download_html(url)
xml = extract_main_content(dl.html)
md = convert_to_markdown(xml)
print("EXTRACTED TEXT:")
print(md)
