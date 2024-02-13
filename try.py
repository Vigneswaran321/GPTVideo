from flask import Flask, render_template, send_file, send_from_directory, stream_with_context, Response
import requests
from bs4 import BeautifulSoup
import openai
import os
import time
import datetime

latest_headline = {"text": None, "time": datetime.datetime.min}
video_storage_path = 'headlines'
os.makedirs(video_storage_path, exist_ok=True)

# Function to fetch the latest headline
def get_latest_headline():
    global latest_headline
    url = 'https://www.prnewswire.com/news-releases/news-releases-list/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    headlines = soup.find_all('h3')

    for ele in headlines:
        headline_text = ele.text.strip()
        # Assuming each headline includes a timestamp or unique identifier
        # This part should be adjusted based on the actual structure of the news source
        if headline_text != latest_headline["text"]:
            latest_headline["text"] = headline_text
            # Update the time with the current fetch time; in a real scenario, parse the actual time
            latest_headline["time"] = datetime.datetime.now()
            return headline_text
    return None
new_headline = get_latest_headline()
print(new_headline)