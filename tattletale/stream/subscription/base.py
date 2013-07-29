"""
Tattletale is a Python web service for a realtime news feed
"""

from __future__ import absolute_import

__author__ = 'jag'
__copyright__ = 'Copyright (c) 2013, SocialCode'
__license__ = 'Confidential and proprietary - not licensed for distribution'

import logging

logger = logging.getLogger(__name__)

import json
import importlib

from django.conf import settings

from tattletale import r_conn

class SubscriptionSource(object):

    def subscribe_user_to_channel(self, user_id, route_key, route_value):
        raise NotImplementedError

    def unsubscribe_user_from_channel(self, user_id, route_key, route_value):
        raise NotImplementedError

    def get_subscriptions_for_user(self, user_id):
        raise NotImplementedError

    @classmethod
    def channel_for_user(cls, user_id):
        return 'tattletale-user-%s' % user_id

    def announce_subscription_change(self, user_id, add_or_remove, route_key,
                                     route_value):
        r_conn.publish(type(self).channel_for_user(user_id),
                       json.dumps(dict(user_id=user_id,
                                       add_or_remove=add_or_remove,
                                       route_key=route_key,
                                       route_value=route_value)))

def get_subscription_source():
    mod, cls = settings.TATTLETALE_SUBSCRIPTION_SOURCE.rsplit('.', 1)
    mod_obj = importlib.import_module(mod)
    cls_obj = getattr(mod_obj, cls)
    return cls_obj()