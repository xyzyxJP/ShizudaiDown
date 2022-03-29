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
                'INSERT INTO login_logs(duration, timestamp) VALUES (%s, %s)', (duration, datetime.datetime.now()))


def get_recent_durations():
    with pg.connect(DATABASE_URL) as connect:
        with connect.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM login_logs ORDER BY timestamp limit 48')
            column_list = [d.name for d in cursor.description]
            df = pd.DataFrame(cursor.fetchall(), columns=column_list)
            dtype_dict = {}
            for d in cursor.description:
                if d.type_code == 1700:
                    dtype_dict[d.name] = 'float64'
                if d.type_code == 1082:
                    dtype_dict[d.name] = 'datetime64'
            if len(dtype_dict) > 0:
                df = df.astype(dtype_dict)
            return df


def plot_durations():
    df = get_recent_durations()
    # df = pd.DataFrame(data={'timestamp': [datetime.datetime(2022, 3, 29, 0, 0, 0), datetime.datetime(2022, 3, 29, 0, 30, 0), datetime.datetime(2022, 3, 29, 1, 0, 0), datetime.datetime(2022, 3, 29, 1, 30, 0), datetime.datetime(2022, 3, 29, 2, 0, 0), datetime.datetime(2022, 3, 29, 2, 30, 0), datetime.datetime(2022, 3, 29, 3, 0, 0), datetime.datetime(2022, 3, 29, 3, 30, 0), datetime.datetime(2022, 3, 29, 4, 0, 0), datetime.datetime(2022, 3, 29, 4, 30, 0), datetime.datetime(2022, 3, 29, 5, 0, 0), datetime.datetime(2022, 3, 29, 5, 30, 0), datetime.datetime(2022, 3, 29, 6, 0, 0), datetime.datetime(2022, 3, 29, 6, 30, 0), datetime.datetime(2022, 3, 29, 7, 0, 0), datetime.datetime(2022, 3, 29, 7, 30, 0), datetime.datetime(2022, 3, 29, 8, 0, 0), datetime.datetime(2022, 3, 29, 8, 30, 0), datetime.datetime(2022, 3, 29, 9, 0, 0), datetime.datetime(2022, 3, 29, 9, 30, 0), datetime.datetime(2022, 3, 29, 10, 0, 0), datetime.datetime(2022, 3, 29, 10, 30, 0), datetime.datetime(2022, 3, 29, 11, 0, 0), datetime.datetime(2022, 3, 29, 11, 30, 0), datetime.datetime(2022, 3, 29, 12, 0, 0), datetime.datetime(2022, 3, 29, 12, 30, 0), datetime.datetime(2022, 3, 29, 13, 0, 0), datetime.datetime(2022, 3, 29, 13, 30, 0), datetime.datetime(2022, 3, 29, 14, 0, 0), datetime.datetime(2022, 3, 29, 14, 30, 0), datetime.datetime(2022, 3, 29, 15, 0, 0), datetime.datetime(2022, 3, 29, 15, 30, 0), datetime.datetime(2022, 3, 29, 16, 0, 0), datetime.datetime(2022, 3, 29, 16, 30, 0), datetime.datetime(2022, 3, 29, 17, 0, 0), datetime.datetime(2022, 3, 29, 17, 30, 0), datetime.datetime(2022, 3, 29, 18, 0, 0), datetime.datetime(2022, 3, 29, 18, 30, 0), datetime.datetime(2022, 3, 29, 19, 0, 0), datetime.datetime(2022, 3, 29, 19, 30, 0), datetime.datetime(2022, 3, 29, 20, 0, 0), datetime.datetime(2022, 3, 29, 20, 30, 0), datetime.datetime(2022, 3, 29, 21, 0, 0), datetime.datetime(2022, 3, 29, 21, 30, 0), datetime.datetime(2022, 3, 29, 22, 0, 0), datetime.datetime(2022, 3, 29, 22, 30, 0), datetime.datetime(2022, 3, 29, 23, 0, 0), datetime.datetime(2022, 3, 29, 23, 30, 0)],
    # 'duration': [11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12]})
    fig = plt.figure(figsize=(16, 9), dpi=120)
    ax = plt.gca()
    ax.plot(df['timestamp'], df['duration'], color='#fe923a', linewidth=3)
    fig.set_facecolor('#212529')
    ax.set_facecolor('#343a40')
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    ax.tick_params(axis='x', colors='#f8f9fa', size=12)
    ax.tick_params(axis='y', colors='#f8f9fa', size=12)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    plt.ylim(5, 20)
    ax.axhspan(ymin=15, ymax=99, color='#c92a2a', alpha=0.3)
    print(df[-1:]['timestamp'])
    ax.text(0.99, 0.99, df[-1:]['timestamp'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S'), va='top', ha='right',
            transform=ax.transAxes, color='#f8f9fa', size=16)
    ax.text(0.99, 0.02, '@ShizudaiDown', horizontalalignment='right',
            transform=ax.transAxes, color='#f8f9fa', size=16)
    fig.savefig('plot.png')
    return df[-1:]['timestamp'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S')


def post_tweet(timestamp):
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    t = tweepy.API(auth)
    t.update_status_with_media(
        status='ShizudaiDown {}'.format(timestamp), filename='plot.png')


if 3 <= datetime.datetime.now().hour < 5:
    exit()
add_duration(calc_duration())
post_tweet(plot_durations())
