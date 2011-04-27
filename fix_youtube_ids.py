from django.core.management import setup_environ
import settings

setup_environ(settings)

import time
from django.db import IntegrityError
from music.models import Track

total = Track.objects.filter(youtube_id__isnull=True).count()
for t in Track.objects.filter(youtube_id__isnull=True):
    for id in t.youtube_ids:
        t.youtube_id = id
        try:
            t.save()
        except IntegrityError as e:
            print "FAILED FOR TRACK", t.pk
        break

    total -= 1
    print total
    time.sleep(2)
