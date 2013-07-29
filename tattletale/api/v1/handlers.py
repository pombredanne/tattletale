"""
Tattletale is a Python web service for a realtime news feed
"""

from __future__ import absolute_import

__author__ = 'jag'
__copyright__ = 'Copyright (c) 2013, SocialCode'
__license__ = 'Confidential and proprietary - not licensed for distribution'

import logging

logger = logging.getLogger(__name__)

from tastypie.resources import Resource
from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.exceptions import NotFound

from ...exceptions import NoSuchExchange
from ...models import Message, Exchange

class MessageResource(Resource):
    uuid = fields.CharField(attribute='uuid', readonly=True)
    text = fields.CharField(attribute='text')
    publisher = fields.CharField(attribute='publisher')
    routing_key = fields.CharField(attribute='routing_key')

    class Meta:
        resource_name = 'message'
        object_class = Message
        detail_allowed_methods = ['get']
        list_allowed_methods = ['post']

    def get_resource_url(self, bundle_or_obj):
        kwargs = {
            'resource_name': self._meta.resource_name,
        }

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.uuid
        else:
            kwargs['pk'] = bundle_or_obj.uuid

        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name

        return self._build_reverse_url('api_dispatch_detail', kwargs=kwargs)

    def obj_get(self, request=None, **kwargs):
        pk = kwargs['pk']
        obj = Message.get(pk)
        if not obj:
            raise NotFound('Message expired or not found.')
        return obj

    def obj_create(self, bundle, request = None, **kwargs):
        try:
            exchange = Exchange('default')
        except NoSuchExchange, e:
            raise NotFound('No such exchange.')
        bundle.obj = Message()

        # full_hydrate does the heavy lifting mapping the
        # POST-ed payload key/values to object attribute/values
        bundle = self.full_hydrate(bundle)

        bundle.obj.publish(exchange)
        return bundle

    def detail_uri_kwargs(self, bundle_or_obj):
        if isinstance(bundle_or_obj, Bundle):
            return {'pk': bundle_or_obj.obj.uuid}
        else:
            return {'pk': bundle_or_obj.uuid}
