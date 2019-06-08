#!/bin/env python

import TestConstants
from abstract_fedora_tests import FedoraTests, register_tests, Test
import os


@register_tests
class FedoraBasicIxnTests(FedoraTests):

    # Create test objects all inside here for easy of review
    CONTAINER = "/test_nested"

    def createTestResource(self, type, files=None):
        """ Create a container with an expected type link type and return the URI """
        link_type = self.make_type(type)
        headers = {
            'Link': link_type
        }
        r = self.do_post(self.getBaseUri(), headers=headers, files=files)
        self.assertEqual(201, r.status_code, "Did not create container")
        location = self.get_location(r)
        self.nodes.append(location)
        r = self.do_get(location)
        self.assertEqual(200, r.status_code, "Did not get container")
        self.assertIsNotNone(r.headers['Link'], "Did not get any link headers returned")
        type_headers = FedoraTests.get_link_headers(r)
        self.assertIsNotNone(type_headers['type'], "Did not get any link headers with rel=type")
        self.assertIn(type, type_headers['type'], "Did not find link header for {}".format(type))
        return location

    @Test
    def testBasicContainer(self):
        self.createTestResource(TestConstants.LDP_BASIC)

    @Test
    def testDirectContainer(self):
        self.createTestResource(TestConstants.LDP_DIRECT)

    @Test
    def testIndirectContainer(self):
        self.createTestResource(TestConstants.LDP_INDIRECT)

    @Test
    def testNonRdfSource(self):
        testfiles = {'files': ('testdata.csv', 'this,is,some,data\n')}
        self.createTestResource(TestConstants.LDP_NON_RDF_SOURCE, files=testfiles)

    @Test
    def testLdpResource(self):
        """ We don't allow you to create a ldp:Resource so this returns 400 Bad Request """
        link_type = self.make_type(TestConstants.LDP_RESOURCE)
        headers = {
            'Link': link_type
        }
        r = self.do_post(self.getBaseUri(), headers=headers)
        self.assertEqual(400, r.status_code, "Did not get expected response")

    @Test
    def testLdpContainer(self):
        """ We don't allow you to create a ldp:Container so this returns 400 Bad Request """
        link_type = self.make_type(TestConstants.LDP_CONTAINER)
        headers = {
            'Link': link_type
        }
        r = self.do_post(self.getBaseUri(), headers=headers)
        self.assertEqual(400, r.status_code, "Did create container")

    @Test
    def doNestedTests(self):
        self.log("Create a container")
        headers = {
            'Content-type': 'text/turtle'
        }
        r = self.do_post(self.getBaseUri(), headers=headers, body=TestConstants.OBJECT_TTL)
        self.assertEqual(201, r.status_code, "Did not get expected status code")
        location = self.get_location(r)

        self.log("Create a container in a container")
        r = self.do_post(location, headers=headers, body=TestConstants.OBJECT_TTL)
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

    def changeIxnModels(self, location, starting_model):
        """ This function uses a created object at {location} with starting type {starting_model}.
            The below dictionary of tuples works as such
            expected_ixn_change = {
                <Initial Model>: [
                    (<Model to change to>, <expected response status code>),
            """
        expected_ixn_change = {
            TestConstants.LDP_BASIC: [
                (TestConstants.LDP_INDIRECT, 409),
                (TestConstants.LDP_DIRECT, 409),
                (TestConstants.LDP_NON_RDF_SOURCE, 409),
                (TestConstants.LDP_RESOURCE, 400),
                (TestConstants.LDP_CONTAINER, 400)
            ],
            TestConstants.LDP_DIRECT: [
                (TestConstants.LDP_BASIC, 409),
                (TestConstants.LDP_INDIRECT, 409),
                (TestConstants.LDP_NON_RDF_SOURCE, 409),
                (TestConstants.LDP_RESOURCE, 400),
                (TestConstants.LDP_CONTAINER, 400)
            ],
            TestConstants.LDP_INDIRECT: [
                (TestConstants.LDP_BASIC, 409),
                (TestConstants.LDP_DIRECT, 409),
                (TestConstants.LDP_NON_RDF_SOURCE, 409),
                (TestConstants.LDP_RESOURCE, 400),
                (TestConstants.LDP_CONTAINER, 400)
            ],
            TestConstants.LDP_NON_RDF_SOURCE: [
                (TestConstants.LDP_BASIC, 409),
                (TestConstants.LDP_DIRECT, 409),
                (TestConstants.LDP_INDIRECT, 409),
                (TestConstants.LDP_RESOURCE, 400),
                (TestConstants.LDP_CONTAINER, 400)
            ]
        }
        for model, result in expected_ixn_change[starting_model]:
            self.log("Changing from {0} to {1} expect status {2}".format(starting_model, model, result))

            if model == TestConstants.LDP_NON_RDF_SOURCE:
                files = {'file': ('testcsvdata.csv', 'this,is,changed,data\nnow,go,away,please\n')}
            else:
                files = None

            headers = {
                'Link': self.make_type(model)
            }

            r = self.do_put(location, headers=headers, files=files)
            self.assertEqual(result, r.status_code, "Did not get expected response")

    @Test
    def testChangeIxnModel(self):
        self.log("Create a basic container")
        basic = self.createTestResource(TestConstants.LDP_BASIC)
        self.changeIxnModels(basic, TestConstants.LDP_BASIC)

        self.log("Create a direct container")
        direct = self.createTestResource(TestConstants.LDP_DIRECT)
        self.changeIxnModels(direct, TestConstants.LDP_DIRECT)

        self.log("Create a indirect container")
        indirect = self.createTestResource(TestConstants.LDP_INDIRECT)
        self.changeIxnModels(indirect, TestConstants.LDP_INDIRECT)

        self.log("Create a Non Rdf Source")
        testfiles = {'files': ('testdata.csv', 'this,is,some,data\n')}
        non_rdf = self.createTestResource(TestConstants.LDP_NON_RDF_SOURCE, files=testfiles)
        self.changeIxnModels(non_rdf, TestConstants.LDP_NON_RDF_SOURCE)
