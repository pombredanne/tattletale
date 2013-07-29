"""
Tattletale is a Python web service for a realtime news feed
"""

from __future__ import absolute_import

__author__ = 'jag'
__copyright__ = 'Copyright (c) 2013, SocialCode'
__license__ = 'Confidential and proprietary - not licensed for distribution'

import logging

logger = logging.getLogger(__name__)

from .. import r_conn
from .subscription.base import get_subscription_source
from ..models import Router

def tattler(user_id):
    subscription_src = get_subscription_source()
    subscriptions = subscription_src.get_subscriptions_for_user(user_id)
    subber = r_conn.pubsub()
    for (routing_key, routing_value) in subscriptions:
        subber.subscribe(Router.channel_key(routing_key, routing_value))
    user_channel = type(subscription_src).channel_for_user(user_id)
    subber.subscribe(user_channel)
    messages = subber.listen()
    while True:
        message = messages.next()
        if message['channel'] == user_channel:
            add_remove_cmd = message['data']
            fn = subber.subscribe if add_remove_cmd['add_or_remove'] == 'add' \
                else subber.unsubscribe
            fn(Router.channel_key(add_remove_cmd['route_key'],
                                  add_remove_cmd['route_value']))
        else:
            message_id = message['data']
            yield message_id
    subber.unsubscribe()




