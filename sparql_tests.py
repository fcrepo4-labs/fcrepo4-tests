#!/bin/env python

import TestConstants
from abstract_fedora_tests import FedoraTests, register_tests, Test
import os


@register_tests
class FedoraSparqlTests(FedoraTests):

    # Create test objects all inside here for easy of review
    CONTAINER = "/test_sparql"

    TITLE_SPARQL = "prefix dc: <http://purl.org/dc/elements/1.1/>" \
                   "INSERT { <> dc:title \"First title\". } WHERE {}"

    UPDATE_SPARQL = "prefix dc: <http://purl.org/dc/elements/1.1/> " \
                    "DELETE { <> dc:title ?o . } INSERT { <> dc:title \"Updated title\" .} WHERE { <> dc:title ?o . }"

    def __init__(self, config):
        super().__init__(config)

    @Test
    def doSparqlContainerTest(self):
        self.log("Running doSparqlContainerTest")

        self.log("Create container")
        headers = {
            'Content-type': 'text/turtle'
        }
        r = self.do_post(self.getBaseUri(), headers=headers, body=TestConstants.OBJECT_TTL)
        self.assertEqual(201, r.status_code, "Did not create container")
        location = self.get_location(r)

        self.log("Set dc:title with SPARQL")
        patch_headers = {
            'Content-type': TestConstants.SPARQL_UPDATE_MIMETYPE
        }
        r = self.do_patch(location, headers=patch_headers, body=self.TITLE_SPARQL)
        self.assertEqual(204, r.status_code, "Did not get expected result")
        self.assertTitleExists("First title", location)

        self.log("Update dc:title with SPARQL")
        r = self.do_patch(location, headers=patch_headers, body=self.UPDATE_SPARQL)
        self.assertEqual(204, r.status_code, "Did not get expected results")
        self.assertTitleExists("Updated title", location)

        self.log("Passed")

    @Test
    def doSparqlBinaryTest(self):
        self.log("Running doSparqlBinaryTest")

        self.log("Create a binary")
        headers = {
            'Content-type': 'image/jpeg'
        }
        with open(os.path.join(os.getcwd(), 'resources', 'basic_image.jpg'), 'rb') as fp:
            data = fp.read()
            r = self.do_post(self.getBaseUri(), headers=headers, body=data)
            self.assertEqual(201, r.status_code, "Did not get expected response")
            description = self.find_binary_description(r)

        self.log("Set dc:title with SPARQL")
        patch_headers = {
            'Content-type': TestConstants.SPARQL_UPDATE_MIMETYPE
        }
        r = self.do_patch(description, headers=patch_headers, body=self.TITLE_SPARQL)
        self.assertEqual(204, r.status_code, "Did not get expected result")
        self.assertTitleExists("First title", description)

        self.log("Update dc:title with SPARQL")
        r = self.do_patch(description, headers=patch_headers, body=self.UPDATE_SPARQL)
        self.assertEqual(204, r.status_code, "Did not get expected results")
        self.assertTitleExists("Updated title", description)

        self.log("Passed")

    @Test
    def doUnicodeSparql(self):
        self.log("Running doUnicodeSparql")

        self.log("Create a container")
        r = self.do_post(self.getBaseUri())
        self.assertEqual(201, r.status_code, "Did not get expected response code")
        location = self.get_location(r)

        sparql = "PREFIX dc: <http://purl.org/dc/elements/1.1/> " \
                 "INSERT { <> dc:title \"Die von Blumenbach gegründete anthropologische Sammlung der Universität\" . }" \
                 " WHERE {}".encode('UTF-8')

        self.log("Patching with unicode")
        headers = {
            'Content-type': TestConstants.SPARQL_UPDATE_MIMETYPE
        }
        r = self.do_patch(location, headers=headers, body=sparql)
        self.assertEqual(204, r.status_code, "Did not get expected response code")
        self.assertTitleExists("Die von Blumenbach gegründete anthropologische Sammlung der Universität", location)

        self.log("Passed")