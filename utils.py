from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, PromptTemplate
from langchain_community.document_loaders import YoutubeLoader
import tiktoken
import streamlit as st
from langchain.schema import HumanMessage

GPT_MODEL = "gpt-3.5-turbo-1106"

BLOG_PROMPT_VANILLA = """I want you to act as a blogger and a {category} industry expert. The topic of the post will be {topic}. This post should be helpful for people who care about {category}. The length of the blog post will be around {word_count} words.You should be writing as an individual blogger with a personal approach so do not use plural first-person to refer to yourself e.g. “our”, “we”. Only use singular first-person. Do not use passive voice. Break the blog post down into relevant sections rather than one long paragraph. Make it so it is easily readable by a 4th grader. Only include the blog content, nothing else. """
BLOG_PROMPT_WTH_VIDEO = """I want you to act as a blogger and a {category} industry expert. The topic of the post will be {topic}. This post should be helpful for people who care about {category}. The length of the blog post will be around {word_count} words.You should be writing as an individual blogger with a personal approach so do not use plural first-person to refer to yourself e.g. “our”, “we”. Only use singular first-person. Do not use passive voice. Break the blog post down into relevant sections rather than one long paragraph. Make it so it is easily readable by a 4th grader. Only include the content, no title. I am also providing a summary of the transcript of a youtube video which is related to the topic, which I want you to incorporate and reference in this blog. Here it is - {summary}"""
SUMMARY_PROMPT = """You are a video transcript summarizer."""

def write_blog(topic, category, word_count, api_key, url):
    chat = ChatOpenAI(model=GPT_MODEL, openai_api_key=api_key, max_tokens=3500)
 
    system_message_prompt = SystemMessagePromptTemplate.from_template(BLOG_PROMPT_VANILLA)
    human_template = BLOG_PROMPT_VANILLA

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt]
    )

    blog_response = chat(
        chat_prompt.format_prompt(
           topic=topic, category=category, word_count=word_count
        ).to_messages()
    )

    if url:
        summary = summarize_video(url, api_key)
        ammend_prompt = ChatPromptTemplate.from_messages(
        [HumanMessagePromptTemplate.from_template("Create new blog content by including ideas from this summary of a video of the related topic - {summary}")]
        )
        amended_blog_response = chat(ammend_prompt.format_prompt(summary=summary).to_messages())
        title_response = chat([HumanMessage(content="Generate a catchy title for this blog")])
        return title_response.content, amended_blog_response.content


    return title_response.content, blog_response.content


def summarize_video(url, api_key):
    transcript = get_transcript(url)
    token_count = count_tokens(transcript)

    if token_count > 10001:
        st.error("Video is too long i.e. >10001 tokens. Try a shorter video", icon="🚨")
        return
    
    chat = ChatOpenAI(model=GPT_MODEL, openai_api_key=api_key)
    system_message_prompt = SystemMessagePromptTemplate.from_template(SUMMARY_PROMPT)
    human_template = """Summarize this transcript in 250 words - ```{transcript}```"""
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    summary_response = chat(
        chat_prompt.format_prompt(
           transcript=transcript
        ).to_messages()
    )

    return summary_response.content


def get_transcript(url: str) -> str:
    try:
        loader = YoutubeLoader.from_youtube_url(url, add_video_info=False)
        docs = loader.load()
        if docs:
            doc = docs[0]
            transcript = doc.page_content
            return transcript
    except Exception as e:
        st.error("Failed to load transcript from URL. Check Link!", icon="🚨")
        return


def count_tokens(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(GPT_MODEL)
    num_tokens = len(encoding.encode(string))
    return num_tokens
