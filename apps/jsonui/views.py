# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.template import RequestContext


from models import City,State
from forms import CityForm

from utils import qdct_as_kwargs
from response import JSONResponse

def mainview(request):

    return render_to_response('base.html',{'form': CityForm() },
        context_instance=RequestContext(request))

def json_get_city(request):

    if not request.method == "POST":
        # return all cities if any filter was send
        return JSONResponse(City.objects.order_by('name'))

    # get cities with request.POST as filter arguments
    cities = City.objects.filter(**qdct_as_kwargs(request.POST)).order_by('name')
    
    #return JSONResponse with id and name
    return JSONResponse(cities.values('id','name'))



