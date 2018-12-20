import os
from datetime import datetime
import helpers, escape_helpers
from .queries import construct_needs_mail_query
from .queries import construct_mail_sent_query
from .queries import construct_mail_query

ABB_URI = "http://data.lblod.info/id/bestuurseenheden/141d9d6b-54af-4d17-b313-8d1c30bc3f5b"
PUBLIC_GRAPH = "http://mu.semte.ch/graphs/public"
MAX_AGE = 7 #days
FROM_ADDRESS = "binnenland@vlaanderen.be"

def new_email(email_from, to, subject, content):
    email = {}
    email['uuid'] = helpers.generate_uuid()
    email['from'] = email_from
    email['to'] = to
    email['subject'] = subject
    email['content'] = content
    return email

def process_send_notifications():
    """
    Fetch messages that need a notification to be sent, construct an email message and place it in the correct outbox.

    :returns ?:
    """
    helpers.log("fetching messages that need a notification to be sent ...")
    q = construct_needs_mail_query(PUBLIC_GRAPH, MAX_AGE) #?bericht ?conversatieuuid ?van ?ontvangen ?dossiernummer ?betreft ?mailadres
    berichten = helpers.query(q)['results']['bindings']
    helpers.log("found {} berichten. Processing ...".format(len(berichten)))
    for bericht in berichten:
        subject = "Dossier {}:'{}' - Nieuw bericht".format(bericht['dossiernummer'], bericht['betreft'])
        link = "https://loket.lokaalbestuur.vlaanderen.be/berichten/{}".format(bericht['conversatieuuid'])
        content = "Nieuw bericht: {}".format(link) ## TEMP: stub
        email = new_email(FROM_ADDRESS, bericht['mailadres'], subject, content)
        helpers.log("placing bericht '{}' into outbox".format(subject))
        insert_q = construct_mail_query(PUBLIC_GRAPH, email, os.environ.get('OUTBOX_FOLDER_URI'))
        helpers.update(insert_q)
        # Conditional on above query?
        insert_q2 = construct_mail_sent_query(PUBLIC_GRAPH, bericht['bericht'], "http://data.lblod.info/id/emails/{}".format(email['uuid']))
        helpers.update(insert_q2)
        
