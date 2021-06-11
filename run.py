from bs4 import BeautifulSoup
import requests
import json
import datetime
import praw
import configparser
import schedule
import time


config = configparser.ConfigParser()
config.read('conf.ini')
reddit_user = config['REDDIT']['reddit_user']
reddit_pass = config['REDDIT']['reddit_pass']
reddit_client_id = config['REDDIT']['reddit_client_id']
reddit_client_secret = config['REDDIT']['reddit_client_secret']
reddit_target_subreddit = config['REDDIT']['reddit_target_subreddit']
reddit_post_title = config['REDDIT']['reddit_post_title']
schedule_time = config['SCHEDULE']['schedule_time']
run_at_startup = config.getboolean('SETTINGS', 'run_at_startup')
test_mode = config.getboolean('SETTINGS', 'test_mode')

reddit = praw.Reddit(
    username=reddit_user,
    password=reddit_pass,
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent='Daily Writing Object (by u/impshum)'
)

reddit.validate_on_submit = True

update_me_next_time = True


def lovely_soup(url):
    r = requests.get(url, headers={
                     'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'})
    return BeautifulSoup(r.content, 'lxml')


def get_between(thing, start, end):
    return thing[thing.find(start) + len(start):thing.rfind(end)].strip()


def get_daily_tips():
    soup = lovely_soup('https://objectwriting.com/')
    post = soup.find('article', {'id': 'post-156'})
    table = post.find('table')
    script = table.find('script')
    tips = get_between(script.string.lower(), 'tips of the month',
                       'document.write(tiptitle)').split('\n')

    daily_tips = {}

    for i, tip in enumerate(tips):
        tip = get_between(tip.lower(), '<h1>', '</h1>').strip()
        day_tip = {i + 1: tip}
        daily_tips.update(day_tip)

    with open('tips.json', 'w') as f:
        json.dump(daily_tips, f)

    print('Updated tip jar')


def post_daily_tip():
    global update_me_next_time

    if update_me_next_time:
        get_daily_tips()
        update_me_next_time = False

    with open('tips.json', 'r') as f:
        tips = json.load(f)

    now = datetime.datetime.now()
    day = now.strftime('%-d')
    date = now.strftime('%m/%d/%Y')

    last_tip = list(tips.items())[-1][1]
    todays_tip = tips[day]

    with open('selftext.md') as f:
        selftext = f.read()

    title = f'({date}) {reddit_post_title} {todays_tip.title()}'

    reddit.subreddit(reddit_target_subreddit).submit(title, selftext=selftext)

    if last_tip == todays_tip:
        update_me_next_time = True

    print(title)


def post_daily_tip_test():
    global update_me_next_time

    c = 0
    for i in range(33):
        if update_me_next_time:
            get_daily_tips()
            update_me_next_time = False
            c = 0

        with open('tips.json', 'r') as f:
            tips = json.load(f)

        now = datetime.datetime.now().replace(day=1) + datetime.timedelta(days=c)
        day = now.strftime('%-d')
        date = now.strftime('%m/%d/%Y')

        last_tip = list(tips.items())[-1][1]
        todays_tip = tips[day]

        with open('selftext.md') as f:
            selftext = f.read()

        title = f'({date}) {reddit_post_title} {todays_tip.title()}'

        print(title)

        if last_tip == todays_tip:
            update_me_next_time = True

        c += 1


def main():
    if test_mode:
        post_daily_tip_test()
        return

    if run_at_startup:
        post_daily_tip()

    schedule.every().day.at(schedule_time).do(post_daily_tip)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
