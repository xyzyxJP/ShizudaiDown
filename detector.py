from bs4 import BeautifulSoup as bs4
from lxml import html
import os
import psycopg2 as pg
import requests
import time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import datetime
import seaborn as sns
import tweepy

session = requests.session()
apache = None

GAKUJO_USERNAME = os.environ.get('GAKUJO_USERNAME')
GAKUJO_PASSWORD = os.environ.get('GAKUJO_PASSWORD')
DATABASE_URL = os.environ.get('DATABASE_URL')
TWITTER_ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_SECRET = os.environ.get('TWITTER_ACCESS_SECRET')
TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY')
TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET')


def calc_duration():
    start_time = time.perf_counter()
    session = requests.session()
    session.get('https://gakujo.shizuoka.ac.jp/portal/')
    session.post(
        'https://gakujo.shizuoka.ac.jp/portal/login/preLogin/preLogin', data={'mistakeChecker': '0'})
    session.get(
        'https://gakujo.shizuoka.ac.jp/UI/jsp/topPage/topPage.jsp')
    session.post('https://gakujo.shizuoka.ac.jp/portal/shibbolethlogin/shibbolethLogin/initLogin/sso',
                 data={'selectLocale': 'ja', 'mistakeChecker': '0', 'EXCLUDE_SET': ''})
    session.get(
        'https://idp.shizuoka.ac.jp/idp/profile/SAML2/Redirect/SSO?execution=e1s1')
    login = session.post('https://idp.shizuoka.ac.jp/idp/profile/SAML2/Redirect/SSO?execution=e1s1', data={
        'j_username': GAKUJO_USERNAME, 'j_password': GAKUJO_PASSWORD, '_eventId_proceed': ''})
    if ('ユーザ名またはパスワードが正しくありません。' in login.text):
        return 0
    bs = bs4(login.text, 'html.parser')
    relay_state = html.fromstring(str(bs)).xpath(
        '/html/body/form/div/input[1]/@value')[0]
    saml_response = html.fromstring(str(bs)).xpath(
        '/html/body/form/div/input[2]/@value')[0]
    session.post('https://gakujo.shizuoka.ac.jp/Shibboleth.sso/SAML2/POST', data={
        'RelayState': relay_state, 'SAMLResponse': saml_response}, headers={'Referer': 'https://idp.shizuoka.ac.jp/'})
    session.get('https://gakujo.shizuoka.ac.jp/portal/shibbolethlogin/shibbolethLogin/initLogin/sso',
                headers={'Referer': 'https://idp.shizuoka.ac.jp/'})
    login = session.post('https://gakujo.shizuoka.ac.jp/portal/home/home/initialize',
                         data={'EXCLUDE_SET': ''}, headers={'Referer': 'https://idp.shizuoka.ac.jp/'})
    bs = bs4(login.text, 'html.parser')
    apache = html.fromstring(str(bs)).xpath(
        '/html/body/div[1]/form[1]/div/input/@value')
    end_time = time.perf_counter()
    return end_time - start_time


def add_duration(duration):
    with pg.connect(DATABASE_URL) as connect:
        with connect.cursor() as cursor:
            cursor.execute(
                'INSERT INTO login_logs(duration) VALUES (%s)', (duration,))


def get_recent_durations():
    with pg.connect(DATABASE_URL) as connect:
        with connect.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM login_logs ORDER BY timestamp limit 48')
            return pd.DataFrame(cursor.fetchall())


def plot_durations():
    df = get_recent_durations()
    # df = pd.DataFrame(
    # data={'timestamp': [datetime.datetime(2022, 3, 29, 0, 0, 0), datetime.datetime(2022, 3, 29, 1, 0, 0), datetime.datetime(2022, 3, 29, 2, 0, 0)], 'duration': [11, 9, 12]})
    fig, ax = plt.subplots()
    ax.plot(df['timestamp'], df['duration'], color='#fe923a', linewidth=3)
    fig.set_facecolor('#212529')
    ax.set_facecolor('#343a40')
    ax.tick_params(axis='x', colors='#f8f9fa', size=12)
    ax.tick_params(axis='y', colors='#f8f9fa', size=12)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    plt.ylim(5, 20)
    ax.axhspan(ymin=15, ymax=99, color='#c92a2a', alpha=0.3)
    ax.text(0.99, 0.02, '@ShizudaiDown', horizontalalignment='right',
            transform=ax.transAxes, color='#f8f9fa', size=12)
    fig.savefig('plot.png')


def post_tweet():
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    t = tweepy.API(auth)
    t.update_with_media(status='Hello World from Heroku.', filename='plot.png')


add_duration(calc_duration())
plot_durations()
post_tweet()
