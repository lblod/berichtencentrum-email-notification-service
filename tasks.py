import os
from datetime import datetime
import helpers, escape_helpers
from .queries import construct_needs_mail_query
from .queries import construct_mail_sent_query
from .queries import construct_mail_query
from SPARQLWrapper import SPARQLWrapper, JSON

ABB_URI = "http://data.lblod.info/id/bestuurseenheden/141d9d6b-54af-4d17-b313-8d1c30bc3f5b"
MESSAGE_GRAPH_PATTERN_START = "http://mu.semte.ch/graphs/organizations/"
MESSAGE_GRAPH_PATTERN_END = "/LoketLB-berichtenGebruiker"
SYSTEM_EMAIL_GRAPH = "http://mu.semte.ch/graphs/system/email"
OUTBOX_FOLDER_URI = "http://data.lblod.info/id/mail-folders/2"
MAX_AGE = 60 #days
FROM_ADDRESS = "binnenland@vlaanderen.be"

authClient = SPARQLWrapper(os.environ.get('MU_SPARQL_ENDPOINT'), returnFormat=JSON)
authClient.customHttpHeaders = { "mu-auth-sudo": True }

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
    q = construct_needs_mail_query(MESSAGE_GRAPH_PATTERN_START, MESSAGE_GRAPH_PATTERN_END, MAX_AGE) #?bericht ?conversatieuuid ?van ?ontvangen ?dossiernummer ?betreft ?mailadres
    berichten = helpers.query(q)['results']['bindings']
    helpers.log("found {} berichten. Processing ...".format(len(berichten)))
    for bericht in berichten:
        subject = "Dossier {}:'{}' - Nieuw bericht".format(bericht['dossiernummer']['value'], bericht['betreft']['value'])
        link = "https://loket.lokaalbestuur.vlaanderen.be/berichten/{}".format(bericht['conversatieuuid']['value'])
        content = "Nieuw bericht: {}".format(link) ## TEMP: stub
        email = new_email(FROM_ADDRESS, bericht['mailadres']['value'], subject, content)
        helpers.log("placing bericht '{}' into outbox".format(subject))
        insert_q = construct_mail_query(SYSTEM_EMAIL_GRAPH, email, OUTBOX_FOLDER_URI)
        helpers.update(insert_q)
        # Conditional on above query?
        insert_q2 = construct_mail_sent_query(SYSTEM_EMAIL_GRAPH, bericht['bericht']['value'], "http://data.lblod.info/id/emails/{}".format(email['uuid']))
        helpers.update(insert_q2)

def query(the_query):
    """Execute the given SPARQL query (select/ask/construct)on the tripple store and returns the results
    in the given returnFormat (JSON by default)."""
    log("execute query: \n" + the_query)
    authClient.setQuery(the_query)
    return authClient.query().convert()
