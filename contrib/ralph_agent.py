#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
import urllib
import urllib2
import json
import fcntl
import errno
import time
import subprocess
import logging


RALPH_API_VERSION = '0.9'
LOG_FORMAT = '%(levelname)s\t%(asctime).19s %(filename)s:%(lineno)d\t%(message)s'


class Error(Exception):
    pass

    
class ApiError(Error):
    pass
    
    
class ApiAuthError(ApiError):
    pass


class SimpleApiClient(object):
    def __init__(self, api_url, api_username, api_key, api_resource=None):
        self.__api_url = api_url
        self.__api_username = api_username
        self.__api_key = api_key
        self.__api_resource = api_resource

    def __getattr__(self, resource):
        if self.__api_resource:
            resource = "%s/%s" % (self.__api_resource, resource)
        return SimpleApiClient(self.__api_url, self.__api_username,
                               self.__api_key, resource)

    def __get_data(self, url):
        try:
            f = urllib2.urlopen(url)
            raw_data = f.read()
            return json.loads(raw_data)
        except:
            raise ApiError(sys.exc_info()[1])
            
    def __put_data(self, url, data):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(url, data)
        request.add_header('Content-Type', 'application/json')
        request.get_method = lambda: 'PUT'
        
        try:
            f = opener.open(request)
        except urllib2.HTTPError, e:
            if '401' in e:
                raise ApiAuthError(e)
            raise ApiError(e)
        except:
            raise ApiError(sys.exc_info()[1])
        
        if 'HTTP/1.0 204 NO CONTENT' in f.info().headers:
            return True
            
        return False
    
    def __do_get_request(self, **kwargs):
        id_part = ''
        if 'id' in kwargs:
            id_part = "%s/" % kwargs['id']
            del kwargs['id']

        api_resource = self.__api_resource.replace('/get', '')
        
        url = ("%s/api/v%s/%s/%s?format=json&username=%s&api_key=%s" % 
               (self.__api_url, RALPH_API_VERSION, api_resource, id_part,
                self.__api_username, self.__api_key))

        query = '&'.join(["%s=%s" % (key, kwargs[key]) for key in kwargs])
        if query:
            url = "%s&%s" % (url, query)

        return self.__get_data(url)
        
    def __do_put_request(self, id, data):
        api_resource = self.__api_resource.replace('/put', '')

        url = ("%s/api/v%s/%s/%s/?format=json&username=%s&api_key=%s" % 
               (self.__api_url, RALPH_API_VERSION, api_resource, id,
                self.__api_username, self.__api_key))

        return self.__put_data(url, data)

    def __call__(self, **kwargs):
        if self.self.__api_resource.endswith('get/self'):
            return self.__do_get_request(**kwargs)
        elif self.self.__api_resource.endswith('put/self'):
            return self.__do_put_request(**kwargs)
        else:
            raise ApiError('Incorrect API call.')


class SimplePuppetManager(object):
    def __init__(self, ralph_url, ralph_api_username, ralph_api_key, 
                 log_path=None):
        if ralph_url.endswith('/'):
            ralph_url = ralph_url[:-1]
        
        self.api = SimpleApiClient(ralph_url, ralph_api_username, ralph_api_key)
        self.log_path = log_path
        
        if self.log_path:
            logging.basicConfig(format=LOG_FORMAT, filename=self.log_path, 
                                level=logging.INFO)

    def __get_certs_to_remove(self):
        deployments = []
        current_offset = 0
        certs = []
        
        try:
            response = self.api.deployment.get(
                offset=current_offset, limit=20, status=3,
                puppet_certificate_revoked=False)
            deployments += response['objects']
            while response['meta']['next']:
                current_offset += 20
                response = self.api.deployment.get(
                    offset=current_offset, limit=20, status=3,
                    puppet_certificate_revoked=False)
                deployments += response['objects']

            for deploy in deployments:
                certs.append({
                    'id': deploy['id'],
                    'name': deploy['hostname'],
                })
        except ApiAuthError, e:
            if self.log_path:
                logging.error('ApiAuthError occured: "%s"' % e)
        except ApiError, e:
            if self.log_path:
                logging.error('ApiError occured: "%s"' % e)

        return certs
        
    def __remove_cert(self, cert_name):
        command = ['puppet', 'cert', 'clean', cert_name]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        proc.wait()

        if proc.returncode == 0:
            return True
        
        return False
        
    def __notify_ralph(self, id):
        data = '{"puppet_certificate_revoked": "True"}'
        try:
            self.api.deployment.put(id=id, data=data)
        except ApiAuthError, e:
            if self.log_path:
                logging.error('ApiAuthError occured: "%s"' % e)
        except ApiError, e:
            if self.log_path:
                logging.error('ApiError occured: "%s"' % e)

    def remove_certs(self):
        certs = self.__get_certs_to_remove()
        for cert in certs:
            if self.__remove_cert(cert['name']):
                self.__notify_ralph(cert['id'])


if __name__ == "__main__":
    f = open('/tmp/%s.lock' % sys.argv[0], 'w')
    try:
        fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError, e:
        if e.errno == errno.EAGAIN:
            sys.stderr.write('[%s] Script already running.\n' % time.strftime('%c'))
            sys.exit(-1)
        raise
    
    args_parser = argparse.ArgumentParser(
        description='Delete certs from Puppet server.')
    args_parser.add_argument('ralph_url', help='Ralph instance address.')
    args_parser.add_argument('ralph_api_username', help='Ralph API username.')
    args_parser.add_argument('ralph_api_key', help='Ralph API key.')
    args_parser.add_argument('-l', '--log_path', help='Path to log file.')

    args = vars(args_parser.parse_args())

    spm = SimplePuppetManager(**args)
    spm.remove_certs()

    sys.exit(0)
