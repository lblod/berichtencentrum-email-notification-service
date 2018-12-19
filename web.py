import os
import schedule
from helpers import log
from .tasks import process_send_notifications

INTERVAL = 5 if os.environ.get('RUN_INTERVAL') is None else os.environ.get('RUN_INTERVAL')

# schedule.every(INTERVAL).minutes.do(process_send_notifications)
log("Registered a task for fetching and processing messages from Kalliope every {} minutes".format(INTERVAL))



################# TEMP: test routes ############################################

import flask
from .queries import construct_needs_mail_query
from .queries import construct_mail_sent_query
from .queries import construct_mail_query
from .mocks import mock_email

ABB_URI = "http://data.lblod.info/id/bestuurseenheden/141d9d6b-54af-4d17-b313-8d1c30bc3f5b"
PUBLIC_GRAPH = "http://mu.semte.ch/graphs/public"
OUTBOX_FOLDER_URI = os.environ.get('OUTBOX_FOLDER_URI') or "http://data.lblod.info/id/mail-folders/2"

@app.route('/needs_mail/')
def needs_mail():
    q = construct_needs_mail_query(PUBLIC_GRAPH, 7)
    return flask.jsonify(helpers.query(q))

@app.route("/mock_insert")
def mock():
    e = mock_email()
    q = construct_mail_query(PUBLIC_GRAPH, e, OUTBOX_FOLDER_URI)
    return flask.jsonify(helpers.update(q))
