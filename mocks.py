#!/usr/bin/python3
from datetime import datetime
from .tasks import new_email

def mock_email():
    return new_email("me@redpencil.io",
                     "you@redpencil.io",
                     "subject @{}.".format(datetime.now().isoformat()),
                     "content @{}.".format(datetime.now().isoformat()))
