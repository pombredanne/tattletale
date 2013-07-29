"""
Tattletale is a Python web service for a realtime news feed
"""

from __future__ import absolute_import

__author__ = 'jag'
__copyright__ = 'Copyright (c) 2013, SocialCode'
__license__ = 'Confidential and proprietary - not licensed for distribution'

import logging

logger = logging.getLogger(__name__)

import uuid
import json
import time
from . import r_conn
from . import exceptions

MAX_QUEUE_LENGTH = 1000

class Message(object):
    TTL = 60*60*24*5

    text = None
    publisher = None
    routing_key = None
    uuid = None

    def __init__(self, text=None, publisher=None, routing_key=None, **kwargs):
        self.text = text
        self.publisher = publisher
        self.routing_key = routing_key
        self.r_conn = r_conn

    @classmethod
    def key_for_uuid(cls, uuid):
        return 'tattletale-msg-%s' % uuid

    @property
    def key(self):
        """The key to store this message at"""
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        return type(self).key_for_uuid(self.uuid)

    @classmethod
    def get(cls, uuid):
        obj = cls(**json.loads(
            r_conn.hgetall(cls.key_for_uuid(uuid))['message']))
        obj.uuid = uuid
        return obj

    def publish(self, exchange):
        """Publish this message on the given Exchange"""
        message = json.dumps({'text': self.text,
                              'publisher': self.publisher,
                              'routing_key': self.routing_key})
        with self.r_conn.pipeline() as pipe:
            pipe.hmset(self.key,
                       dict(timestamp=time.time(),
                            message=message))
            pipe.expire(self.key, self.TTL)
            pipe.execute()
        exchange.publish_message(self.key, self.routing_key)


class Router(object):
    def __init__(self):
        self.r_conn = r_conn

    def generate_queue_key(self, route_key, route_value):
        return 'tattletale-queue-%s::%s' % (route_key, route_value)

    def generate_channel_key(self, route_key, route_value):
        return 'tattletale-channel-%s::%s' % (route_key, route_value)

    def route(self, message_id, routing_key):
        with self.r_conn.pipeline() as pipe:
            for route_key, route_value in routing_key.iteritems():
                pipe.lpush(self.generate_queue_key(route_key, route_value),
                           message_id)
                pipe.ltrim(self.generate_queue_key(route_key, route_value),
                           0, MAX_QUEUE_LENGTH)
                pipe.publish(self.generate_channel_key(route_key, route_value),
                             message_id)
            pipe.execute()


class Exchange(object):
    def __init__(self, name, create=True):
        self.name = name
        if not name:
            raise exceptions.NoSuchExchange('Empty exchange name.')
        self.r_conn = r_conn
        self.router = Router()
        if not create:
            exchange_type = self.r_conn.type(self.name)
            if exchange_type != 'list':
                raise exceptions.NoSuchExchange('No such exchange.')

    def publish_message(self, message_id, routing_key):
        self.r_conn.lpush(self.name, message_id)
        self.router.route(message_id, routing_key)






