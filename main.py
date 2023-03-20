import logging.handlers
import os
from utils import *
import lmproof

ARTICLES_PATH = './articles/'
TOPICS_FILE_NAME = 'topics.csv'

def create_blog_post_e2e(logger): 
    # Get Topic
    maybeTopic = get_topic(TOPICS_FILE_NAME)

    if maybeTopic is None:
        exit()

    # Write an article for that topic
    try:
        OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    except KeyError:
        logger.info("Token not available!")
        exit()
    
    topic = maybeTopic

    # Generate blog prompt
    logger.info("Generating prompt!")
    prompt = generate_blog_prompt(topic)
    logger.info("Prompt generated, writing article!")

    article = write_prompt(prompt, OPENAI_API_KEY)
    proofed_article = ''
    logger.info("Article generated, proofreading :)")

    # Proofread that article
    try: 
        proofread = lmproof.load("en")
        proofed_article = proofread.proofread(article)
        logger.info("Proofread finished, writing to file!")
    except:
        logger.info("Proofread failed, writing to file, please check grammar!")


    # Write locally for now
    if not os.path.exists(ARTICLES_PATH):
        os.makedirs(ARTICLES_PATH)

    filename = topic['topic'] + '.txt'
    with open(os.path.join(ARTICLES_PATH, filename), 'w') as f:
        f.write(article)

    if proofed_article != '': 
        filenameProofed = topic['topic'] + 'PROOFED' + '.txt'
        with open(os.path.join(ARTICLES_PATH, filenameProofed), 'w') as f:
            f.write(proofed_article)

    # ToDo: Write that article to Google Drive


if __name__ == "__main__":
    logger = setup_logger()
    create_blog_post_e2e(logger)