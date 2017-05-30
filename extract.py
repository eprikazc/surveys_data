import configparser
import logging

import requests


config = configparser.ConfigParser()
config.read('config.ini')

if config['DEFAULT'].getboolean('debug'):
    logging.basicConfig(level=logging.DEBUG)


def get_session():
    session = requests.Session()
    res = session.post(
        'https://api.zenloop.com/v1/sessions',
        json={
            'user': {
                'email': config['API']['email'],
                'password': config['API']['password'],
            }
        }
    )
    token = res.json()['session']['jwt']
    session.headers['Authorization'] = 'Bearer: %s' % token
    return session


def get_surveys(session):
    page = 1
    while True:
        response = session.get(
            'https://api.zenloop.com/v1/surveys',
            params={'page': page})
        surveys = response.json().get('surveys')
        if surveys:
            for item in surveys:
                yield item
            page += 1
        else:
            break


def filter_survey(survey):
    surveys_whitelist = config['DEFAULT']['survey_titles'].split('\n')
    return survey['title'] in surveys_whitelist


def run():
    session = get_session()
    for survey in get_surveys(session):
        if filter_survey(survey):
            print(survey)


if __name__ == '__main__':
    run()
