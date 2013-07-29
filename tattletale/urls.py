"""
Tattletale is a Python web service for a realtime news feed
"""

from __future__ import absolute_import

__author__ = 'jag'
__copyright__ = 'Copyright (c) 2013, SocialCode'
__license__ = 'Confidential and proprietary - not licensed for distribution'

import logging

logger = logging.getLogger(__name__)

from django.conf.urls.defaults import patterns, include

urlpatterns = patterns(
    '',
    (r'^api/', include('tattletale.api.urls'))
)

