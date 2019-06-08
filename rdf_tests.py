#!/bin/env python

import TestConstants
from abstract_fedora_tests import FedoraTests, register_tests, Test


@register_tests
class FedoraRdfTests(FedoraTests):

    # Create test objects all inside here for easy of review
    CONTAINER = "/test_rdf"

    RDF_VARIANTS = [
        "text/turtle;charset=utf-8",
        "application/rdf+xml;charset=utf-8",
        "application/ld+json;charset=utf-8",
        "application/n-triples;charset=utf-8",
        "text/n3;charset=utf-8"
    ]

    @Test
    def testRdfSerialization(self):
        self.log("Put new resource.")
        headers = {
            "Content-type": "text/turtle"
        }
        r = self.do_post(self.getBaseUri(), headers=headers, body=TestConstants.OBJECT_TTL)
        self.assertEqual(201, r.status_code, "Did not create new object")
        location = self.get_location(r)

        self.log("Check for correct title.")
        self.assertTitleExists("An Object", location)

        self.log("PUT to update title.")
        n_triples = "<{0}> <http://purl.org/dc/elements/1.1/title> \"Updated Title\" .".format(location)
        headers = {
            "Content-type": "application/n-triples",
            "Prefer": TestConstants.PUT_PREFER_LENIENT
        }
        r = self.do_put(location, headers=headers, body=n_triples)
        self.assertEqual(204, r.status_code, "Did not update the resource")

        self.log("Check updated title.")
        self.assertTitleExists("Updated Title", location)

        self.log("Test RDF variants.")
        for MIME in self.RDF_VARIANTS:
            self.log("Testing {0}".format(MIME))
            headers = {
                'Accept': MIME
            }
            r = self.do_get(location, headers=headers)
            self.assertEqual(200, r.status_code, "Unable to get resource")
            self.assertIsNotNone(r.headers['Content-type'], "No content-type defined")
            self.assertEqual(MIME, r.headers['Content-type'], "Did not get expected content type")

        self.log("Delete object")
        r = self.do_delete(location)
        self.assertEqual(204, r.status_code, "Did not delete object")

        self.log("Test for tombstone")
        r = self.do_get(location)
        self.assertEqual(410, r.status_code, "Object's tombstone not found.")
