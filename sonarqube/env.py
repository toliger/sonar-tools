#!/Library/Frameworks/Python.framework/Versions/3.6/bin/python3

import sys
import re
import json
import requests
import sonarqube.utilities as util

HTTP_ERROR_MSG = "%s%s raised error %d: %s"
DEFAULT_URL = 'http://localhost:9000'

class Environment:

    def __init__(self, url, token):
        self.root_url = url
        self.token = token
        self.version = None
        self.major = None
        self.minor = None
        self.patch = None
        self.build = None

    def __str__(self):
        redacted_token = re.sub(r'(...).*(...)', '\1***\2', self.token)
        return "{0}@{1}".format(redacted_token, self.root_url)

    def set_env(self, url, token):
        self.root_url = url
        self.token = token
        util.logger.debug('Setting environment: %s', str(self))

    def set_token(self, token):
        self.token = token

    def get_token(self):
        return self.token

    def get_credentials(self):
        return (self.token, '')

    def set_url(self, url):
        self.root_url = url

    def get_url(self):
        return self.root_url

    def get_version(self):
        if self.version is None:
            resp = self.get('/api/server/version')
            (self.major, self.minor, self.patch, self.build) = resp.text.split('.')
            version = "{0}.{1}.{2}".format(self.major, self.minor, self.patch)
        return version

    def version_higher_or_equal_than(self, version):
        (major, minor, patch) = version.split('.')
        self.get_version()
        if patch is None:
            patch = 0
        if major > self.major:
            return True
        if major == self.major and minor > self.minor:
            return True
        if major == self.major and minor == self.minor and patch >= self.patch:
            return True
        return False

    def get(self, api, params = None):
        #for k in params:
        #    params[k] = urllib.parse.quote(str(params[k]), safe=':')
        api = normalize_api(api)
        util.logger.debug('GET: %s', self.urlstring(api, params))
        try:
            if params is None:
                r = requests.get(url=self.root_url + api, auth=self.get_credentials())
            else:
                r = requests.get(url=self.root_url + api, auth=self.get_credentials(), params=params)
        except requests.RequestException as e:
            util.logger.error(str(e))
            raise
        if (r.status_code // 100) != 2:
            util.logger.error(HTTP_ERROR_MSG, self.root_url, api, r.status_code, r.text)
        return r

    def post(self, api, params = None):
        api = normalize_api(api)
        util.logger.debug('POST: %s', self.urlstring(api, params))
        try:
            if params is None:
                r = requests.post(url=self.root_url + api, auth=self.get_credentials())
            else:
                r = requests.post(url=self.root_url + api, auth=self.get_credentials(), params=params)
        except requests.RequestException as e:
            util.logger.error(str(e))
            raise
        if (r.status_code // 100) != 2:
            util.logger.error(HTTP_ERROR_MSG, self.root_url, api, r.status_code, r.text)
        return r

    def delete(self, api, params = None):
        api = normalize_api(api)
        util.logger.debug('DELETE: %s', self.urlstring(api, params))
        try:
            if params is None:
                r = requests.delete(url=self.root_url + api, auth=self.get_credentials())
            else:
                r = requests.delete(url=self.root_url + api, auth=self.get_credentials(), params=params)
        except requests.RequestException as e:
            util.logger.error(str(e))
            raise
        if (r.status_code // 100) != 2:
            util.logger.error(HTTP_ERROR_MSG, self.root_url, api, r.status_code, r.text)
        return r

    def urlstring(self, api, params):
        first = True
        url = "{0}{1}".format(str(self), api)
        if params is not None:
            for p in params:
                sep = '?' if first else '&'
                first = False
                url += '{0}{1}={2}'.format(sep, p, params[p])
        return url

    def __verify_setting__(self, setting, key, value):
        if setting['key'] == key:
            if setting['value'] == value:
                util.logger.info("Setting %s has correct value %s", key, setting['value'])
                return 0
            else:
                util.logger.warning("Setting %s has potentially incorrect/unsafe value %s", key, setting['value'])
                return 1
        return 0

    def __verify_project_default_visibility__(self):
        resp = self.get('navigation/organization', params={'organization':'default-organization'})
        data = json.loads(resp.text)
        visi = data['organization']['projectVisibility']
        if visi == 'private':
            util.logger.info('Project default visibility is private')
        else:
            util.logger.warning('Project default visibility is %s, which can be a security risk', visi)
            return False
        return True

    def audit(self):
        util.logger.info('Auditing global settings')
        resp = self.get('settings/values')
        settings = json.loads(resp.text)
        for s in settings['settings']:
            self.__verify_setting__(s, 'sonar.forceAuthentication', 'true')
            self.__verify_setting__(s, 'sonar.cpd.cross_project', 'false')
            self.__verify_setting__(s, 'sonar.scm.disabled', 'false')
            # TODO: Check dbCleaner settings
            # TODO: Check TD rating grip
            # TODO: Check cost for writing line
            # TODO: Verify sonar.core.serverBaseURL is set
        self.__verify_project_default_visibility__()




#--------------------- Static methods, not recommended -----------------
# this is a pointer to the module object instance itself.
this = sys.modules[__name__]
this.context = Environment("http://localhost:9000", '')

def set_env(url, token):
    this.context = Environment(url, token)
    util.logger.debug('Setting GLOBAL environment: %s@%s', token, url)

def set_token(token):
    this.context.set_token(token)

def get_token():
    return this.context.token

def get_credentials():
    return (this.context.token, '')

def set_url(url):
    this.context.set_url(url)

def get_url():
    return this.context.root_url

def normalize_api(api):
    api = api.lower()
    if re.match(r'/api', api):
        pass
    elif re.match(r'api', api):
        api = '/' + api
    elif re.match(r'/', api):
        api = '/api' + api
    else:
        api = '/api/' + api
    return api

def get(api, params = None, ctxt = None):
    if ctxt is None:
        ctxt = this.context
    return ctxt.get(api, params)

def post(api, params = None, ctxt = None):
    if ctxt is None:
        ctxt = this.context
    return ctxt.post(api, params)

def delete(api, params = None, ctxt = None):
    if ctxt is None:
        ctxt = this.context
    return ctxt.delete(api, params)
