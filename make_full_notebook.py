import nbformat as nbf
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NOTEBOOK_PATH = ROOT / "notebooks" / "ScrapingForNLP.ipynb"

nb = nbf.v4.new_notebook()
cells = []

# Intro
cells.append(nbf.v4.new_markdown_cell("# Clinical NLP Engine: Data Pipeline\n\nThis notebook demonstrates the **Certus Clinical Language Engine** architecture. We fetch articles using our modular scraper, and then pass them through our `Medical Normalization Pipeline` (which relies on a dynamic `Medical Ontology` and custom `Medical Stopwords`). We output a versioned `knowledge_v1` TF-IDF corpus."))

cells.append(nbf.v4.new_code_cell("""import os
import sys
from pathlib import Path
import pandas as pd
import pickle

def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "scraper").is_dir() and (candidate / "corpus").is_dir():
            return candidate
    raise RuntimeError("Could not locate the Diabetes DataScience project root.")

PROJECT_ROOT = find_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MANIFEST_PATH = PROJECT_ROOT / "manifest_v1.json"
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge_v1"

from scraper.manifest_loader import load_manifest
from scraper.search_provider import search_article_url
from scraper.downloader import download_html
from scraper.extractor import extract_main_content
from scraper.markdown_converter import convert_to_markdown
from corpus.medical_normalizer import MedicalPipeline"""))

cells.append(nbf.v4.new_markdown_cell("## 1. Scraping the Corpus\nWe will extract the required jobs from our manifest. For this assignment, we will process the first 10 successful articles to populate our corpus."))

cells.append(nbf.v4.new_code_cell("""# Load jobs
all_jobs = load_manifest(str(MANIFEST_PATH))
dataset = {}
full_names = {}
successful = 0

for job in all_jobs:
    if successful >= 10:
        break
        
    topic_id = job.topic_id
    source = job.source_id
    key = f"{topic_id}_{source}"
    
    url = search_article_url(job.query, job.search_url_template)
    if not url: continue
        
    dl_result = download_html(url)
    if dl_result.error: continue
        
    xml = extract_main_content(dl_result.html)
    if not xml: continue
        
    md = convert_to_markdown(xml)
    
    dataset[key] = [md]
    full_names[key] = f"{job.topic_id.upper()} ({job.source_id.upper()})"
    successful += 1
    
print(f"Successfully scraped {len(dataset)} documents.")"""))

cells.append(nbf.v4.new_markdown_cell("## 2. Medical Normalization Pipeline\nUnlike generic NLP (which destroys thresholds, clinical units, and negation), we use our custom pipeline to normalize clinical text, map entities to the ontology, and preserve operators like `<` or `>=`."))

cells.append(nbf.v4.new_code_cell("""# Create DataFrame
data_df = pd.DataFrame.from_dict(dataset).transpose()
if data_df.empty:
    print("Warning: Used fallback data due to network blocks.")
    data_df = pd.DataFrame({'transcript': ['HbA1c > 6.5% indicates diabetes. No evidence of nephropathy. Creatinine 1.2 mg/dL.']})

data_df.columns = ['transcript']
data_df = data_df.sort_index()

# Run through Medical Pipeline
pipeline = MedicalPipeline()

data_clean = pd.DataFrame(data_df.transcript.apply(lambda x: pipeline.process_document(str(x))))
data_clean.columns = ['transcript']

if not data_df.empty and len(full_names) == len(data_clean):
    data_clean['full_name'] = [full_names.get(idx, idx) for idx in data_clean.index]

data_clean.head()"""))

cells.append(nbf.v4.new_markdown_cell("## 3. TF-IDF Matrix Generation\nWe pass our semantically rich tokens directly into the vectorizer. Because our custom pipeline already removed generic stopwords and preserved clinical ones, we do not use the default English stopword list here."))

cells.append(nbf.v4.new_code_cell("""from sklearn.feature_extraction.text import TfidfVectorizer

# Our tokens are clean, so we don't apply lowercase or standard stop_words here again
tfidf = TfidfVectorizer(lowercase=False, stop_words=None, token_pattern=r'\\S+')
data_tfidf = tfidf.fit_transform(data_clean.transcript)

data_dtm = pd.DataFrame(data_tfidf.toarray(), columns=tfidf.get_feature_names_out())
data_dtm.index = data_clean.index

data_dtm.head()"""))

cells.append(nbf.v4.new_markdown_cell("## 4. Saving to Versioned Storage (`knowledge_v1`)\nWe store the resulting corpus, matrix, and vectorizer in a version-controlled directory. If we update our Medical Ontology tomorrow, we will output to `knowledge_v2`."))

cells.append(nbf.v4.new_code_cell("""os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

data_clean.to_pickle(KNOWLEDGE_DIR / "corpus.pkl")
data_dtm.to_pickle(KNOWLEDGE_DIR / "dtm.pkl")
pickle.dump(tfidf, open(KNOWLEDGE_DIR / "tfidf.pkl", "wb"))

print("Successfully saved artifacts to knowledge_v1/")"""))

nb.cells = cells
with open(NOTEBOOK_PATH, 'w') as f:
    nbf.write(nb, f)

print("Notebook updated successfully!")
