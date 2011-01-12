from django.conf import settings

class GfcMiddleware(object):
    def process_request(self, request):
        if not hasattr(settings, 'GOOGLE_SITE_ID'):
            raise Exception('Please set GOOGLE_SITE_ID in settings.py')

        print request.COOKIES.get('fcauth' + settings.GOOGLE_SITE_ID, False)
