from flask import Flask,request,jsonify
from linkedin_api import Linkedin
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
import re

# Authenticate using LinkedIn account credentials
username = 'nchimote02@gmail.com'
password = 'nvc@2002'
api = Linkedin(username, password)


def fetch_basic_linkedin_data(userid):
    
    basic_info=api.get_profile(userid)
    connections=api.get_profile_connections(userid)
    views=api.get_current_profile_views()
    requests=api.get_invitations()
    posts=api.get_profile_posts(userid)

    data={
        'name': basic_info.get('firstName'),
        'connections': len(connections),
        'views': views,
        'requests': len(requests),
        'posts': len(posts)
    }

    return data

def perform_sentiment_analysis(comments_response):
    comments = comments_response.json().get('data', [])
    # Sentiment analyzer using VADER
    analyzer = SentimentIntensityAnalyzer()

    # Lists to store sentiment values
    compound_scores = []
    sentiments = []

    # Analyze sentiment for each comment
    for comment_data in comments:
        comment_text = comment_data.get('comment', {}).get('values', [{}])[0].get('value', '')

        if comment_text:
            # Get compound sentiment score from VADER
            compound_score = analyzer.polarity_scores(comment_text)['compound']

            # Classify sentiment as positive, neutral, or negative based on the compound score
            if compound_score >= 0.05:
                sentiment = 'Positive'
            elif compound_score <= -0.05:
                sentiment = 'Negative'
            else:
                sentiment = 'Neutral'

            # Store sentiment values for visualization
            compound_scores.append(compound_score)
            sentiments.append(sentiment)

    # Visualize sentiment distribution using a pie chart
    sentiment_counts = {'Positive': sentiments.count('Positive'), 'Neutral': sentiments.count('Neutral'), 'Negative': sentiments.count('Negative')}
  
    return sentiment_counts

def comment_frequency_data(comments_response):
    # Dictionary to store the number of comments for each date
    comments = comments_response.json().get('data', [])

    comments_by_date = {}

    # Extract the comment timestamps and count the number of comments for each date
    for comment_data in comments:
        timestamp = comment_data.get('createdTime', 0) / 1000  # Convert milliseconds to seconds
        date = datetime.utcfromtimestamp(timestamp).date()

        # Update the comment count for the specific date
        comments_by_date[date] = comments_by_date.get(date, 0) + 1

    # Sort the data by date
    sorted_dates = sorted(comments_by_date.keys())
    comment_counts = [comments_by_date[date] for date in sorted_dates]

    data={
        'sorted_dates': sorted_dates,
        'comment_counts': comment_counts
    }

    return data

def fetch_linkedin_data(post_url):
    try:
        if post_url:
            # Extract post ID from the URL
            match = re.search(r':activity:(\d+)', post_url)

            if match:
                post_id = match.group(1)

                # Get post comments
                comments = api.get_post_comments(post_id)

                # Perform sentiment analysis
                sentiment_data = perform_sentiment_analysis(comments)

                # Calculate comment frequency
                comment_frequency = comment_frequency_data(comments)


                data = {
                    'sentiment_data': sentiment_data,
                    'comment_frequency': comment_frequency,
                }

                return data

            else:
                return jsonify({'error': 'Unable to extract post ID from the provided URL'})

        else:
            return jsonify({'error': 'No URL provided'})

    except Exception as e:
        print(f"Error fetching LinkedIn data: {e}")
        return jsonify({'error': 'Error fetching LinkedIn data'})

