"""
Tattletale is a Python web service for a realtime news feed
"""
from __future__ import absolute_import

__author__ = 'jag'
__copyright__ = 'Copyright (c) 2013, SocialCode'
__license__ = 'Confidential and proprietary - not licensed for distribution'
__version__ = '0.1'

import logging

logger = logging.getLogger(__name__)

from threading import local

from django.utils.functional import LazyObject
import redis

_locals = local()

class LazyRedisConnection(LazyObject):
    def _setup(self):
        from django.conf import settings
        self._wrapped = redis.Redis(host=getattr(settings, 'REDIS_HOST',
                                                 'localhost'),
                                    port=getattr(settings, 'REDIS_PORT',
                                                 6379),
                                    db=getattr(settings, 'REDIS_DB',
                                               0))

r_conn = LazyRedisConnection()
