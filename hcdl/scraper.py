import logging
import os
import requests
import urllib.parse

from bs4 import BeautifulSoup as BS
from pprint import pprint as pp

def ppsoup(soup):
    print(soup.prettify())

def get_soup(text):
    return BS(text, 'lxml')

def urljoin(*args):
    return urllib.parse.urljoin(*args)

class LoginForm(object):

    PASSWORD_KEY = 'j_password'
    USERNAME_KEY = 'j_username'

    def __init__(self, soup):
        self.action = soup['action']
        self.data = { input['name']:input.get('value') for input in soup('input') }

    @property
    def password(self):
        return self.data[self.PASSWORD_KEY]

    @password.setter
    def password(self, value):
        self.data[self.PASSWORD_KEY] = value

    @property
    def username(self):
        return self.data[self.USERNAME_KEY]

    @username.setter
    def username(self, value):
        self.data[self.USERNAME_KEY] = value


class Scraper(object):

    ROOT = 'https://ohio.ent.sirsi.net'
    LOGIN_FORM_URL = '/client/en_US/hhi/search/patronlogin/$N'
    ACCOUNT_URL = '/client/en_US/hhi/search/account'

    def __init__(self):
        self.session = requests.Session()

        self.logged_in = False

        self.logger = logging.getLogger(self.__class__.__name__)

        self.endpoints = dict(login=urljoin(self.ROOT, self.LOGIN_FORM_URL),
                              account=urljoin(self.ROOT, self.ACCOUNT_URL))

    def url_for(self, name):
        return self.endpoints[name]

    def download(self, name):
        url = self.url_for(name)
        #self.logger.info(url)
        rv = self.session.get(url)
        return get_soup(rv.text)

    def download_login_form(self):
        soup = self.download('login')
        form_soup = soup.find(id='loginPageForm')
        return LoginForm(form_soup)

    def login(self, username, password):
        form = self.download_login_form()
        form.username = username
        form.password = password
        rv = self.session.post(urljoin(self.ROOT, form.action), form.data)
        soup = get_soup(rv.text)
        self.logged_in = 'Logging in...' in soup.title.text
        return self.logged_in

    def download_account(self):
        soup = self.download('account')
        return soup

    def test(self, f, urlpart, *args):
        url = urljoin(self.ROOT, urlpart)
        rv = f(url, *args)
        return get_soup(rv.text)

    def test_get(self, urlpart):
        return self.test(self.session.get, urlpart)

    def test_post(self, urlpart, data):
        return self.test(self.session.post, urlpart)


def main():
    logging.basicConfig(level=logging.DEBUG)

    try:
        username = os.environ['HCDL_USERNAME']
        password = os.environ['HCDL_PASSWORD']
    except KeyError:
        print('\nError:\n\tUsername and password environment variables not'
              ' found. Please `source hcdlinit` first.')
        return

    scraper = Scraper()
    success = scraper.login(username, password)

    if not success:
        raise RuntimeError('Login failed')

    soup = scraper.download_account()
    soup.find('form', id=lambda x: x.startswith('HoldsSelectionForm'))
    ppsoup(soup)


    #soup = scraper.test_post(
    #    '/client/en_US/hhi/search/account.holds.libraryholdsaccordion?',
    #    {'t:zoneid': 'libraryHoldsAccordion'})
    #ppsoup(soup)

if __name__ == '__main__':
    main()
