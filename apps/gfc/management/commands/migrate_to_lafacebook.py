from django.core.management.base import BaseCommand, CommandError
from socialregistration.models import FacebookProfile
from la_facebook.models import UserAssociation

class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        for social_profile in FacebookProfile.objects.all():
            try:
                u = UserAssociation.objects.get(identifier=social_profile.uid)
                u.user = social_profile.user
                u.save()
            except UserAssociation.DoesNotExist:
                UserAssociation.objects.get_or_create(
                    user=social_profile.user,
                    identifier=social_profile.uid
                )
