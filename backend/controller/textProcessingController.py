from nltk.corpus import words, stopwords
from nltk.tokenize import word_tokenize
import string
import nltk
import contractions
from dateutil import parser
import enchant

# # Download necessary NLTK corpora and models
# nltk.download('stopwords')
# nltk.download('words')
# nltk.download('punkt')
# nltk.download('punkt_tab')

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
