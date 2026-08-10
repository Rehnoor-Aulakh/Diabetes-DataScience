import nbformat as nbf

nb = nbf.v4.new_notebook()

cells = []

# Intro
cells.append(nbf.v4.new_markdown_cell("# Data Cleaning\n\nData cleaning is a time consuming and unenjoyable task, yet it's a very important one. Keep in mind, \"garbage in, garbage out\".\nFeeding dirty data into a model will give us results that are meaningless.\n\n### Objective:\n1. Getting the data\n2. Cleaning the data\n3. Organizing the data - organize the cleaned data into a way that is easy to input into other algorithms\n\n### Output:\ncleaned and organized data in two standard text formats:\n1. Corpus - a collection of text\n2. Document-Term Matrix - word counts in matrix format"))

cells.append(nbf.v4.new_markdown_cell("## Getting The Data\n\nBlood Tests Data is available, but what it represents in real life has to be understood from the real medical data, so I plan on scrapping a medical website for these blood tests and how it leads to diabetes, I will create a corpus, which is a collection of text documents, make it lowercase, remove punctuation, stopwords, etc for the FIRST STAGE."))

cells.append(nbf.v4.new_code_cell("""# Web scraping, pickle imports
import requests
from bs4 import BeautifulSoup
import pickle

# Scrapes transcript data from niddk.nih.gov
def url_to_transcript(url):
    '''Returns transcript data specifically from niddk.nih.gov.'''
    page = requests.get(url).text
    soup = BeautifulSoup(page, "lxml")
    text = [p.text for p in soup.find_all('p')]
    print(url)
    return text

# URLs of transcripts in scope
urls = [
    'https://www.niddk.nih.gov/health-information/diagnostic-tests/a1c-test',
    'https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/prediabetes-insulin-resistance',
    'https://www.niddk.nih.gov/health-information/kidney-disease/chronic-kidney-disease-ckd/tests-diagnosis',
    'https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis',
    'https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/heart-disease-stroke'
]

# Medical topics
topics = ['a1c', 'insulin_resistance', 'kidney_tests', 'diabetes_tests', 'heart_disease']"""))

cells.append(nbf.v4.new_code_cell("""# Actually request transcripts (takes a few minutes to run)
transcripts = [url_to_transcript(u) for u in urls]"""))

cells.append(nbf.v4.new_code_cell("""# Pickle files for later use

# Make a new directory to hold the text files
import os
os.makedirs("transcripts", exist_ok=True)

for i, c in enumerate(topics):
    with open("transcripts/" + c + ".txt", "wb") as file:
        pickle.dump(transcripts[i], file)"""))

cells.append(nbf.v4.new_code_cell("""# Load pickled files
data = {}
for i, c in enumerate(topics):
    with open("transcripts/" + c + ".txt", "rb") as file:
        data[c] = pickle.load(file)"""))

cells.append(nbf.v4.new_code_cell("""# Double check to make sure data has been loaded properly
data.keys()"""))

cells.append(nbf.v4.new_code_cell("""# More checks
data['a1c'][:2]"""))

cells.append(nbf.v4.new_markdown_cell("## Cleaning The Data\n\nWhen dealing with numerical data, data cleaning often involves removing null values and duplicate data, dealing with outliers, etc. With text data, there are some common data cleaning techniques, which are also known as text pre-processing techniques.\n\nWith text data, this cleaning process can go on forever. There's always an exception to every cleaning step. So, we're going to follow the MVP (minimum viable product) approach - start simple and iterate."))

cells.append(nbf.v4.new_markdown_cell("### Assignment:\n1. Perform the following data cleaning on transcripts: i) Make text all lower case ii) Remove punctuation iii) Remove numerical values iv) Remove common non-sensical text (/n) v) Tokenize text vi) Remove stop words"))

cells.append(nbf.v4.new_code_cell("""# Let's take a look at our data again
next(iter(data.keys()))"""))

cells.append(nbf.v4.new_code_cell("""# Notice that our dictionary is currently in key: topic, value: list of text format
next(iter(data.values()))[:2]"""))

cells.append(nbf.v4.new_code_cell("""# We are going to change this to key: topic, value: string format
def combine_text(list_of_text):
    '''Takes a list of text and combines them into one large chunk of text.'''
    combined_text = ' '.join(list_of_text)
    return combined_text"""))

cells.append(nbf.v4.new_code_cell("""# Combine it!
data_combined = {key: [combine_text(value)] for (key, value) in data.items()}"""))

cells.append(nbf.v4.new_code_cell("""# We can either keep it in dictionary format or put it into a pandas dataframe
import pandas as pd
pd.set_option('max_colwidth', 150)

data_df = pd.DataFrame.from_dict(data_combined).transpose()
data_df.columns = ['transcript']
data_df = data_df.sort_index()
data_df"""))

cells.append(nbf.v4.new_code_cell("""# Let's take a look at the transcript for a1c
data_df.transcript.loc['a1c'][:200]"""))

cells.append(nbf.v4.new_code_cell("""# Apply a first round of text cleaning techniques
import re
import string

def clean_text_round1(text):
    '''Make text lowercase, remove text in square brackets, remove punctuation and remove words containing numbers.'''
    text = text.lower()
    text = re.sub('\\[.*?\\]', '', text)
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub('\\w*\\d\\w*', '', text)
    return text

round1 = lambda x: clean_text_round1(x)"""))

cells.append(nbf.v4.new_code_cell("""# Let's take a look at the updated text
data_clean = pd.DataFrame(data_df.transcript.apply(round1))
data_clean"""))

cells.append(nbf.v4.new_code_cell("""# Apply a second round of cleaning
def clean_text_round2(text):
    '''Get rid of some additional punctuation and non-sensical text that was missed the first time around.'''
    text = re.sub('[‘’“”…]', '', text)
    text = re.sub('\\n', '', text)
    return text

round2 = lambda x: clean_text_round2(x)"""))

cells.append(nbf.v4.new_code_cell("""# Let's take a look at the updated text
data_clean = pd.DataFrame(data_clean.transcript.apply(round2))
data_clean"""))

cells.append(nbf.v4.new_markdown_cell("## Organizing The Data\n\n### Assignment:\n1. Organized data in two standard text formats: a) Corpus - corpus is a collection of texts, and they are all put together neatly in a pandas dataframe here. b) Document-Term Matrix - word counts in matrix format"))

cells.append(nbf.v4.new_markdown_cell("### Corpus: Example\n\nA corpus is a collection of texts, and they are all put together neatly in a pandas dataframe here."))

cells.append(nbf.v4.new_code_cell("""# Let's take a look at our dataframe
data_df"""))

cells.append(nbf.v4.new_code_cell("""# Let's add the topics' full names as well
full_names = ['A1C Test', 'Diabetes Tests', 'Heart Disease', 'Insulin Resistance', 'Kidney Tests']

data_df['full_name'] = full_names
data_df"""))

cells.append(nbf.v4.new_code_cell("""# Let's pickle it for later use
data_df.to_pickle("corpus.pkl")"""))

cells.append(nbf.v4.new_markdown_cell("### Document-Term Matrix: Example\n\nFor many of the techniques we'll be using in future assignment, the text must be tokenized, meaning broken down into smaller pieces. The most common tokenization technique is to break down text into words. We can do this using scikit-learn's `CountVectorizer`, where every row will represent a different document and every column will represent a different word.\n\nIn addition, with `CountVectorizer`, we can remove stop words. Stop words are common words that add no additional meaning to text such as 'a', 'the', etc."))

cells.append(nbf.v4.new_code_cell("""# We are going to create a document-term matrix using CountVectorizer, and exclude common English stop words
from sklearn.feature_extraction.text import CountVectorizer

cv = CountVectorizer(stop_words='english')
data_cv = cv.fit_transform(data_clean.transcript)
data_dtm = pd.DataFrame(data_cv.toarray(), columns=cv.get_feature_names_out())
data_dtm.index = data_clean.index
data_dtm"""))

cells.append(nbf.v4.new_code_cell("""# Let's pickle it for later use
data_dtm.to_pickle("dtm.pkl")"""))

cells.append(nbf.v4.new_code_cell("""# Let's also pickle the cleaned data (before we put it in document-term matrix format) and the CountVectorizer object
data_clean.to_pickle('data_clean.pkl')
pickle.dump(cv, open("cv.pkl", "wb"))"""))

nb.cells = cells

with open('notebooks/ScrapingForNLP.ipynb', 'w') as f:
    nbf.write(nb, f)

print("Notebook successfully generated!")
