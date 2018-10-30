#!/bin/env python

import TestConstants
from abstract_fedora_tests import FedoraTests, register_tests, Test
import os

@register_tests
class FedoraBasicIxnTests(FedoraTests):

    # Create test objects all inside here for easy of review
    CONTAINER = "/test_nested"

    def __init__(self, config):
        super().__init__(config)

    def run_tests(self):
        self.check_for_retest(self.getBaseUri())
        super().run_tests()
        self.cleanup(self.getBaseUri())

    def testContainer(self, type):
        """ Create a container with type link type """
        link_type = self.make_type(type)
        headers = {
            'Link': link_type
        }
        r = self.do_post(self.getBaseUri(), headers=headers)
        self.assertEqual(201, r.status_code, "Did not create container")
        location = self.get_location(r)
        self.nodes.append(location)
        r = self.do_get(location)
        self.assertEqual(200, r.status_code, "Did not get container")
        self.assertIsNotNone(r.headers['Link'], "Did not get any link headers returned")
        type_headers = FedoraTests.get_link_headers(r)
        self.assertIsNotNone(type_headers['type'], "Did not get any link headers with rel=type")
        self.assertIn(type, type_headers['type'], "Did not find link header for {}".format(type))
        self.log("Passed")

    @Test
    def testBasicContainer(self):
        self.log("Running testBasicContainer")
        self.testContainer(TestConstants.LDP_BASIC)

    @Test
    def testDirectContainer(self):
        self.log("Running testDirectContainer")
        self.testContainer(TestConstants.LDP_DIRECT)

    @Test
    def testIndirectContainer(self):
        self.log("Running testIndirectContainer")
        self.testContainer(TestConstants.LDP_INDIRECT)

    @Test
    def doNestedTests(self):
        self.log("Running doNestedTests")

        object_ttl = "@prefix dc: <http://purl.org/dc/elements/1.1/> ." \
                     "@prefix pcdm: <http://pcdm.org/models#> ." \
                     "<> a pcdm:Object ;" \
                     "dc:title \"An Object\" ."

        self.log("Create a container")
        headers = {
            'Content-type': 'text/turtle'
        }
        r = self.do_post(self.getBaseUri(), headers=headers, body=object_ttl)
        self.assertEqual(201, r.status_code, "Did not get expected status code")
        location = self.get_location(r)

        self.log("Create a container in a container")
        r = self.do_post(location, headers=headers, body=object_ttl)
        self.assertEqual(201, r.status_code, "Did not get expected status code")
        location2 = self.get_location(r)

        self.log("Create binary inside a container inside a container")
        with open(os.path.join(os.getcwd(), 'resources', 'basic_image.jpg'), 'rb') as fp:
            headers = {
                'Content-type': 'image/jpeg'
            }
            data = fp.read()
            r = self.do_post(location2, headers=headers, body=data)
            self.assertEqual(201, r.status_code, "Did not get expected status code")
            binary_location = self.get_location(r)

        self.log("Delete binary")
        r = self.do_delete(binary_location)
        self.assertEqual(204, r.status_code, "Did not get expected status code")

        self.log("Verify its gone")
        r = self.do_get(binary_location)
        self.assertEqual(410, r.status_code, "Did not get expected status code")

        self.log("Delete container with a container inside it")
        r = self.do_delete(location)
        self.assertEqual(204, r.status_code, "Did not get expected status code")

        self.log("Verify both are gone")
        r = self.do_get(location2)
        self.assertEqual(410, r.status_code, "Did not get expected status code")
        r = self.do_get(location)
        self.assertEqual(410, r.status_code, "Did not get expected status code")

        self.log("Passed")