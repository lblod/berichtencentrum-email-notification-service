#!/usr/bin/python3
from datetime import datetime
from .tasks import new_email


def mock_email():
    e = new_email("me@redpencil.io",
                  "you@redpencil.io",
                  "subject @{}.".format(datetime.now().isoformat()),
                  "content @{}.".format(datetime.now().isoformat()))
    e['uri'] = "http://data.lblod.info/id/emails/{}".format(e['uuid'])
    e['bcc'] = "blindcc@redpencil.io"
    return e
