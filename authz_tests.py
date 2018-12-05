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
                "acl:default <{0}>; " \
                "acl:agent \"{1}\" ."

    FILES_ACL = "@prefix acl: <http://www.w3.org/ns/auth/acl#> .\n" \
                "@prefix pcdm: <http://pcdm.org/models#> .\n" \
                "<#writeauth> a acl:Authorization ;" \
                "acl:accessTo <{0}> ;" \
                "acl:mode acl:Read, acl:Write;"

    @Test
    def doAuthTests(self):
        self.log("Running doAuthTests")

        self.log("Checking that authZ is enabled")
        lst = [random.choice('0123456789abcdef') for n in range(16)]
        random_string = "".join(lst)

        temp_auth = FedoraTests.create_auth(random_string, random_string)
        r = self.do_get(self.getFedoraBase(), admin=temp_auth)
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
        body = self.COVER_ACL.format(cover_location, self.config[TestConstants.USER_NAME_PARAM])
        r = self.do_put(cover_acl, headers=headers, body=body)
        self.assertEqual(201, r.status_code, "Did not get expected response code")

        self.log("Create \"files\" inside \"cover\"")
        r = self.do_put(cover_location + "/files")
        self.assertEqual(201, r.status_code, "Did not get expected response code")
        files_location = self.get_location(r)
        files_acl = self.get_link_headers(r)
        self.assertIsNotNone(files_acl['acl'])
        files_acl = files_acl['acl'][0]

        self.log("Anonymous can't access \"cover\"")
        r = self.do_get(cover_location, admin=None)
        self.assertEqual(401, r.status_code, "Did not get expected response code")

        self.log("Anonymous can't access \"cover/files\"")
        r = self.do_get(files_location, admin=None)
        self.assertEqual(401, r.status_code, "Did not get expected response code")

        self.log("{0} can access \"cover\"".format(self.config[TestConstants.ADMIN_USER_PARAM]))
        r = self.do_get(cover_location)
        self.assertEqual(200, r.status_code, "Did not get expected response code")

        self.log("{0} can access \"cover/files\"".format(self.config[TestConstants.ADMIN_USER_PARAM]))
        r = self.do_get(files_location)
        self.assertEqual(200, r.status_code, "Did not get expected response code")

        self.log("{0} can access \"cover\"".format(self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_get(cover_location, admin=False)
        self.assertEqual(200, r.status_code, "Did not get expected response code")

        self.log("{0} can access \"cover/files\"".format(self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_get(files_location, admin=False)
        self.assertEqual(200, r.status_code, "Did not get expected response code")

        auth = self.create_auth(self.config[TestConstants.USER2_NAME_PARAM],
                                self.config[TestConstants.USER2_PASS_PARAM])
        self.log("{0} can't access \"cover\"".format(self.config[TestConstants.USER2_NAME_PARAM]))
        r = self.do_get(cover_location, admin=auth)
        self.assertEqual(403, r.status_code, "Did not get expected response code")

        self.log("{0} can't access \"cover/files\"".format(self.config[TestConstants.USER2_NAME_PARAM]))
        r = self.do_get(files_location, admin=auth)
        self.assertEqual(403, r.status_code, "Did not get expected response code")

        self.log("Verify \"cover/files\" has no ACL")
        r = self.do_get(files_acl)
        self.assertEqual(404, r.status_code, "Did not get expected response code")

        self.log("PUT Acl to \"cover/files\" to allow access for {0}".format(self.config[TestConstants.USER2_NAME_PARAM]))
        headers = {
            'Content-type': 'text/turtle'
        }
        body = self.FILES_ACL.format(files_location, self.config[TestConstants.USER2_NAME_PARAM])
        r = self.do_put(files_acl, headers=headers, body=body)
        self.assertEqual(201, r.status_code, "Did not get expected response code")

        self.log("{0} can't access \"cover\"".format(self.config[TestConstants.USER2_NAME_PARAM]))
        r = self.do_get(cover_location, admin=auth)
        self.assertEqual(403, r.status_code, "Did not get expected response code")

        self.log("{0} can access \"cover/files\"".format(self.config[TestConstants.USER2_NAME_PARAM]))
        r = self.do_get(files_location, admin=auth)
        self.assertEqual(200, r.status_code, "Did not get expected response code")

        self.log("Passed")
