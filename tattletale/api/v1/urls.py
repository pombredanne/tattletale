"""
Tattletale is a Python web service for a realtime news feed
"""

from __future__ import absolute_import

__author__ = 'jag'
__copyright__ = 'Copyright (c) 2013, SocialCode'
__license__ = 'Confidential and proprietary - not licensed for distribution'

import logging

logger = logging.getLogger(__name__)

from tastypie.api import Api
from django.conf.urls.defaults import patterns, include

from .handlers import MessageResource

api = Api(api_name='v1')
api.register(MessageResource())

urlpatterns = patterns(
    '',
    (r'', include(api.urls))
)