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
    roles = []
    routing_key = None
    uuid = None
    timestamp = None

    def __init__(self, text=None, publisher=None, routing_key=None,
                 roles=[], timestamp=None, **kwargs):
        self.text = text
        self.publisher = publisher
        self.routing_key = routing_key
        self.roles = roles
        self.timestamp = timestamp or time.time()
        self.r_conn = r_conn

    @classmethod
    def key_for_uuid(cls, uuid):
        return 'tattletale-msg-%s' % uuid

    @classmethod
    def uuid_from_key(cls, key):
        return key[len('tattletale-msg-'):]

    @property
    def key(self):
        """The key to store this message at"""
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        return type(self).key_for_uuid(self.uuid)

    @classmethod
    def get(cls, key):
        logger.debug('Getting message for key %s', key)
        message_dict = r_conn.hgetall(key)
        logger.debug('Message dict gathered from exchange: %s', message_dict)
        obj = cls(**json.loads(message_dict['message']))
        obj.uuid = cls.uuid_from_key(key)
        return obj

    def as_json(self, **kwargs):
        return json.dumps({'text': self.text,
                           'publisher': self.publisher,
                           'roles': self.roles,
                           'routing_key': self.routing_key,
                           'timestamp': self.timestamp})

    def publish(self, exchange):
        """Publish this message on the given Exchange"""
        message = self.as_json()
        with self.r_conn.pipeline() as pipe:
            pipe.hmset(self.key,
                       dict(timestamp=self.timestamp,
                            message=message))
            pipe.expire(self.key, self.TTL)
            pipe.execute()
        exchange.publish_message(self.key, self.routing_key)


class Router(object):
    def __init__(self, exchange_name):
        self.exchange_name = exchange_name
        self.r_conn = r_conn

    @classmethod
    def queue_key(cls, exchange_name, route_key, route_value):
        return 'tattletale-queue-%s::%s::%s' % (exchange_name,
                                                route_key,
                                                route_value)

    @classmethod
    def channel_key(cls, exchange_name, route_key, route_value):
        return 'tattletale-channel-%s::%s::%s' % (exchange_name,
                                                  route_key,
                                                  route_value)

    def route(self, message_id, routing_key):
        with self.r_conn.pipeline() as pipe:
            for route_key, route_value in routing_key.iteritems():
                pipe.lpush(type(self).queue_key(self.exchange_name,
                                                route_key, route_value),
                           message_id)
                pipe.ltrim(type(self).queue_key(self.exchange_name,
                                                route_key, route_value),
                           0, MAX_QUEUE_LENGTH)
                pipe.publish(type(self).channel_key(self.exchange_name,
                                                    route_key, route_value),
                             message_id)
            pipe.execute()


class Exchange(object):
    def __init__(self, name, create=True):
        self.name = name
        if not name:
            raise exceptions.NoSuchExchange('Empty exchange name.')
        self.r_conn = r_conn
        self.router = Router(exchange_name=self.name)
        if not create:
            exchange_type = self.r_conn.type(self.name)
            if exchange_type != 'list':
                raise exceptions.NoSuchExchange('No such exchange.')

    def publish_message(self, message_id, routing_key):
        self.r_conn.lpush(self.name, message_id)
        self.router.route(message_id, routing_key)






