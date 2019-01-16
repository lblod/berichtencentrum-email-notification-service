from datetime import datetime, timedelta

def construct_needs_mail_query(message_graph_pattern_start, message_graph_pattern_end, max_bericht_age=7):
    """
    Construct a query for retrieving all berichten that require a mail notification to be sent for.

    :param max_bericht_age: int, specifies how old a message (in days) can maximally be.
        In case the messages are older they are not considered, as the emails that were sent for them may be already deleted again for example.
    """
    oldest = datetime.now() - timedelta(days=max_bericht_age)
    oldest = oldest.isoformat()
    q = """
    PREFIX schema: <http://schema.org/>
    PREFIX besluit: <http://data.vlaanderen.be/ns/besluit#>
    PREFIX nmo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nmo#>
    PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>

    SELECT ?bericht ?van ?ontvangen ?dossiernummer ?conversatieuuid ?betreft ?mailadres
    WHERE {{
        GRAPH ?h {{
            ?naar a besluit:Bestuurseenheid;
                ext:wilMailOntvangen "true";
                ext:mailAdresVoorNotificaties ?mailadres.
        }}
        GRAPH ?g {{
            ?bericht a schema:Message;
                schema:dateReceived ?ontvangen;
                schema:text ?inhoud;
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
            FILTER (?ontvangen > "{2}"^^xsd:dateTime)
        }}
        FILTER(STRSTARTS(STR(?g), "{0}"))
        FILTER(STRENDS(STR(?g), "{1}"))
    }}
    """.format(message_graph_pattern_start, message_graph_pattern_end, oldest)
    return q

def construct_mail_sent_query(graph_uri, bericht_uri, email_uuid):
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
        GRAPH ?g {{
            <{1}> ext:notificatieEmail ?email. # TODO: predicate?
        }}
    }}
    WHERE {{
        GRAPH <{0}> {{
            ?email a nmo:Email.
            ?email <http://mu.semte.ch/vocabularies/core/uuid> "{2}".
        }}
        GRAPH ?g {{
            <{1}> a schema:Message.
        }}
        FILTER(STRSTARTS(STR(?g), "http://mu.semte.ch/graphs/organizations/"))
        FILTER(STRENDS(STR(?g), "/LoketLB-berichtenGebruiker"))
    }}
    """.format(graph_uri, bericht_uri, email_uuid)
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
                nmo:messageFrom "{1[from]}";
                nmo:emailTo "{1[to]}";
                nmo:messageSubject "{1[subject]}";
    """
    if 'html_content' in email:
        q += """nmo:htmlMessageContent "{1[html_content]}";"""
    else: #then at least plain text content should exist
        q += """nmo:plainTextMessageContent "{1[content]}";"""
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
