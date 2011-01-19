#!/usr/bin/python
#
# Copyright (C) 2007, 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


__author__ = 'davidbyttow@google.com (David Byttow)'


import hashlib
import random
import time
import urlparse
from types import ListType

import data
import http

from opensocial import simplejson


def generate_uuid(*args):
  """Simple method for generating a unique identifier.
  
  Args: Any arguments used to help make this uuid more unique.
  
  Returns: A 128-bit hex identifier.

  """
  t = long(time.time() * 1000)
  r = long(random.random() * 1000000000000000L)
  a = random.random() * 1000000000000000L
  data = '%s %s %s %s' % (str(t), str(r), str(a), str(args))
  return hashlib.md5(data).hexdigest()


class Request(object):
  """Represents an OpenSocial request that can be processed via RPC or REST."""
  
  def __init__(self, rest_request, rpc_request, requestor=None):
    self.rest_request = rest_request
    self.rpc_request = rpc_request
    self.set_requestor(requestor)
    
  def get_requestor(self):
    """Get the requestor id for this request.
    
    Returns: The requestor's id.
    
    """
    return self.__requestor
  
  def set_requestor(self, id):
    """Set the requestor id for this request.
    
    This does not accept any keywords such as @me.
    TODO: Refactor the id check out of here, it feels wrong.
    
    Args:
      id: str The requestor's id.
      
    """
    if id and id[0] is not '@':
      self.__requestor = id
    else:
      self.__requestor = None
    
  def get_query_params(self):
    """Returns the query params string for this request."""
    query_params = {}
    if self.get_requestor():
      query_params['xoauth_requestor_id'] = self.get_requestor()
    return query_params
  
  def make_rest_request(self, url_base):
    """Creates a RESTful HTTP request.
    
    Args:
      url_base: str The base REST URL.

    """
    return self.rest_request.make_http_request(url_base,
                                               self.get_query_params())

  def get_rpc_body(self):
    return self.rpc_request.get_rpc_body()


class FetchSupportedFields(Request):
    """A request class for fetching supported fields. """
    def __init__(self, user_id, osobject):
        rest_request = RestRequestInfo('/'.join((osobject, '@supportedFields')),'GET')
        super(FetchSupportedFields, self).__init__(rest_request,
                                             None,
                                             user_id)
    def process_json(self, json):
        """Construct the appropriate OpenSocial object from a JSON dict.
        Args:
        json: dict The JSON structure.
        Returns: a Collection of Person objects.
        """
        return json


class FetchGroupRequest(Request):
    """A request for handling group"""
    def __init__(self, user_id, params=None):
        params = params or {}
        rest_request = RestRequestInfo('/'.join(('groups', user_id)),'GET', params )
       
        super(FetchGroupRequest, self).__init__(rest_request,
                                             None,
                                             user_id)
    
    def process_json(self, json):
        """Construct the appropriate OpenSocial object from a JSON dict.
        Args:
        json: dict The JSON structure.
        Returns: a Collection of Person objects.
        """
        return data.Collection.parse_json(json, data.Group)
    
class FetchAlbumRequest(Request):
    """A request for handling Album"""
    
    def __init__(self, user_id, albumid=None, params=None):
        params = params or {}
        if albumid !=  None:
            rest_request = RestRequestInfo('/'.join(('albums', user_id,'@self', albumid)),'GET', params )
        else:
            rest_request = RestRequestInfo('/'.join(('albums', user_id,'@self')),'GET', params )
            
        super(FetchAlbumRequest, self).__init__(rest_request,
                                             None,
                                             user_id)
    
    def process_json(self, json):
        """Construct the appropriate OpenSocial object from a JSON dict.
        Args:
        json: dict The JSON structure.
        Returns: a Collection of Person objects.
        """
        json_list = json.get('album') 
        
        if json_list != None:
            """ this is  individual album """
            return data.Album(json_list)
        
        return data.Collection.parse_json(json, data.Album )
    
    
class FetchMediaItemsRequest(Request):
    """A request for handling Album"""
    
    def __init__(self, user_id, albumid=None, mediaitemid=None, params=None):
        params = params or {}
        if mediaitemid !=  None:
            rest_request = RestRequestInfo('/'.join(('mediaitems', user_id,'@self', albumid, mediaitemid)),'GET', params )
        else:
            rest_request = RestRequestInfo('/'.join(('mediaitems', user_id,'@self', albumid)),'GET', params )
            
        super(FetchMediaItemsRequest, self).__init__(rest_request,
                                             None,
                                             user_id)
    
    def process_json(self, json):
        """Construct the appropriate OpenSocial object from a JSON dict.
        Args:
        json: dict The JSON structure.
        Returns: a Collection of Person objects.
        """
        json_list = json.get('mediaItem') 
        
        if json_list != None:
            """ this is  individual album """
            return data.MediaItem(json_list)
        
        return data.Collection.parse_json(json, data.MediaItem )
    
    
class FetchStatusMoodRequest(Request):
    """A request for handling Statusmoodcomments"""
    
    def __init__(self, user_id, params=None):
        params = params or {}
        rest_request = RestRequestInfo('/'.join(('statusmood', user_id,'@self')),'GET', params )
       
        super(FetchStatusMoodRequest, self).__init__(rest_request,
                                                     None,
                                                     user_id)
            
    def process_json(self, json):
        """Construct the appropriate OpenSocial object from a JSON dict.
        Args:
        json: dict The JSON structure.
        Returns: a Collection of Person objects.
        """
        return data.StatusMood(json)

class FetchStatusMoodCommentsRequest(Request):
    """A request for handling StatusmoodcommentsRequests"""
    
    def __init__(self, user_id, params=None):
        params = params or {}
        rest_request = RestRequestInfo('/'.join(('statusMoodComments', user_id,'@self')),'GET', params )
       
        super(FetchStatusMoodCommentsRequest, self).__init__(rest_request,
                                                     None,
                                                     user_id)
            
    def process_json(self, json):
        """Construct the appropriate OpenSocial object from a JSON dict.
        Args:
        json: dict The JSON structure.
        Returns: a Collection of statusmoodcomments objects objects.
        """
        return data.Collection.parse_json(json, data.StatusMoodComments)
    
    
class FetchProfileCommentsRequest(Request):
    """A request for handling profile comments"""
    
    def __init__(self, user_id, params=None):
        params = params or {}
        rest_request = RestRequestInfo('/'.join(('profilecomments', user_id,'@self')),'GET', params )
        super(FetchProfileCommentsRequest, self).__init__(rest_request,
                                                     None,
                                                     user_id)
            
    def process_json(self, json):
        """Construct the appropriate OpenSocial object from a JSON dict.
        Args:
        json: dict The JSON structure.
        Returns: a Collection of statusmoodcomments objects objects.
        """
        return data.Collection.parse_json(json, data.ProfileComments)        

class FetchPeopleRequest(Request):    
  """A request for handling fetching a collection of people."""
  
  def __init__(self, user_id, group_id, fields=None, params=None):
    params = params or {}
    if fields:
      params['fields'] = ','.join(fields)
    rest_request = RestRequestInfo('/'.join(('people', user_id, group_id)),
                                   params=params)
    rpc_params = params.copy()
    rpc_params.update({'userId': user_id,
                       'groupId': group_id})
    rpc_request = RpcRequestInfo('people.get', params=rpc_params)
    super(FetchPeopleRequest, self).__init__(rest_request,
                                             rpc_request,
                                             user_id)
    
  def process_json(self, json):
    """Construct the appropriate OpenSocial object from a JSON dict.
    
    Args:
      json: dict The JSON structure.
      
    Returns: a Collection of Person objects.

    """
    return data.Collection.parse_json(json, data.Person)

    
class FetchPersonRequest(FetchPeopleRequest):
  """A request for handling fetching a single person by id."""

  def __init__(self, user_id, fields=None, params={}):
    super(FetchPersonRequest, self).__init__(user_id,
                                             '@self',
                                             fields=fields,
                                             params=params)

  def process_json(self, json):
    """Construct the appropriate OpenSocial object from a JSON dict.
    
    Args:
      json: dict The JSON structure.
      
    Returns: A Person object.

    """
    return data.Person.parse_json(json)


class FetchAppDataRequest(Request):
  """A request for handling fetching app data."""

  def __init__(self, user_id, group_id, app_id='@app', fields=None, 
               params=None):
    params = params or {}
    if fields:
      params['fields'] = ','.join(fields)
    
    rest_path = '/'.join(('appdata', user_id, group_id, app_id))
    rest_request = RestRequestInfo(rest_path, params=params)
    
    # TODO: Handle REST fields.
    params.update({'userId': user_id,
                   'groupId': group_id,
                   'appId': app_id,
                   'keys': fields})
    rpc_request = RpcRequestInfo('appdata.get', params=params)
    super(FetchAppDataRequest, self).__init__(rest_request,
                                              rpc_request,
                                              user_id)

  def process_json(self, json):
    """Construct the appropriate OpenSocial object from a JSON dict.
    
    Args:
      json: dict The JSON structure.
      
    Returns: An AppData object.

    """
    if type(json) == ListType:
      return json
    else:
      return data.AppData.parse_json(json)


class UpdateAppDataRequest(Request):
  """A request for handling updating app data."""

  def __init__(self, user_id, group_id, app_id='@app', fields=None, data={}, 
               params=None):
    params = params or {}
    if fields:
      params['fields'] = ','.join(fields)
    else: 
      params['fields'] = ','.join(data.keys())

    params['data'] = data

    #TODO: add support for rest
    params.update({'userId': user_id,
                   'groupId': group_id,
                   'appId': app_id})
    rpc_request = RpcRequestInfo('appdata.update', params=params)
    super(UpdateAppDataRequest, self).__init__(None,
                                              rpc_request,
                                              user_id)

  def process_json(self, json):
    return json


class DeleteAppDataRequest(Request):
  """A request for handling deleting app data."""

  def __init__(self, user_id, group_id, app_id='@app', fields=None, 
               params=None):
    params = params or {}
    if fields:
      params['fields'] = ','.join(fields)

    #TODO: add support for rest
    params.update({'userId': user_id,
                   'groupId': group_id,
                   'appId': app_id,
                   'keys': params['fields']})
    rpc_request = RpcRequestInfo('appdata.delete', params=params)
    super(DeleteAppDataRequest, self).__init__(None,
                                              rpc_request,
                                              user_id)

  def process_json(self, json):
    return json




class CreateNotificationRequest(Request):
    """ A request for creating an Notification. """
    def __init__(self, user_id, recipients, mediaitems = None, templateParameters = None,  
               params=None):

        params = params or {}
        bodycontent = {}
        if mediaitems !=None:
            itemlist =[]
            for mediaitem in  mediaitems:
                itemdict = {}
                itemdict['msMediaItemUri'] = mediaitem;
                itemlist.append(itemdict);
                
            bodycontent['mediaItems'] = itemlist
            bodycontent['recipientIds'] = recipients
            bodycontent['templateParameters'] = templateParameters
        
        #if user_id != "@me": 
        #    params['xoauth_requestor_id'] = user_id;
        
        rest_request = RestRequestInfo('/'.join(('notifications', user_id,'@self')),'POST', params, bodycontent, False)
        super(CreateNotificationRequest, self).__init__(rest_request,
                                                  None,
                                                  user_id)
        
    def process_json(self, json):
        return json

class CreateAlbumRequest(Request):
  def __init__(self, user_id, body, params = None):
    params = params or {}
    rest_request = RestRequestInfo('/'.join(('albums', user_id,'@self')),'POST', params, body , False)
    super(CreateAlbumRequest, self ).__init__(rest_request, None, user_id)
    pass
    
  def process_json(self, json):
    return json

class CreateActivityRequest(Request):
  """ A request for creating an activity. """
  def __init__(self, user_id, activity, group_id='@self', app_id='@app', 
               params=None):
    params = params or {}
    params['activity'] = activity

    #TODO: add support for rest
    params.update({'userId': user_id,
                   'groupId': group_id,
                   'appId': app_id})
    rpc_request = RpcRequestInfo('activities.create', params=params)
    super(CreateActivityRequest, self).__init__(None,
                                              rpc_request,
                                              user_id)
    
  def process_json(self, json):
    return json


class FetchActivityRequest(Request):
  def __init__(self, user_id, group_id='@self', app_id=None, params=None):
    params = params or {}
    #TODO: add support for rest
    params.update({'userId': user_id,
                   'groupId': group_id,
                   'appId': app_id,
                  })
    rpc_request = RpcRequestInfo('activities.get', params=params)
    if app_id != None:
      rest_request = RestRequestInfo('/'.join(('activities', user_id,'@self', app_id)),'GET', params)
    else:
      rest_request = RestRequestInfo('/'.join(('activities', user_id,'@self')),'GET', params)
    
    super(FetchActivityRequest, self).__init__(rest_request,
                                              rpc_request,
                                              user_id)
  
  def process_json(self, json):
    return data.Collection.parse_json(json, data.Activity)


class RestRequestInfo(object):
  """Represents a pending REST request."""

  def __init__(self, path, method='GET', params=None, body=None, body_hash=True):
    self.method = method
    self.path = path
    self.params = params or {}
    self.body = body
    self.body_hash = body_hash

  def make_http_request(self, url_base, query_params=None):
    """Generates a http.Request object for the UrlFetch interface.
    
    Args:
      url_base: str The base REST URL.
    
    Returns: The http.Request object.

    """
    # Ensure that there is a path separator.
    if url_base[-1] is not '/' and self.path[0] is not '/':
      url_base = url_base + '/'
    url = url_base + self.path
    if query_params:
      self.params.update(query_params)

    return http.Request(url, method=self.method, signed_params=self.params, post_body=self.body, add_bodyhash=self.body_hash)

class TextRpcRequest(Request):
  """ Represents an RPC request which is not configured with parameters, but
  a raw text blob.  Intended for debugging or developer tools."""
  def __init__(self, rpc_body, requestor=None):
    self.__rpc_body = rpc_body;
    self.set_requestor(requestor)

  def get_rpc_body(self):
    return simplejson.loads(self.__rpc_body)

  def get_requestor(self):
    """Get the requestor id for this request.

    Returns: The requestor's id.

    """
    return self.__requestor

  def set_requestor(self, id):
    """Set the requestor id for this request.

    This does not accept any keywords such as @me.
    TODO: Refactor the id check out of here, it feels wrong.

    Args:
      id: str The requestor's id.

    """
    if id and id[0] is not '@':
      self.__requestor = id
    else:
      self.__requestor = None

  def process_json(self, json):
    return json


class RpcRequestInfo(object):
  """Represents a pending RPC request."""

  def __init__(self, method, params, id=None):
    self.method = method
    self.params = params
    self.id = id or generate_uuid(method)
    
  def get_rpc_body(self):
    """Creates the JSON dict structure for thie RPC request.
    
    Returns: dict The JSON body for this RPC.

    """
    rpc_body = {
      'params': self.params,
      'method': self.method,
      'id': self.id,
    }
    return rpc_body


class RequestBatch(object):
  """This class will manage the batching of requests."""
  
  def __init__(self):
    self.requests = {}
    self.data = {}
  
  def add_request(self, key, request):
    """Adds a request to this batch.
    
    Args:
      key: str A unique key to pair with the result of this request.
      request: obj The request object.

    """
    if key:
      request.rpc_request.id = key
    self.requests[key] = request

  def get(self, key):
    """Get the result value for a given request key.
    
    Args:
      key: str The key to retrieve.

    """
    return self.data.get(key)

  def send(self, container):
    """Execute the batch with the specified container.
    
    Args:
      container: The container to execute this batch on.

    """
    container.send_request_batch(self, False)

  def _set_data(self, key, data):
    self.data[key] = data
