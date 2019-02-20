import os
from datetime import datetime
import helpers, escape_helpers
from .sudo_query_helpers import query, update
from .queries import construct_needs_mail_query
from .queries import construct_mail_sent_query
from .queries import construct_mail_query
from pybars import Compiler

ABB_URI = "http://data.lblod.info/id/bestuurseenheden/141d9d6b-54af-4d17-b313-8d1c30bc3f5b"
PUBLIC_GRAPH = "http://mu.semte.ch/graphs/public"
MESSAGE_GRAPH_PATTERN_START = "http://mu.semte.ch/graphs/organizations/"
MESSAGE_GRAPH_PATTERN_END = "/LoketLB-berichtenGebruiker"
SYSTEM_EMAIL_GRAPH = "http://mu.semte.ch/graphs/system/email"
OUTBOX_FOLDER_URI = os.environ.get('OUTBOX_FOLDER_URI')
MAX_AGE = int(os.environ.get('MAX_MESSAGE_AGE')) #days
FROM_EMAIL_ADDRESS = os.environ.get('FROM_EMAIL_ADDRESS')
LOKET_APP_BASEURL = os.environ.get('LOKET_APP_BASEURL')

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
    q = construct_needs_mail_query(MESSAGE_GRAPH_PATTERN_START, MESSAGE_GRAPH_PATTERN_END, PUBLIC_GRAPH, MAX_AGE) #?bericht ?conversatieuuid ?van ?ontvangen ?dossiernummer ?betreft ?mailadres
    berichten = query(q)['results']['bindings']
    helpers.log("found {} berichten. Processing ...".format(len(berichten)))
    if berichten: # Prepare email template
        here = os.path.dirname(os.path.realpath(__file__))
        templatepath = os.path.join(here, 'templates/nieuw_bericht.hbs')
        with open(templatepath, 'r') as email_template_file:
            compiler = Compiler()
            precompiled = compiler.precompile(email_template_file.read())
            email_html_template = compiler.template(precompiled)
    for bericht in berichten:
        subject = "Dossier {}:'{}' - Nieuw bericht".format(bericht['dossiernummer']['value'], bericht['betreft']['value'])
        link = "{}/berichtencentrum/berichten/{}".format(LOKET_APP_BASEURL.strip('/'), bericht['conversatieuuid']['value'])
        content = None # NOTE: Not used, we use html_content
        email = new_email(FROM_EMAIL_ADDRESS, bericht['mailadres']['value'], subject, content)
        email['html_content'] = email_html_template({'link': link, 'bestuurseenheid-naam': bericht['bestuurseenheidnaam']['value']})
        email['uri'] = "http://data.lblod.info/id/emails/{}".format(email['uuid'])
        helpers.log("placing bericht '{}' into outbox".format(subject))
        insert_q = construct_mail_query(SYSTEM_EMAIL_GRAPH, email, OUTBOX_FOLDER_URI)
        # helpers.log(insert_q)
        update(insert_q)
        # Conditional on above query?
        bestuurseenheid_uuid = bericht['naar']['value'].split('/')[-1] # NOTE: Add graph as argument to query because Virtuoso
        bestuurseenheid_graph = "http://mu.semte.ch/graphs/organizations/{}/LoketLB-berichtenGebruiker".format(bestuurseenheid_uuid)
        insert_q2 = construct_mail_sent_query(SYSTEM_EMAIL_GRAPH, bestuurseenheid_graph, bericht['bericht']['value'], email['uuid'])
        # helpers.log(insert_q2)
        update(insert_q2)
