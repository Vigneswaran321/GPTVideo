from flask import Flask, render_template, send_file, send_from_directory, stream_with_context, Response
import requests
from bs4 import BeautifulSoup
import openai
import os
import time
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Global variables to store the latest headline and its publication time
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

# Function to generate audio from the headline
def generate_news_audio(headline):
    api_key = os.environ.get('OPENAI_API_KEY')
    client = openai.Client(api_key=api_key)
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You are a AI News Anchor acting similar like a human in a way that cannot be easily detected by the way of speaking and generate the content like a news anchor based upon the headlines received."},
            {"role": "user", "content": headline}
        ]
    )
    audio_content = completion.choices[0].message.content
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=audio_content
    )
    return response

# Function to request video processing (stub example, adjust to your video generation logic)
def request_video_processing(audio_url, headline):
    video_filename = f"{video_storage_path}/{headline.replace(' ', '_')}.mp4"
    # This is where you'd integrate with a video processing API using the audio_url
    # For this example, we're just returning a dummy filename
    return video_filename

# Function to manage video files
def manage_video_files():
    files = sorted([os.path.join(video_storage_path, f) for f in os.listdir(video_storage_path)], 
                   key=os.path.getctime)
    while len(files) > 10:
        os.remove(files.pop(0))

@app.route('/')
def index():
    # global latest_headline
    # new_headline = get_latest_headline()
    # if new_headline:
    #     audio_response = generate_news_audio(new_headline)
    #     audio_response.write_to_file('static\output.mp3')
    #     # video_file = request_video_processing(audio_response, new_headline)
    #     # manage_video_files()
    return render_template('index.html')

def scheduled_task():
    global latest_headline
    new_headline = get_latest_headline()
    if new_headline:
        audio_response = generate_news_audio(new_headline)
        audio_response.write_to_file('static/output.mp3')
        # video_file = request_video_processing(audio_response, new_headline)
        # manage_video_files()
    print("Task executed.")

@app.route('/video')
def video_stream():
    def generate():
        video_files = sorted([f for f in os.listdir(video_storage_path) if f.endswith('.mp4')],
                             key=lambda x: os.path.getctime(os.path.join(video_storage_path, x)))
        while True:
            for video_file in video_files:
                video_path = os.path.join(video_storage_path, video_file)
                with open(video_path, 'rb') as f:
                    data = f.read(1024 * 1024)
                    while data:
                        yield data
                        data = f.read(1024 * 1024)
                    time.sleep(1)  # Delay between videos to simulate continuous stream
    return Response(stream_with_context(generate()), mimetype='video/mp4')

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scheduled_task, trigger="interval", minutes=10)
    scheduler.start()
    try:
        app.run(use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()