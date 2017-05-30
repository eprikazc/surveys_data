import logging

import requests

from config import config
from models import Survey, Session


if config['DEFAULT'].getboolean('debug'):
    logging.basicConfig(level=logging.DEBUG)


def get_requests_session():
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


def store_surveys_to_db(db_session, requests_session):
    existing_hash_ids = [
        obj.public_hash_id
        for obj in db_session.query(Survey).all()
    ]
    for survey in get_surveys(requests_session):
        if not filter_survey(survey):
            continue
        if survey['public_hash_id'] not in existing_hash_ids:
            db_session.add(Survey(
                title=survey['title'],
                public_hash_id=survey['public_hash_id'],
                status=survey['status'],
            ))
            db_session.commit()


def run():
    db_session = Session()
    requests_session = get_requests_session()
    store_surveys_to_db(db_session, requests_session)


if __name__ == '__main__':
    run()
