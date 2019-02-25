import os
from apscheduler.schedulers.background import BackgroundScheduler
from helpers import log
from .tasks import process_send_notifications

INTERVAL = 5 if os.environ.get('RUN_INTERVAL') is None else int(os.environ.get('RUN_INTERVAL'))

scheduler = BackgroundScheduler()
scheduler.add_job(func=process_send_notifications, trigger="interval", minutes=INTERVAL)
log("Registered a task for fetching and processing messages from Kalliope every {} minutes".format(INTERVAL))
scheduler.start()



################# TEMP: test routes ############################################

import flask
from .queries import construct_needs_mail_query
from .queries import construct_mail_sent_query
from .queries import construct_mail_query
from .mocks import mock_email

ABB_URI = "http://data.lblod.info/id/bestuurseenheden/141d9d6b-54af-4d17-b313-8d1c30bc3f5b"
MESSAGE_GRAPH_PATTERN_START = "http://mu.semte.ch/graphs/organizations/"
MESSAGE_GRAPH_PATTERN_END = "/LoketLB-berichtenGebruiker"
MAX_AGE = 3 if int(os.environ.get('MAX_MESSAGE_AGE')) is None else int(os.environ.get('MAX_MESSAGE_AGE')) #days
SYSTEM_EMAIL_GRAPH = "http://mu.semte.ch/graphs/system/email"
OUTBOX_FOLDER_URI = os.environ.get('OUTBOX_FOLDER_URI') or "http://data.lblod.info/id/mail-folders/2"

@app.route('/needs_mail/')
def needs_mail():
    q = construct_needs_mail_query(MESSAGE_GRAPH_PATTERN_START, MESSAGE_GRAPH_PATTERN_END, MAX_AGE)
    return flask.jsonify(helpers.query(q))

@app.route("/mock_insert")
def mock():
    e = mock_email()
    q = construct_mail_query(SYSTEM_EMAIL_GRAPH, e, OUTBOX_FOLDER_URI)
    return flask.jsonify(helpers.update(q))
