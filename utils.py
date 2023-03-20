import openai
import pandas as pd
from datetime import datetime
import logging
import logging.handlers
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Retrieve topic from csv
def get_topic(filename):
    topics = pd.read_csv(filename)
    topics = topics.fillna('')
    
    try: 
        topic_index = topics[topics.isUsed == False].index
        topic_index[0]
    except:
        print('get_topic: No Available Topics Found :(')
        return None

    current_time = datetime.now()

    topics.loc[topic_index[0], 'isUsed'] = True
    topics.loc[topic_index[0], 'usedOn'] = current_time

    topics.to_csv(filename, index=False)
    topic = topics.iloc[topic_index].to_dict(orient='records')[0]

    topic['keywords'] = [s.strip() for s in topic['keywords'].split(', ')] 
    
    return topic

# Generate prompt for chat-gpt given the topic
def generate_blog_prompt(blog_topic):
    # heading, topic,category,description,keywords,wordCount,freeTextPrompt,isUsed,usedOn
    topic = blog_topic['topic']
    heading = blog_topic['heading']
    industry = blog_topic['industry']
    description = blog_topic['description']
    keywords = blog_topic['keywords']
    wordCount = blog_topic['wordCount']
    freeTextPrompt = blog_topic['freeTextPrompt']
    categories = blog_topic['categories']


    main = "I want you to act as a blogger and a {} industry expert. The topic of the post will be '{}'. This post should be helpful for people who care about {}. ".format(industry, topic, categories)
    title = "The title of the post is {}. ".format(heading) if heading != '' else ''
    length = "The length of the blog post will be around {} words. ".format(wordCount) if wordCount != '' else "The length of the blog post will be around 395 words. "
    # tone = "The tone will be [informal/ helpful/ persuasive/ professional/ authoritative etc…]."
    instructions = "You should be writing as an individual blogger with a personal approach so do not use plural first-person to refer to yourself e.g. “our”, “we”. Only use singular first-person. Do not use passive voice. Break the blog post down into relevant sections rather than one long paragraph. Make it so it is easily readable by a 4th grader."
    keywords = "I want you to include these keywords: {}".format(' '.join(keywords)) if len(keywords) > 1 else ''

    return main + title  + length + description +  instructions + keywords + freeTextPrompt

# Write a blog using Chat-GPT
def write_prompt(prompt, api_key):
    openai.api_key = api_key

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=0.5,
    )

    return response.choices[0].text.strip()

def create_doc_with_folder(doc_title, folder_name, credentials):    
    # authenticate with the Google Drive API and Google Docs API using a service account
    credentials = service_account.Credentials.from_service_account_info(credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
    docs_service = build('docs', 'v1', credentials=credentials)

    try:
        # create the folder in the root directory of the Google Drive
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive_service.files().create(body=folder_metadata, fields='id').execute()

        # create the Google Doc inside the folder
        doc_metadata = {
            'title': doc_title,
            'parents': [folder.get('id')],
            'mimeType': 'application/vnd.google-apps.document'
        }
        doc = docs_service.documents().create(body=doc_metadata).execute()

        print(f'Created Google Doc "{doc_title}" with folder "{folder_name}"')
    except HttpError as error:
        print(f'An error occurred: {error}')
        doc = None

    return doc
    

def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger_file_handler = logging.handlers.RotatingFileHandler(
        "status.log",
        maxBytes=1024 * 1024,
        backupCount=1,
        encoding="utf8",
    )
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger_file_handler.setFormatter(formatter)
    logger.addHandler(logger_file_handler)

    return logger
