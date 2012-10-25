#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.utils import simplejson as json
from django.conf import settings
from restkit import Resource, BasicAuth
from lxml import objectify
import logging


logger = logging.getLogger(__name__)


class Fisheye(object):
    def __init__(self):
        user = settings.FISHEYE_USER
        password = settings.FISHEYE_PASSWORD
        jira_url = settings.FISHEYE_URL
        self.project_name = settings.FISHEYE_PROJECT_NAME
        self.auth = BasicAuth(user, password)
        self.base_url = "%s/rest-service-fe" % jira_url

    def get_resource(self, resource_name):
        complete_url = "%s/%s" % (self.base_url, resource_name)
        logger.debug("Calling " + complete_url)
        resource = Resource(complete_url, filters=[self.auth])
        return resource

    def call_resource(self, resource_name, params):
        """ call GET method and returns json/xml results"""
        resource = self.get_resource(resource_name)
        response = resource.get(headers={'Content-Type': 'application/json'})
        s = response.body_string()
        if response.headers.get('content-type').find('application/xml') >= 0:
            ret = objectify.fromstring(s)
        elif response.headers.get('content-type').find('application/json') >= 0:
            ret = json.loads(s)
        else:
            ret = s
        return ret

    def get_details(self, change_id):
        """ Returns changeset details """
        resource_name = "revisionData-v1/changeset/%(project)s/%(changeset)s" \
            % dict(
                project=self.project_name,
                changeset=change_id
            )
        return self.call_resource(resource_name, params={})

    def get_changes(self, params={}):
        """ Returns list of changesets """
        resource_name = "revisionData-v1/changesetList/%s?media=json" % \
            self.project_name
        return self.call_resource(resource_name, params)

