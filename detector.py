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
from decimal import Decimal, ROUND_HALF_UP

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
                'insert into login_logs(duration, timestamp) values (%s, %s)', (duration, datetime.datetime.now()))


def get_recent_durations():
    with pg.connect(DATABASE_URL) as connect:
        with connect.cursor() as cursor:
            cursor.execute(
                'select * from (select * from login_logs order by timestamp desc limit 48) as x order by timestamp')
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


def plot_durations(filename):
    df = get_recent_durations()
    # df = pd.DataFrame(data={'timestamp': [datetime.datetime(2022, 3, 29, 0, 0, 0), datetime.datetime(2022, 3, 29, 0, 30, 0), datetime.datetime(2022, 3, 29, 1, 0, 0), datetime.datetime(2022, 3, 29, 1, 30, 0), datetime.datetime(2022, 3, 29, 2, 0, 0), datetime.datetime(2022, 3, 29, 2, 30, 0), datetime.datetime(2022, 3, 29, 3, 0, 0), datetime.datetime(2022, 3, 29, 3, 30, 0), datetime.datetime(2022, 3, 29, 4, 0, 0), datetime.datetime(2022, 3, 29, 4, 30, 0), datetime.datetime(2022, 3, 29, 5, 0, 0), datetime.datetime(2022, 3, 29, 5, 30, 0), datetime.datetime(2022, 3, 29, 6, 0, 0), datetime.datetime(2022, 3, 29, 6, 30, 0), datetime.datetime(2022, 3, 29, 7, 0, 0), datetime.datetime(2022, 3, 29, 7, 30, 0), datetime.datetime(2022, 3, 29, 8, 0, 0), datetime.datetime(2022, 3, 29, 8, 30, 0), datetime.datetime(2022, 3, 29, 9, 0, 0), datetime.datetime(2022, 3, 29, 9, 30, 0), datetime.datetime(2022, 3, 29, 10, 0, 0), datetime.datetime(2022, 3, 29, 10, 30, 0), datetime.datetime(2022, 3, 29, 11, 0, 0), datetime.datetime(2022, 3, 29, 11, 30, 0), datetime.datetime(2022, 3, 29, 12, 0, 0), datetime.datetime(2022, 3, 29, 12, 30, 0), datetime.datetime(
    # 2022, 3, 29, 13, 0, 0), datetime.datetime(2022, 3, 29, 13, 30, 0), datetime.datetime(2022, 3, 29, 14, 0, 0), datetime.datetime(2022, 3, 29, 14, 30, 0), datetime.datetime(2022, 3, 29, 15, 0, 0), datetime.datetime(2022, 3, 29, 15, 30, 0), datetime.datetime(2022, 3, 29, 16, 0, 0), datetime.datetime(2022, 3, 29, 16, 30, 0), datetime.datetime(2022, 3, 29, 17, 0, 0), datetime.datetime(2022, 3, 29, 17, 30, 0), datetime.datetime(2022, 3, 29, 18, 0, 0), datetime.datetime(2022, 3, 29, 18, 30, 0), datetime.datetime(2022, 3, 29, 19, 0, 0), datetime.datetime(2022, 3, 29, 19, 30, 0), datetime.datetime(2022, 3, 29, 20, 0, 0), datetime.datetime(2022, 3, 29, 20, 30, 0), datetime.datetime(2022, 3, 29, 21, 0, 0), datetime.datetime(2022, 3, 29, 21, 30, 0), datetime.datetime(2022, 3, 29, 22, 0, 0), datetime.datetime(2022, 3, 29, 22, 30, 0), datetime.datetime(2022, 3, 29, 23, 0, 0), datetime.datetime(2022, 3, 29, 23, 30, 0)], 'duration': [11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12, 11, 9, 12]})
    fig, ax = plt.subplots(figsize=(16, 9), dpi=120)
    ax.plot(df['timestamp'], df['duration'], color='#fe923a', linewidth=6)
    fig.set_facecolor('#212529')
    ax.set_facecolor('#343a40')
    ax.tick_params(axis='x', colors='#f8f9fa', labelsize=32)
    ax.tick_params(axis='y', colors='#f8f9fa', labelsize=32)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    ax.set_ylim(5, 20)
    ax.axhspan(ymin=15, ymax=21, color='#c92a2a', alpha=0.3)
    ax.text(0.98, 0.98, df[-1:]['timestamp'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S'), va='top', ha='right',
            transform=ax.transAxes, color='#f8f9fa', size=36)
    ax.text(0.98, 0.02, '@ShizudaiDown', horizontalalignment='right',
            transform=ax.transAxes, color='#f8f9fa', size=36)
    ax.set_title('Shizudai Downdetector',
                 loc='center', color='#f8f9fa', size=54, pad=24)
    fig.savefig('plot.png')
    return df[-1:]['timestamp'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S')


def post_tweet(timestamp, duration, filename):
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    t = tweepy.API(auth)
    status = '学務情報システムのログイン処理は{}秒です'.format(str(
        Decimal(duration).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)))
    if duration >= 15:
        status += '\r\n通常よりログイン処理に時間が掛かっています'
    status += '\r\n{}'.format(timestamp)
    t.update_status_with_media(
        status=status, filename=filename)


if 3 <= datetime.datetime.now().hour < 5:
    exit()
duration = calc_duration()
add_duration(duration)
timestamp = plot_durations('plot.png')
# if (23 <= datetime.datetime.now().hour or datetime.datetime.now().hour < 9) and duration < 15:
#     exit()
if duration < 15:
    exit()
post_tweet(timestamp, duration, 'plot.png')
