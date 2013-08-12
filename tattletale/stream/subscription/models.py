"""
Tattletale is a Python web service for a realtime news feed
"""

from __future__ import absolute_import

__author__ = 'jag'
__copyright__ = 'Copyright (c) 2013, SocialCode'
__license__ = 'Confidential and proprietary - not licensed for distribution'

import logging

logger = logging.getLogger(__name__)

from django.db import models
from django.contrib.auth.models import User

from .base import SubscriptionSource

class Subscription(models.Model):
    user = models.ForeignKey(User)
    route_key = models.CharField(max_length=100)
    route_value = models.CharField(max_length=100)
    exchange_name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'User %s -> %s { %s => %s }' % (self.user, self.route_key,
                                                self.exchange, self.route_value)

    class Meta:
        unique_together = [('user', 'exchange_name', 'route_key',
                            'route_value')]

class ModelSubscriptionSource(SubscriptionSource):
    def subscribe_user_to_channel(self, user_id, exchange_name, route_key,
                                  route_value, role):
        Subscription.objects.get_or_create(user_id=user_id,
                                           exchange_name=exchange_name,
                                           route_key=route_key,
                                           route_value=route_value,
                                           defaults={'role': role})
        self.announce_subscription_change(user_id, 'add', exchange_name,
                                          route_key, route_value)

    def unsubscribe_user_from_channel(self, user_id, exchange_name, route_key,
                                      route_value):
        qs = Subscription.objects.filter(user_id=user_id, route_key=route_key,
                                         exchange_name=exchange_name,
                                         route_value=route_value)
        qs.delete()
        self.announce_subscription_change(user_id, 'remove', exchange_name,
                                          route_key, route_value)

    def get_subscriptions_for_user(self, user_id, exchange_name):
        return [(obj.route_key, obj.route_value, obj.role) for obj in
                Subscription.objects.filter(user_id=user_id,
                                            exchange_name=exchange_name)]

    def get_role_for_subscription(self, user_id, exchange_name, route_key,
                                  route_value):
        return Subscription.objects.get(user_id=user_id,
                                        exchange_name=exchange_name,
                                        route_key=route_key,
                                        route_value=route_value).role