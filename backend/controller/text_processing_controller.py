from nltk.corpus import words, stopwords
from nltk.tokenize import word_tokenize
import string
import contractions
from dateutil import parser
import spacy
import enchant
import nltk
from nltk.data import find


def check_and_download_nltk_resources(resource_list):
    for resource_name in resource_list:
        try:
            find(resource_name)  # Check if the resource is already downloaded
            print(f"{resource_name} is already downloaded.")
        except LookupError:
            print(f"{resource_name} is missing. Downloading now...")
            # Remove the 'corpora/' or 'tokenizers/' part for download
            temp = resource_name.split('/')[1]
            packages = temp.split('.')[0]
            nltk.download(packages)


# List of NLTK resources to check
nltk_resources = [
    'corpora/stopwords.zip',
    'corpora/words.zip',
    'tokenizers/punkt.zip',
    'tokenizers/punkt_tab.zip'  # Adjust if punkt_tab is a valid resource
]

# Check and download the resources if they are missing
check_and_download_nltk_resources(nltk_resources)
nlp = spacy.load("en_core_web_sm")


class TextProcessing:
    @staticmethod
    def text_processing_model(text: str) -> list:
        expanded_text = contractions.fix(text)
        tokens = word_tokenize(expanded_text)
        punctuation_set = set(string.punctuation)
        filtered_tokens = [word for word in tokens if word not in punctuation_set]
        stopwords_list = set(stopwords.words('english'))
        english_words = set(words.words())
        keywords = [word.lower() for word in filtered_tokens if
                    word.lower() not in stopwords_list and word in english_words]

        return keywords

    @staticmethod
    def extract_information(query):
        doc = nlp(query)
        brands = []
        dates = []

        for ent in doc.ents:
            if ent.label_ == "ORG":  # Organizations can represent brands
                brands.append(ent.text)
            elif ent.label_ == "DATE":  # Dates
                dates.append(ent.text)

        return brands, dates

    @staticmethod
    def date_processor(text):
        try:
            parser.parse(text)
            return True
        except ValueError:
            return False

    @staticmethod
    def check_word(text):
        d = enchant.Dict("en_US")
        return d.check(text)

    @staticmethod
    def date_parser(text):
        try:
            date_obj = parser.parse(text)
            formatted_date = date_obj.strftime("%Y-%m-%d")
            return formatted_date
        except ValueError as e:
            print(e)
            return None
