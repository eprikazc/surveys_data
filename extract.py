import logging

import requests

from datetime import datetime, timedelta

from config import config
from models import Answer, Survey, Session

URLS = {
    'login': 'https://api.zenloop.com/v1/sessions',
    'surveys': 'https://api.zenloop.com/v1/surveys',
    'answers': 'https://api.zenloop.com/v1/surveys/%s/answers',
}

if config['DEFAULT'].getboolean('debug'):
    logging.basicConfig(level=logging.DEBUG)


def get_requests_session():
    session = requests.Session()
    res = session.post(
        URLS['login'],
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


def paginate(session, url, items_getter, params=None):
    params = params or {}
    page = 1
    while True:
        params['page'] = page
        response = session.get(
            url,
            params=params)
        items = items_getter(response)
        if items:
            for item in items:
                yield item
            page += 1
        else:
            break


def get_surveys(session):
    return paginate(
        session,
        URLS['surveys'],
        lambda response: response.json().get('surveys'))


def filter_survey(survey):
    surveys_whitelist = config['DEFAULT'].get('survey_titles')
    if not surveys_whitelist:
        return True
    surveys_whitelist = surveys_whitelist.split('\n')
    return survey['title'] in surveys_whitelist


def store_surveys_to_db(db_session, requests_session):
    surveys_by_hash_id = {
        obj.public_hash_id: obj
        for obj in db_session.query(Survey).all()
    }
    res = []
    for survey in get_surveys(requests_session):
        if not filter_survey(survey):
            continue
        res.append(survey['public_hash_id'])
        survey_obj = surveys_by_hash_id.get(survey['public_hash_id'])
        if survey_obj:
            survey_obj.title = survey['title']
            survey_obj.status = survey['status']
            db_session.commit()
        else:
            db_session.add(Survey(
                title=survey['title'],
                public_hash_id=survey['public_hash_id'],
                status=survey['status'],
            ))
            db_session.commit()
    return res


def store_answers(db_session, requests_session, survey_ids=None):
    query = db_session.query(Survey)
    if survey_ids:
        query = query.filter(Survey.public_hash_id.in_(survey_ids))
    for survey in query:
        response = requests_session.get(
            URLS['answers'] % survey.public_hash_id)
        data = response.json()
        survey.nps = data['survey']['nps']['percentage']
        db_session.commit()

        db_query = db_session.query(Answer).filter(survey == survey)
        request_params = {}
        if not config['DEFAULT'].getboolean('all_time'):
            yesterday = datetime.now() - timedelta(days=1)
            db_query = db_query.filter(Answer.inserted_at > yesterday)
            request_params = {'date_shortcut': 'today'}
        existing_answers = [
            obj
            for obj in db_query
        ]
        for answer in paginate(
                requests_session,
                URLS['answers'] % survey.public_hash_id,
                lambda response: response.json().get('answers'),
                request_params,
                ):
            exists = bool([
                obj
                for obj in existing_answers
                if (
                    obj.score == answer['score'] and
                    obj.comment == answer['comment'] and
                    obj.inserted_at_str == answer['inserted_at'])
                ])
            if exists:
                continue
            db_session.add(Answer(
                survey=survey,
                recipient_id=answer['recipient_id'],
                score=answer['score'],
                comment=answer['comment'],
                inserted_at=answer['inserted_at'],
                inserted_at_str=answer['inserted_at'],
            ))
            db_session.commit()


def run():
    db_session = Session()
    requests_session = get_requests_session()
    survey_ids = store_surveys_to_db(db_session, requests_session)
    store_answers(db_session, requests_session, survey_ids)


if __name__ == '__main__':
    run()
