#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import re

from restkit.errors import Unauthorized

from ralph.business.models import Venture
from ralph.util import plugin
from ralph.cmdb.integration.lib.fisheye import Fisheye
from ralph.cmdb.integration.lib.puppet_yaml import load
from ralph.cmdb import models as db
from ralph.cmdb.integration.base import BaseImporter
from ralph.cmdb.integration.util import strip_timezone

from lck.django.common import nested_commit_on_success

logger = logging.getLogger(__name__)


class PuppetGitImporter(BaseImporter):

    """ Fetch changesets from fisheye repo.
    CI's are recognized from changed repo directories. Eg:
    ./modules/venture/venture__role
    """

    def __init__(self, fisheye_class=Fisheye):
        self.fisheye = fisheye_class()

    @staticmethod
    @plugin.register(chain='cmdb_git')
    def git(**kwargs):
        x = PuppetGitImporter()
        x.import_git()
        return True, 'Done', kwargs

    def is_imported(self, changeset):
        return db.CIChangeGit.objects.filter(changeset=changeset).exists()

    @nested_commit_on_success
    def import_changeset(self, changeset):
        x = self.fisheye
        details = x.get_details(changeset)
        logger.debug(details.comment)
        c = db.CIChangeGit()
        c.comment = unicode(details.comment)[0:999]
        c.time = strip_timezone(details.get('date'))
        files_list_str = ""
        try:
            files = details.fileRevisionKey
            files_list = []
            for f in files:
                path = (f.get('path'))
                files_list.append(path)
            files_list_str = '#'.join(files_list)
        except AttributeError:
            files_list_str = ''
            files_list = []
        c.file_paths = unicode(files_list_str)[0:3000]
        c.author = details.get('author')
        c.ci = self.get_ci_by_path(files_list)
        c.changeset = changeset
        c.save()

    def reconcilate(self, ch):
        obj = db.CIChangeGit.objects.get(changeset=ch)
        ci = self.get_ci_by_path(obj.file_paths.split('#'))
        if ci:
            obj.ci = ci
            obj.save()
            ch = db.CIChange.get_by_content_object(obj)
            ch.ci = ci
            ch.save()

    def import_git(self):
        try:
            ret = self.fisheye.get_changes()
        except Unauthorized as e:
            logger.warning(str(e))
            return
        for changeset in ret.getchildren():
            if not self.is_imported(changeset):
                self.import_changeset(changeset)
            else:
                self.reconcilate(changeset)

    def find_venture(self, name):
        """Returns first venture ci with given `name`"""
        try:
            return db.CI.get_by_content_object(
                Venture.objects.get(symbol=name)
            )
        except Venture.DoesNotExist:
            pass

    def find_role(self, venture_ci, role):
        """Returns first role of parent `venture_ci` with given `role` name"""
        for relation in db.CIRelation.objects.filter(
                parent=venture_ci,
                type=db.CI_RELATION_TYPES.HASROLE.id,
                child__name=role):
            return relation.child

    def find_ci_by_venturerole(self, role):
        venture = role[0]
        role = role[1]
        v = self.find_venture(venture)
        if not v:
            v = self.find_venture(venture.replace('-', '_'))
            if not v:
                return None
        r = self.find_role(v, role.replace('.pp', ''))
        if not r:
            r = self.find_role(v, role.replace('.pp', '').replace('__', '_'))
            if not r:
                # can't find role. assign none for now.
                return None
            else:
                return r
        else:
            return r

    def get_ci_by_path_mapping(self, path):
        """Return first successfull ci mapped to this path"""
        for mapping in db.GitPathMapping.objects.all():
            if mapping.is_regex:
                compiled = re.compile(mapping.path)
                if compiled.match(path):
                    return mapping.ci
            else:
                if path in mapping.path:
                    return mapping.ci

    def get_ci_by_path(self, paths):
        ventures_1 = re.compile('modules/ventures/([^\/]+)/files/(.*)')
        ventures_2 = re.compile('modules/ventures/([^\/]+)/manifests/(.*)')
        for path in paths:
            groups = None
            if ventures_1.match(path):
                groups = ventures_1.match(path).groups()
                ci = self.find_ci_by_venturerole(groups)
                if ci:
                    return ci
            elif ventures_2.match(path):
                groups = ventures_2.match(path).groups()
                ci = self.find_ci_by_venturerole(groups)
                if ci:
                    return ci
            else:
                ci = self.get_ci_by_path_mapping(path)
                if ci:
                    return ci
