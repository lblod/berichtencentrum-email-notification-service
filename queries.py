from datetime import datetime, timedelta
from pytz import timezone
import copy
import escape_helpers

TIMEZONE = timezone('Europe/Brussels')


def construct_needs_mail_query(message_graph_pattern_start, message_graph_pattern_end, bestuurseenheid_graph,
                               max_bericht_age=7):
    """
    Construct a query for retrieving all berichten that require a mail notification to be sent for.

    :param max_bericht_age: int, specifies how old a message (in days) can maximally be.
        In case the messages are older they are not considered, as the emails that were sent for them may be already deleted again for example.
    """
    oldest = datetime.now(tz=TIMEZONE) - timedelta(days=max_bericht_age)
    oldest = oldest.replace(microsecond=0).isoformat()
    bestuurseenheid_graph = escape_helpers.sparql_escape_uri(bestuurseenheid_graph)
    q = """
    PREFIX schema: <http://schema.org/>
    PREFIX besluit: <http://data.vlaanderen.be/ns/besluit#>
    PREFIX nmo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nmo#>
    PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    
    SELECT ?bericht ?van ?naar ?bestuurseenheidnaam ?ontvangen ?dossiernummer ?conversatieuuid ?betreft ?mailadres
    WHERE {{
        GRAPH ?i {{
            ?naar a besluit:Bestuurseenheid;
                skos:prefLabel ?naam;
                besluit:classificatie/skos:prefLabel ?label.
        }}
        GRAPH ?h {{
            ?naar ext:wilMailOntvangen "true"^^<http://mu.semte.ch/vocabularies/typed-literals/boolean>;
                ext:mailAdresVoorNotificaties ?mailadres.
        }}
        GRAPH ?g {{
            ?bericht a schema:Message;
                schema:dateReceived ?ontvangen;
                schema:sender ?van;
                schema:recipient ?naar.

            ?conversatie a schema:Conversation;
                <http://mu.semte.ch/vocabularies/core/uuid> ?conversatieuuid;
                schema:identifier ?dossiernummer;
                schema:about ?betreft;
                #<http://purl.org/dc/terms/type> ?typecommunicatie;
                #schema:processingTime ?reactietermijn;
                schema:hasPart ?bericht.

            FILTER NOT EXISTS {{ ?bericht ext:notificatieEmail ?email. }}  # TODO: predicate?
            FILTER (?ontvangen > "{3}"^^xsd:dateTime)
        }}
        FILTER(STRSTARTS(STR(?g), "{0}"))
        FILTER(STRENDS(STR(?g), "{1}"))
        BIND(CONCAT(?label, " ", ?naam) as ?bestuurseenheidnaam)
    }}
    """.format(message_graph_pattern_start, message_graph_pattern_end, bestuurseenheid_graph, oldest)
    return q


def construct_mail_sent_query(graph_uri, bestuurseenheid_graph_uri, bericht_uri, email_uuid):
    """
    Construct a query for marking that a mail notification for a bericht has been sent.

    :param graph_uri: string
    :param bericht_uri: string
    :param email_uri: string
    :returns: string containing SPARQL query
    """
    q = """
    PREFIX schema: <http://schema.org/>
    PREFIX nmo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nmo#>
    PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>

    INSERT {{
        GRAPH <{1}> {{
            <{2}> ext:notificatieEmail ?email. # TODO: predicate?
        }}
    }}
    WHERE {{
        GRAPH <{0}> {{
            ?email a nmo:Email.
            ?email <http://mu.semte.ch/vocabularies/core/uuid> "{3}".
        }}
        GRAPH <{1}> {{
            <{2}> a schema:Message.
        }}
    }}
    """.format(graph_uri, bestuurseenheid_graph_uri, bericht_uri, email_uuid)
    return q


def construct_mail_query(graph_uri, email, outbox_folder_uri):
    """
    Construct a query for creating a new email and linking it to the right outbox. This way the mail will be
    picked up by the mail sending service and delivered.

    :param graph_uri: string
    :param email: dict containing properties of the email to create
    :param outbox_folder_uri: string
    :returns: string containing SPARQL query 
    """
    email = copy.deepcopy(email)  # For not modifying the pass-by-name original
    email['from'] = escape_helpers.sparql_escape_string(email['from'])
    email['to'] = escape_helpers.sparql_escape_string(email['to'])
    email['subject'] = escape_helpers.sparql_escape_string(email['subject'])
    if 'html_content' in email:
        email['html_content'] = escape_helpers.sparql_escape_string(email['html_content'])
    else:  # then at least plain text content should exist
        email['content'] = escape_helpers.sparql_escape_string(email['content'])

    q = """
    PREFIX schema: <http://schema.org/>
    PREFIX nmo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nmo#>
    PREFIX nfo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#>
    PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>
    PREFIX email: <http://mu.semte.ch/vocabularies/ext/email/>

    INSERT {{
        GRAPH <{0}> {{
            <{1[uri]}> a nmo:Email;
                <http://mu.semte.ch/vocabularies/core/uuid> "{1[uuid]}";
                nmo:messageFrom {1[from]};
                nmo:emailTo {1[to]};
                nmo:messageSubject {1[subject]};
    """
    if 'bcc' in email:
        email['bcc'] = escape_helpers.sparql_escape_string(email['bcc'])
        q += """
        nmo:emailBcc {1[bcc]};
        """
    if 'html_content' in email:
        q += """nmo:htmlMessageContent {1[html_content]};"""
    else:  # then at least plain text content should exist
        q += """nmo:plainTextMessageContent {1[content]};"""
    q += """
                nmo:isPartOf <{2}>.
            <{2}> email:hasEmail <{1[uri]}>.
        }}
    }}
    WHERE {{
        GRAPH <{0}> {{
            <{2}> a nfo:Folder.
        }}
    }}
    """
    q = q.format(graph_uri, email, outbox_folder_uri)
    return q
