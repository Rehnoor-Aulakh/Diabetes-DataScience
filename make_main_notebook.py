import nbformat as nbf

nb = nbf.v4.new_notebook()

cells = []

# Intro
cells.append(nbf.v4.new_markdown_cell("# Medical Knowledge Base: Scraper & NLP Pipeline\n\nThis notebook acts as the main tutorial to understand the **Scraper Service** architecture we built for Certus Diagnostics. It demonstrates how we fetch medical data, extract the main content, convert it to clean Markdown, and then applies the NLP text-cleaning architecture (Corpus & Document-Term Matrix) required for the assignment."))

cells.append(nbf.v4.new_markdown_cell("## 1. Understanding the Scraper Service\n\nInstead of a simple scraping script, we built a modular pipeline. Let's import the individual components to see how a document goes from a URL to clean Markdown."))

cells.append(nbf.v4.new_code_cell("""import os
import sys
from pprint import pprint

# Ensure the root directory is in the path to import our scraper package
sys.path.append(os.path.abspath('..'))

from scraper.downloader import download_html
from scraper.extractor import extract_main_content
from scraper.markdown_converter import convert_to_markdown
from scraper.quality_checker import check_quality"""))

cells.append(nbf.v4.new_markdown_cell("### Step 1: Downloading Raw HTML\nThe `downloader` module handles HTTP requests, retries, and captures metadata like ETags for versioning."))

cells.append(nbf.v4.new_code_cell("""# Let's fetch a direct article about the A1C test from NIDDK
url = "https://www.niddk.nih.gov/health-information/diagnostic-tests/a1c-test"
download_result = download_html(url)

print(f"Status: Downloaded successfully. Length: {len(download_result.html)} characters.")
print(f"ETag: {download_result.etag}")

raw_html = download_result.html"""))

cells.append(nbf.v4.new_markdown_cell("Let's look at a snippet of the **Raw HTML**. Notice how messy it is with navigation, scripts, and footers."))

cells.append(nbf.v4.new_code_cell("""# Show the first 1000 characters of raw HTML
print(raw_html[:1000])"""))

cells.append(nbf.v4.new_markdown_cell("### Step 2: Content Extraction\nThe `extractor` module uses `trafilatura` and `BeautifulSoup` to strip away the ads, navigation, and footers, leaving only the clinical article content in a structured XML format (preserving tables and headings)."))

cells.append(nbf.v4.new_code_cell("""extracted_xml = extract_main_content(raw_html)
print(f"Extracted content length: {len(extracted_xml)} characters.")
print("\\nSnippet of extracted XML:\\n", extracted_xml[:1000])"""))

cells.append(nbf.v4.new_markdown_cell("### Step 3: Markdown Conversion\nThe `markdown_converter` takes that structured XML and turns it into clean, readable Markdown suitable for our Knowledge Base and Vector DB."))

cells.append(nbf.v4.new_code_cell("""clean_markdown = convert_to_markdown(extracted_xml, metadata_header={"url": url, "source": "NIDDK"})
print("=== CLEANED MARKDOWN ===\\n")
print(clean_markdown[:1500])"""))

cells.append(nbf.v4.new_markdown_cell("### Step 4: Quality Checker\nBefore we save this to our corpus, the `quality_checker` ensures it's not garbage data (e.g., a 404 page or a search hub)."))

cells.append(nbf.v4.new_code_cell("""quality_result = check_quality(clean_markdown, keywords=["a1c", "diabetes", "blood"])
pprint(quality_result.__dict__)"""))

cells.append(nbf.v4.new_markdown_cell("---\n\n## 2. Completing the NLP Assignment (Corpus & DTM)\n\nNow that we understand how the scraper produces high-quality text, let's load a few scraped documents (or simulate them here) and apply the standard Data Cleaning and NLP structuring techniques: **Corpus** and **Document-Term Matrix**."))

cells.append(nbf.v4.new_code_cell("""# Let's fetch a few more articles to build our corpus
urls = {
    'a1c': 'https://www.niddk.nih.gov/health-information/diagnostic-tests/a1c-test',
    'insulin_resistance': 'https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/prediabetes-insulin-resistance',
    'kidney_tests': 'https://www.niddk.nih.gov/health-information/kidney-disease/chronic-kidney-disease-ckd/tests-diagnosis'
}

data = {}
for topic, u in urls.items():
    print(f"Fetching {topic}...")
    html = download_html(u).html
    xml = extract_main_content(html)
    md = convert_to_markdown(xml)
    data[topic] = [md] # Store as a list of strings to match the assignment format
    
print("Data loaded successfully!")"""))

cells.append(nbf.v4.new_markdown_cell("### Data Cleaning\nWe will remove punctuation, lowercase the text, and remove numbers to prepare it for tokenization."))

cells.append(nbf.v4.new_code_cell("""import pandas as pd
import re
import string

pd.set_option('max_colwidth', 150)

# Create DataFrame
data_df = pd.DataFrame.from_dict(data).transpose()
data_df.columns = ['transcript']
data_df = data_df.sort_index()

# Round 1 Cleaning
def clean_text_round1(text):
    text = text.lower()
    text = re.sub('\\[.*?\\]', '', text)
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub('\\w*\\d\\w*', '', text)
    return text

# Round 2 Cleaning (New lines)
def clean_text_round2(text):
    text = re.sub('[‘’“”…]', '', text)
    text = re.sub('\\n', ' ', text)
    return text

data_clean = pd.DataFrame(data_df.transcript.apply(lambda x: clean_text_round1(x)))
data_clean = pd.DataFrame(data_clean.transcript.apply(lambda x: clean_text_round2(x)))

# The Corpus
data_clean['full_name'] = ['A1C Test', 'Insulin Resistance', 'Kidney Tests']
data_clean"""))

cells.append(nbf.v4.new_markdown_cell("### Document-Term Matrix (DTM)\nUsing `CountVectorizer`, we tokenize the text, remove stop words, and create a matrix of word frequencies."))

cells.append(nbf.v4.new_code_cell("""from sklearn.feature_extraction.text import CountVectorizer

cv = CountVectorizer(stop_words='english')
data_cv = cv.fit_transform(data_clean.transcript)
data_dtm = pd.DataFrame(data_cv.toarray(), columns=cv.get_feature_names_out())
data_dtm.index = data_clean.index

data_dtm.head()"""))

cells.append(nbf.v4.new_markdown_cell("### Saving the Data\nFinally, we pickle the corpus, the DTM, and the Vectorizer for future assignments."))

cells.append(nbf.v4.new_code_cell("""import pickle

# Save Corpus
data_clean.to_pickle("corpus.pkl")

# Save Document-Term Matrix
data_dtm.to_pickle("dtm.pkl")

# Save CountVectorizer
pickle.dump(cv, open("cv.pkl", "wb"))

print("NLP artifacts saved successfully!")"""))

nb.cells = cells

with open('notebooks/ScrapingForNLP.ipynb', 'w') as f:
    nbf.write(nb, f)

print("Main Notebook successfully generated!")
