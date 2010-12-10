from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from admin_tools.menu import items, Menu

# to activate your custom menu add the following to your settings.py:
#
# ADMIN_TOOLS_MENU = 'main.menu.CustomMenu'

class CustomMenu(Menu):
    """
    Custom Menu for main admin site.
    """
    def __init__(self, **kwargs):
        Menu.__init__(self, **kwargs)
        self.children.append(items.MenuItem(
            title=_('Dashboard'),
            url=reverse('admin:index')
        ))
        self.children.append(items.AppList(
            title=_('PlaylistNow'),
            include_list=(
                'music',
                'playlist',
            )
        ))
        self.children.append(items.AppList(
            title=_('Applications'),
            exclude_list=(
                'django.contrib', 
                'pinax.apps',
                'music', 
                'playlist',
                'emailconfirmation',
                'mailer',
            )
        ))
        self.children.append(items.AppList(
            title=_('Administration'),
            include_list=(
                'django.contrib',
                'pinax.apps',
                'emailconfirmation',
                'mailer',
            )
        ))

    def init_with_context(self, context):
        """
        Use this method if you need to access the request context.
        """
        pass
