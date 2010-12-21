# -*- coding: utf-8 -*-

from django.db import models

# Create your models here.


class State(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

class City(models.Model):

    name = models.CharField(max_length=50)
    state = models.ForeignKey(State,related_name='cities')

    def __unicode__(self):
        return self.name


""" Tests:

>>> for x in range(5):
>>>     s = State(name=u'State %s' % str(x))
>>>     s.save()
>>>     for y in range(5):
>>>         c = City(name=u'City %s on state %s' % (y,x),state=s)
>>>         c.save()
>>>
>>> [(s,s.cities.all()) for s in State.objects.all()]

[(<State: State 0>,
  [<City: City 0 on state 0>, <City: City 1 on state 0>, <City: City 2 on state 0>, <City: City 3 on state 0>, <City: City 4 on state 0>]),
 (<State: State 1>,
  [<City: City 0 on state 1>, <City: City 1 on state 1>, <City: City 2 on state 1>, <City: City 3 on state 1>, <City: City 4 on state 1>]),
 (<State: State 2>,
  [<City: City 0 on state 2>, <City: City 1 on state 2>, <City: City 2 on state 2>, <City: City 3 on state 2>, <City: City 4 on state 2>]),
 (<State: State 3>,
  [<City: City 0 on state 3>, <City: City 1 on state 3>, <City: City 2 on state 3>, <City: City 3 on state 3>, <City: City 4 on state 3>]),
 (<State: State 4>,
  [<City: City 0 on state 4>, <City: City 1 on state 4>, <City: City 2 on state 4>, <City: City 3 on state 4>, <City: City 4 on state 4>])]

"""
