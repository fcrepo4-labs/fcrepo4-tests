#!/bin/env python

import TestConstants
from abstract_fedora_tests import FedoraTests, register_tests, Test
import random


@register_tests
class FedoraAuthzTests(FedoraTests):

    # Create test objects all inside here for easy of review
    CONTAINER = "/test_authz"

    COVER_ACL = "@prefix acl: <http://www.w3.org/ns/auth/acl#> .\n" \
                "@prefix pcdm: <http://pcdm.org/models#> .\n" \
                "<#writeauth> a acl:Authorization ;" \
                "acl:accessToClass pcdm:Object ;" \
                "acl:mode acl:Read, acl:Write;" \
                "acl:agent \"{0}\" ."

    def __init__(self, config):
        super().__init__(config)

    def run_tests(self):
        self.check_for_retest(self.getBaseUri())
        super().run_tests()
        self.cleanup(self.getBaseUri())

    @Test
    def doAuthTests(self):
        self.log("Running doAuthTests")

        self.log("Checking that authZ is enabled")
        lst = [random.choice('0123456789abcdef') for n in range(16)]
        random_string = "".join(lst)

        temp_auth = FedoraTests.create_auth(random_string, random_string)
        r = self.do_get(self.getFedoraBase(), auth=temp_auth)
        self.assertEqual(401, r.status_code, "Did not get expected response code")

        self.log("Create \"cover\" container")
        r = self.do_put(self.getBaseUri() + "/cover")
        self.assertEqual(201, r.status_code, "Did not get expected response code")
        cover_location = self.get_location(r)
        cover_acl = self.get_link_headers(r)
        self.assertIsNotNone(cover_acl['acl'])
        cover_acl = cover_acl['acl'][0]

        self.log("Make \"cover\" a pcdm:Object")
        sparql = "PREFIX pcdm: <http://pcdm.org/models#>" \
                 "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>" \
                 "INSERT { <> rdf:type pcdm:Object } WHERE { }"
        headers = {
            'Content-type': TestConstants.SPARQL_UPDATE_MIMETYPE
        }
        r = self.do_patch(cover_location, headers=headers, body=sparql)
        self.assertEqual(204, r.status_code, "Did not get expected response code")

        self.log("Verify no current ACL")
        r = self.do_get(cover_acl)
        self.assertEqual(404, r.status_code, "Did not get expected response code")

        self.log("Add ACL to \"cover\"")
        headers = {
            'Content-type': 'text/turtle'
        }
        r = self.do_put(cover_acl, headers=headers,
                        body=self.COVER_ACL.format(self.config[TestConstants.USER_NAME_PARAM]))
        self.assertEqual(201, r.status_code, "Did not get expected response code")

        self.log("Create \"files\" inside \"cover\"")
        r = self.do_put(cover_location + "/files")
        self.assertEqual(201, r.status_code, "Did not get expected response code")

        self.log("verifyAuthZ")
        self.log("Anonymous can't access \"cover\"")
        r = self.do_get(cover_location, auth='anonymous')
        self.assertEqual(401, r.status_code, "Did not get expected response code")

        self.log("{0} can access \"cover\"".format(self.config[TestConstants.ADMIN_USER_PARAM]))
        r = self.do_get(cover_location)
        self.assertEqual(200, r.status_code, "Did not get expected response code")

        self.log("{0} can access \"cover\"".format(self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_get(cover_location, admin=False)
        self.assertEqual(200, r.status_code, "Did not get expected response code")

        self.log("{0} can't access \"cover\"".format(self.config[TestConstants.USER2_NAME_PARAM]))
        auth = self.create_auth(self.config[TestConstants.USER2_NAME_PARAM], self.config[TestConstants.USER2_PASS_PARAM])
        r = self.do_get(cover_location, auth=auth)
        self.assertEqual(403, r.status_code, "Did not get expected response code")

        self.log("Passed")
