import feedparser as fp
from dateutil import parser
from dotenv import find_dotenv, load_dotenv, set_key, get_key
import io

#url = "https://lorem-rss.herokuapp.com/feed" #test url

def check_for_new_tweets():

    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    latest_tweet = parser.parse(get_key(dotenv_path, "LATEST_TWEET_DATE"))

    base_url = get_key(dotenv_path, ("NITTER_BASE_URL"))
    account_url = get_key(dotenv_path, ("NITTER_ACCOUNT_URL"))
    complete_url = base_url + account_url + "/rss"

    feed = fp.parse(complete_url) # Use this to get from url

    """
    # Use this to get from file
    f = open("src/test_rss_feed.txt", "r")
    text = f.read()
    f.close()
    feed = fp.parse(io.BytesIO(bytes(text, 'utf-8')))
    """

    entries = feed.entries

    latest_of_new_tweets = latest_tweet
    # Reverse the entries to process older tweets first,
    #   in case there are multiple new ones
    new_tweets = []
    for entry in reversed(entries):

        link = entry.link

        # Ignore retweets
        if account_url not in link:
            continue

        # Ignore old tweets
        #   Note: When comparing parsed dates, Greater = later.
        time = parser.parse(entry.published)
        if latest_tweet >= time:
            continue

        # Update the latest known tweet
        if time > latest_of_new_tweets:
            set_key(dotenv_path, "LATEST_TWEET_DATE", str(time))
            latest_of_new_tweets = parser.parse(get_key(dotenv_path, "LATEST_TWEET_DATE"))

        replacement_url = get_key(dotenv_path, "FXTWITTER_URL")
        final_link = link.replace(base_url, replacement_url)
        # clean trailing '#m' in links
        final_link = final_link.replace('#m', '')

        new_tweets.append(final_link)
    
    return new_tweets

