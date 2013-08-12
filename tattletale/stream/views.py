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

from django.http import StreamingHttpResponse, HttpResponseForbidden

from .. import r_conn
from .subscription.base import get_subscription_source
from ..models import Router, Message

def tattler(exchange_name, user_id):
    logger.info('Opening new tattler for user ID %s on %s', user_id,
                exchange_name)
    subscription_src = get_subscription_source()
    subscriptions = dict([(Router.channel_key(exchange_name, route_key,
                                              route_value), role)
                          for (route_key, route_value, role) in
                          subscription_src.get_subscriptions_for_user(
                              user_id, exchange_name)])
    logger.info('Subscriptions for user %s on %s are: %s', user_id,
                exchange_name, subscriptions)
    subber = r_conn.pubsub()
    for channel in subscriptions:
        subber.subscribe(channel)
    user_channel = type(subscription_src).channel_for_user(user_id,
                                                           exchange_name)
    subber.subscribe(user_channel)
    messages = subber.listen()
    try:
        while True:
            message = messages.next()
            logger.debug('Raw message received: %s', message)
            if message['type'] != 'message':
                continue
            if message['channel'] == user_channel:
                add_remove_cmd = json.loads(message['data'])
                channel_key = Router.channel_key(exchange_name,
                                                 add_remove_cmd['route_key'],
                                                 add_remove_cmd['route_value'])
                if add_remove_cmd['add_or_remove'] == 'add':
                    subber.subscribe(channel_key)
                    role = subscription_src.get_role_for_subscription(
                        user_id, exchange_name, add_remove_cmd['route_key'],
                        add_remove_cmd['route_value'])
                    subscriptions[channel_key] = role
                else:
                    subber.unsubscribe(channel_key)
                    del subscriptions[channel_key]
            else:
                message_id = message['data']
                message_obj = Message.get(message_id)
                if subscriptions[message['channel']] in message_obj.roles:
                    logger.debug('User %s has role %s for channel %s. '
                                 'Publishing!',
                                 user_id, subscriptions[message['channel']],
                                 message['channel'])
                    # Messages < 1024 bytes will get buffered - make sure we
                    # cross that threshold
                    to_return = message_obj.as_json(indent=None)
                    if len(to_return) < 1024:
                        to_return += ' ' * (1024 - len(to_return))
                    yield to_return+'\n'
    except Exception, e:
        logger.info('Tattler for %s on %s shutting down: %s', user_id,
                    exchange_name, e)
        subber.unsubscribe()
        raise


def tattler_stream(request, exchange_name):
    if request.user.is_anonymous():
        return HttpResponseForbidden()
    response_obj = StreamingHttpResponse(
        streaming_content=tattler(exchange_name, request.user.id),
        content_type='text/plain')
    return response_obj
