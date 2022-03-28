from bs4 import BeautifulSoup
from lxml import html
import os
import psycopg2
from psycopg2 import extras
import requests
import time

session = requests.session()
USERNAME = os.environ.get('GAKUJO_USERNAME')
PASSWORD = os.environ.get('GAKUJO_PASSWORD')
apache = None

DATABASE_URL = os.environ.get('DATABASE_URL')


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
        'j_username': USERNAME, 'j_password': PASSWORD, '_eventId_proceed': ''})
    if ('ユーザ名またはパスワードが正しくありません。' in login.text):
        return 0
    bs = BeautifulSoup(login.text, 'html.parser')
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
    bs = BeautifulSoup(login.text, 'html.parser')
    apache = html.fromstring(str(bs)).xpath(
        '/html/body/div[1]/form[1]/div/input/@value')
    end_time = time.perf_counter()
    return end_time - start_time


def add_duration(duration):
    with psycopg2.connect(DATABASE_URL) as connect:
        with connect.cursor() as cursor:
            cursor.execute(
                "INSERT INTO login_logs(duration) VALUES (%s)", duration)


def get_recent_durations():
    with psycopg2.connect(DATABASE_URL) as connect:
        with connect.cursor(psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM login_logs ORDER BY timestamp limit 10")
            return cursor.fetchall()


add_duration(calc_duration())
