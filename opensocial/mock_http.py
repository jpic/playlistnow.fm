#!/usr/bin/python
#
# Copyright (C) 2009 Google Inc.
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


import httplib
import urllib

from opensocial import http


class MockUrlFetch(http.UrlFetch):
  """A mock UrlFetch implementation for unit tests.
  
  Used to set canned responses for urlfetch requests.  Responses are enqueued
  one at a time, and returned in the order they were added.  The default canned
  response (Error 500) will be returned if a response is not found.

  """
  def __init__(self):
    self.responses = []
    self.requests = []
    self.default_response = http.Response(httplib.INTERNAL_SERVER_ERROR, '')

  def add_response(self, response):
    """Enqueues a canned response.  Responses will be returned in order of 
    being added to the MockUrlFetch object.
    
    Args:
      response: An http.Response object that will be returned.
    """
    self.responses.append(response)

  def get_request(self):
    """Returns a request that was sent to this fetcher.  Requests will be 
    returned in the order of being added to the MockUrlFetch object.
    """
    return self.requests.pop(0)
    
  def fetch(self, request):
    """Perform the fake fetch.
    
    Returns:
      http.Response An enqueued response, if available, otherwise the default.
    """
    self.requests.append(request)
    if len(self.responses) > 0:
      return self.responses.pop(0)
    else:
      return self.default_response

