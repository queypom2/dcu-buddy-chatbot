from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from chatterbot.response_selection import get_most_frequent_response
import logging
from chatterbot.comparisons import LevenshteinDistance

logging.basicConfig(level=logging.INFO)

# Creating ChatBot Instance
chatbot = ChatBot(
    'DCUBuddy',
    storage_adapter='chatterbot.storage.SQLStorageAdapter',
    preprocessors=[
        'chatterbot.preprocessors.clean_whitespace',
        'chatterbot.preprocessors.unescape_html'
    ],

    logic_adapters=[
        {
            'import_path': 'search_all_adapter.SearchMatch',
            'default_response': 'I am sorry, but I do not understand. I am still learning. <br><br> Please contact: mark.queypo2@mail.dcu.ie or conor.marsh2@mail.dcu.ie if you have any errors or any queries I should know.',
            "statement_comparison_function": LevenshteinDistance,
            'maximum_similarity_threshold': 0.90
        }
    ],
    database_uri='sqlite:///database.sqlite3'
)

trainer = ChatterBotCorpusTrainer(chatbot)
trainer.train("../training_data/")