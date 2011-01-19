import opensocial

from django.conf import settings

def my_opensocial_container(request):
    st = request.COOKIES.get('fcauth' + settings.GOOGLE_SITE_ID, False)
    if st is None:
        return st
    config = opensocial.ContainerConfig(
        security_token=st,
        security_token_param='fcauth',
        server_rpc_base='http://friendconnect.gmodules.com/ps/api/rpc',
        server_rest_base='http://friendconnect.gmodules.com/ps/api'
    )
    container = opensocial.ContainerContext(config)
    return container
