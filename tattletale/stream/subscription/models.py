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
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'User %s -> { %s => %s }' % (self.user, self.route_key,
                                             self.route_value)

class ModelSubscriptionSource(SubscriptionSource):
    def subscribe_user_to_channel(self, user_id, route_key, route_value):
        Subscription.objects.get_or_create(user=user_id,
                                           routing_key=route_key,
                                           routing_value=route_value)
        self.announce_subscription_change(user_id, 'add', route_key,
                                          route_value)

    def unsubscribe_user_to_channel(self, user_id, route_key, route_value):
        Subscription.objects.filter(user=user_id, route_key=route_key,
                                    route_value=route_value).delete()
        self.announce_subscription_change(user_id, 'remove', route_key,
                                          route_value)

    def get_subscriptions_for_user(self, user_id):
        return [(obj.route_key, obj.route_value) for obj in
                Subscription.objects.filter(user_id=user_id)]
