import json
import requests

from flask import Flask
from flask_slack import Slack

import config
from goattower import db, engine, init
from goattower.models import Actor, User


app = Flask(__name__)
slack = Slack(app)
app.add_url_rule('/', view_func=slack.dispatch)


def create_user(name):
    actor = Actor(name=name)
    actor.parent_id = 1
    db.session.add(actor)
    db.session.commit()
    user = User(name=name)
    user.actor_id = actor.id
    db.session.add(user)
    db.session.commit()
    return user


def do_goat_things(name, command):
    user = db.session.query(User).filter(User.name == name).first()
    if not user:
        user = create_user(name)

    engine.handle_text(user.actor.id, command)

    return '\n'.join(engine.get_text(user.actor.id))


@slack.command('goat', token=config.SLACK_TOKEN, team_id=config.SLACK_TEAM_ID, methods=['POST'])
def random_photo(**kwargs):
    try:
        post_url = config.SLACK_POST_URL
        name = kwargs['user_name']
        command = kwargs['text']

        print '{} did "{}"'.format(name, command)

        lines = do_goat_things(name, command)

        payload = {
            'text': lines,
            'channel': '@' + name
        }
        req = requests.post(post_url, data={'payload': json.dumps(payload)})
        if req.status_code != 200:
            return slack.response('Error: {}'.format(req.content))

        return slack.response('')
    except Exception as e:
        return slack.response(str(e))


if __name__ == '__main__':
    init()
    app.run(host='0.0.0.0', port=9998, debug=True)
