from flask import Flask, render_template, request
from googleapiclient.discovery import build
import pandas as pd
from sentiment import analyze_comment_sentiment
from urllib.parse import urlparse, parse_qs
import traceback

app = Flask(__name__)

# Replace with your YouTube Data API key
YOUTUBE_API_KEY = '' # Place your API key  
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# Extract video ID from various YouTube URL formats
def extract_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    elif 'youtube' in parsed_url.hostname:
        return parse_qs(parsed_url.query).get('v', [None])[0]
    return None

# Fetch YouTube comments using the API
def get_comments(video_id, max_comments=1000):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)
    comments = []
    next_page_token = None

    while len(comments) < max_comments:
        response = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=1000,
            textFormat='plainText',
            pageToken=next_page_token
        ).execute()

        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment)
            if len(comments) >= max_comments:
                break

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return comments

# Flask route for index page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        try:
            video_id = extract_video_id(url)
            if not video_id:
                raise ValueError("Invalid YouTube URL format.")

            comments = get_comments(video_id)
            if not comments:
                raise ValueError("No comments found or comments are disabled.")

            data = []
            for comment in comments:
                sentiment = analyze_comment_sentiment(comment)
                data.append({'Comment': comment, 'Sentiment': sentiment})

            df = pd.DataFrame(data)
            summary = df['Sentiment'].value_counts().to_dict()

            return render_template('index.html', summary=summary, data=df.to_dict(orient='records'))
        
        except Exception as e:
            # Print full error traceback in terminal for debugging
            traceback.print_exc()
            # Show basic error to user
            return f"<h2>Error: {str(e)}</h2>"

    return render_template('index.html')

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
