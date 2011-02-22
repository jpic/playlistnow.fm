from django.template import Library
from views import group_activities as upstream_group_activities

register = Library()

@register.filter
def group_activities(activities):
    return upstream_group_activities(activities)
