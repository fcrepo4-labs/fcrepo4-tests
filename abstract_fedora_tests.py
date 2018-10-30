#!/bin/env python

import TestConstants
import requests
import re
import unittest
import functools
import inspect
import pyjq
import json
from datetime import datetime, timezone
from email.utils import format_datetime


class FedoraTests(unittest.TestCase):

    nodes = []
    config = {}

    def __init__(self, config):
        super().__init__()
        self.config = config

    def getBaseUri(self):
        return self.config[TestConstants.BASE_URL_PARAM] + self.CONTAINER

    def getFedoraBase(self):
        return self.config[TestConstants.BASE_URL_PARAM]

    def run_tests(self):
        self.not_authorized()
        for test in self._testdict:
            method = getattr(self, test)
            method()

    def not_authorized(self):
        """ Ensure we can even access the repository """
        my_auth = self.get_auth(True)
        try:
            baseurl = self.config[TestConstants.BASE_URL_PARAM]
            r = requests.head(baseurl, auth=my_auth)
        except requests.exceptions.ConnectionError:
            print("Cannot connect the Fedora server, is your configuration correct? {0}".format(baseurl))
            quit()
        if str(r.status_code)[0:2] == '40':
            mesg = "Received a {} status code accessing {}, you may need to provide/check credentials".format(
                r.status_code, self.config[TestConstants.BASE_URL_PARAM])
            print(mesg)
            raise RuntimeError(mesg)

    @staticmethod
    def create_auth(username, password):
        return requests.auth.HTTPBasicAuth(username, password)

    def create_admin_auth(self):
        return FedoraTests.create_auth(
            self.config[TestConstants.ADMIN_USER_PARAM], self.config[TestConstants.ADMIN_PASS_PARAM])

    def create_user_auth(self):
        return FedoraTests.create_auth(
            self.config[TestConstants.USER_NAME_PARAM], self.config[TestConstants.USER_PASS_PARAM])

    def get_auth(self, admin=True):
        if admin:
            return self.create_admin_auth()
        else:
            return self.create_user_auth()

    def do_post(self, parent=None, headers=None, body=None, files=None, admin=True):
        if parent is None:
            parent = self.config[TestConstants.BASE_URL_PARAM]
        if headers is None:
            headers = {}
        my_auth = self.get_auth(admin)
        return requests.post(parent, body, None, headers=headers, files=files, auth=my_auth)

    def do_put(self, url, headers=None, body=None, files=None, admin=True):
        if headers is None:
            headers = {}
        my_auth = self.get_auth(admin)
        return requests.put(url, body, headers=headers, files=files, auth=my_auth)

    def do_get(self, url, headers=None, admin=True, auth=None):
        if headers is None:
            headers = {}
        if auth is not None:
            my_auth = auth if auth != 'anonymous' else None
        else:
            my_auth = self.get_auth(admin)

        return requests.get(url, headers=headers, auth=my_auth)

    def do_head(self, url, headers=None, admin=True):
        if headers is None:
            headers = {}
        my_auth = self.get_auth(admin)
        return requests.head(url, headers=headers, auth=my_auth)

    def do_patch(self, url, body, headers=None, admin=True):
        if headers is None:
            headers = {}
        my_auth = self.get_auth(admin)
        return requests.patch(url, body, headers=headers, auth=my_auth)

    def do_delete(self, url, headers=None, admin=True):
        if headers is None:
            headers = {}
        my_auth = self.get_auth(admin)
        return requests.delete(url, headers=headers, auth=my_auth)

    def do_options(self, url, admin=True):
        my_auth = self.get_auth(admin)
        return requests.options(url, auth=my_auth)

    def assert_regex_in(self, pattern, container, msg):
        for i in container:
            if re.search(pattern, i):
                return
        standard_msg = '%s not found in %s' % (unittest.util.safe_repr(pattern),
                                              unittest.util.safe_repr(container))
        self.fail(self._formatMessage(msg, standard_msg))

    def assert_regex_matches(self, pattern, text, msg):
        if re.search(pattern, text):
            return
        standard_msg = '%s pattern not matched in %s' % (unittest.util.safe_repr(pattern),
                                                         unittest.util.safe_repr(text))
        self.fail(self._formatMessage(msg, standard_msg))

    def make_type(self, type):
        """ Turn a URI to Link type format """
        return "<{0}>; rel=\"type\"".format(type)

    def tear_down(self):
        """ Delete any resources created """
        for node in self.nodes:
            self.cleanup(node)
        self.nodes.clear()

    def cleanup(self, uri):
        print("Deleting {}".format(uri))
        r = self.do_delete(uri)
        if r.status_code == 204 or r.status_code == 410:
            if r.status_code == 204:
                r = self.do_get(uri)
            try:
                links = [x['url'] for x in r.links.values() if x['rel'] == 'hasTombstone']
                for tombstone in links:
                    r = self.do_delete(tombstone)
                    if r.status_code == 204:
                        return True
            except KeyError:
                return True
        return False

    def check_for_retest(self, uri):
        response = self.do_put(uri)
        if response.status_code != 201:
            caller = inspect.stack()[1][0].f_locals['self'].__class__.__name__
            print("The class ({}) has been run. You need to remove this object and all it's "
                  "children before re-running the test.".format(caller))
            rerun = input("Remove the test objects and re-run? (y/N) ")
            if rerun.lower().strip() == 'y':
                if self.cleanup(uri):
                    self.do_put(uri)
                else:
                    print("Error removing $URL, you may need to remove it manually.")
                    quit()
            else:
                print("Exiting...")
                quit()

    @staticmethod
    def get_link_headers(response):
        headers = {}
        link_headers = [x.strip() for x in response.headers['Link'].split(",")]
        for x in link_headers:
            matches = re.match(r'\s*<([^>]+)>;\s?rel=[\'"]?(\w+)[\'"]?', x)
            if matches is not None:
                try:
                    headers[matches.group(2)]
                except KeyError:
                    headers[matches.group(2)] = []
                headers[matches.group(2)].append(matches.group(1))
        return headers

    @staticmethod
    def get_location(response):
        return response.headers['Location']

    @staticmethod
    def make_prefer_header(uris, omit=False):
        if isinstance(uris, list):
            all_uris = ",".join(uris)
        else:
            all_uris = uris
        omit_value = "omit" if omit else "include"
        return TestConstants.PREFER_PATTERN.format(omit_value, all_uris)

    @staticmethod
    def get_rfc_date(isodate):
        isodateformat = "%Y-%m-%d %H:%M:%S"
        date = datetime.strptime(isodate, isodateformat)
        # Take the provided date and make it as if we are starting in UTC
        utc_date = datetime(year=date.year, month=date.month, day=date.day, hour=date.hour, minute=date.minute,
                            second=date.second, tzinfo=timezone.utc)
        return format_datetime(utc_date, True)

    @staticmethod
    def compare_rfc_dates(date1, date2):
        datetime1 = datetime.strptime(date1, TestConstants.RFC_1123_FORMAT)
        datetime2 = datetime.strptime(date2, TestConstants.RFC_1123_FORMAT)
        if datetime1 == datetime2:
            return 0
        elif datetime1 < datetime2:
            return -1
        else:
            return 1

    def assertTitleExists(self, expected, location):
        get_headers = {
            'Accept': TestConstants.JSONLD_MIMETYPE
        }
        response = self.do_get(location, headers=get_headers)
        body = response.content.decode('UTF-8')
        json_body = json.loads(body)
        found_title = pyjq.all('.[] | ."http://purl.org/dc/elements/1.1/title" | .[]."@value"', json_body)
        for title in found_title:
            if title == expected:
                return
        self.fail("Did not find expected title \"{0}\" in response".format(expected))

    def log(self, message):
        print(message)

    def find_binary_description(self, response):
        headers = FedoraTests.get_link_headers(response)
        self.assertIsNotNone(headers['describedby'])
        return headers['describedby'][0]


def Test(func):
    functools.wraps(func)

    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper._istest = True
    return wrapper


def register_tests(cls):
    cls._testdict = []
    for methodname in dir(cls):
        method = getattr(cls, methodname)
        if hasattr(method, '_istest'):
            cls._testdict.append(methodname)
    return cls
