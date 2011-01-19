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

__author__ = 'api.kurrik@google.com (Arne Roomann-Kurrik)'

import base64
import hashlib
import urllib
import oauth
import hmac
import logging

from opensocial.Crypto.PublicKey import RSA
from opensocial.Crypto.Util import number

class RequestValidator(object):
  def get_signature_base_string(self, method, url, params):
    """
    Builds the signature base string (as defined by OAuth) for this request.

    Args:
      method: string The HTTP method used for signing the request.
      url: string The fully-qualified url of the request.
      params: string Parameters used to sign the request.  Should be a merged
          set of all querystring, form-urlencoded POST body, and header params.
      
    Returns: string A signature base string as defined by the OAuth spec.
    """
    encoded_params = {}
    for key, value in params.items():
      encoded_params[key] = value.encode('utf-8', 'ignore')

    oauth_request = oauth.OAuthRequest(
        http_method=method.upper(), 
        http_url=url, 
        parameters=encoded_params)

    base_str = '&'.join((
        oauth.escape(oauth_request.get_normalized_http_method()),
        oauth.escape(oauth_request.get_normalized_http_url()),
        oauth.escape(oauth_request.get_normalized_parameters())))

    return base_str
    
  def validate(self, method, url, params):
    """
    Determines the validity of an OAuth-signed HTTP request.
    
    Args:
      method: string The HTTP method used for signing the request.
      url: string The fully-qualified url of the request.
      params: string Parameters used to sign the request.  Should be a merged
          set of all querystring, form-urlencoded POST body, and header params.
      
    Returns: bool True if the request validated, False otherwise.
    """
    raise NotImplementedError('RequestValidator must be subclassed.')


class RsaSha1Validator(RequestValidator):
  def __init__(self, public_key_str, exponent=65537):
    """
    Creates a validator based off of the RSA-SHA1 signing mechanism.
    
    Args:
      public_key_str: string The RSA public key modulus, expressed in hex 
          format.  Typically, this will look something like: 
                0x00b1e057678343866db89d7dec2518
                99261bf2f5e0d95f5d868f81d600c9a1
                01c9e6da20606290228308551ed3acf9
                921421dcd01ef1de35dd3275cd4983c7
                be0be325ce8dfc3af6860f7ab0bf3274
                2cd9fb2fcd1cd1756bbc400b743f73ac
                efb45d26694caf4f26b9765b9f656652
                45524de957e8c547c358781fdfb68ec0
                56d1
          A list of such values can be found at 
          https://opensocialresources.appspot.com/certificates/
      exponent: int The RSA public key exponent.
    """
    public_key_long = long(public_key_str, 16)
    self.public_key = RSA.construct((public_key_long, exponent))
  
  def validate(self, method, url, params):
    """
    Determines the validity of an OAuth-signed HTTP request.
    
    Args:
      method: string The HTTP method used for signing the request.
      url: string The fully-qualified url of the request.
      params: string Parameters used to sign the request.  Should be a merged
          set of all querystring, form-urlencoded POST body, and header params.
      
    Returns: bool True if the request validated, False otherwise.
    """
    base_string = self.get_signature_base_string(method, url, params)
    local_hash = hashlib.sha1(base_string).digest()
    
    if not params.has_key("oauth_signature"):
      return False
      
    try:
      encoded_remote_signature = urllib.unquote(params["oauth_signature"])
      remote_signature = base64.decodestring(encoded_remote_signature)
      remote_hash = self.public_key.encrypt(remote_signature, '')[0][-20:]
    except:
      return False
      
    return local_hash == remote_hash

class HmacSha1Validator(RequestValidator):
  def __init__(self, key):
    """
    Creates a validator based off of the HMAC-SHA1 signing mechanism.
    
    Args:
      key: string The shared secret key used to sign this request.  Typically,
          this value will be shared with the owner of an application at the
          time the application is registered with the container.
      exponent: int The RSA public key exponent.
    """
    self.hmac_key = '%s&' % oauth.escape(key)
    
  def validate(self, method, url, params):
    """
    Determines the validity of an OAuth-signed HTTP request.
    
    Args:
      method: string The HTTP method used for signing the request.
      url: string The fully-qualified url of the request.
      params: string Parameters used to sign the request.  Should be a merged
          set of all querystring, form-urlencoded POST body, and header params.
      
    Returns: bool True if the request validated, False otherwise.
    """
    base_string = self.get_signature_base_string(method, url, params)
    local_hash = hmac.new(self.hmac_key, base_string, hashlib.sha1).digest()

    if not params.has_key("oauth_signature"):
      return False

    try:
      encoded_remote_hash = urllib.unquote(params["oauth_signature"])
      remote_hash = base64.decodestring(encoded_remote_hash)
    except:
      return False

    return local_hash == remote_hash
    
    
