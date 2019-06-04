#!/bin/env python

import TestConstants
from abstract_fedora_tests import FedoraTests, register_tests, Test
import random
import uuid


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
                "acl:mode acl:Read, acl:Write;" \
                "acl:agent \"{1}\" ."

    def verifyAuthEnabled(self):
        self.log("Checking that authZ is enabled")
        lst = [random.choice('0123456789abcdef') for n in range(16)]
        random_string = "".join(lst)

        temp_auth = FedoraTests.create_auth(random_string, random_string)
        r = self.do_get(self.getFedoraBase(), admin=temp_auth)
        self.assertEqual(401, r.status_code, "Did not get expected response code")

    def getAclUri(self, response):
        acls = FedoraAuthzTests.get_link_headers(response)
        self.assertIsNotNone(acls['acl'])
        return acls['acl'][0]

    @Test
    def doAuthTests(self):
        self.verifyAuthEnabled()

        self.log("Create \"cover\" container")
        r = self.do_put(self.getBaseUri() + "/cover")
        self.assertEqual(201, r.status_code, "Did not get expected response code")
        cover_location = FedoraAuthzTests.get_location(r)
        cover_acl = self.getAclUri(r)

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
        files_location = FedoraAuthzTests.get_location(r)
        files_acl = self.getAclUri(r)

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

    @Test
    def doDirectIndirectAuthTests(self):
        self.verifyAuthEnabled()

        self.log("Create a target container")
        r = self.do_post()
        self.assertEqual(201, r.status_code, "Did not get expected response code")
        target_location = FedoraAuthzTests.get_location(r)
        target_acl = self.getAclUri(r)

        self.log("Create a write container")
        r = self.do_post()
        self.assertEqual(201, r.status_code, "Did not get expected response code")
        write_location = FedoraAuthzTests.get_location(r)
        write_acl = self.getAclUri(r)

        self.log("Make sure the /target resource is readonly")
        target_ttl = "@prefix acl: <http://www.w3.org/ns/auth/acl#> .\n"\
                     "<#readauthz> a acl:Authorization ;\n" \
                     "  acl:agent \"{0}\" ;\n" \
                     "  acl:mode acl:Read ;\n" \
                     "  acl:accessTo <{1}> .\n".format(self.config[TestConstants.USER_NAME_PARAM], target_location)
        headers = {
            'Content-type': 'text/turtle'
        }
        r = self.do_put(target_acl, headers=headers, body=target_ttl)
        self.assertEqual(201, r.status_code, "Did not get expected response code")

        self.log("Make sure the write resource is writable by \"{0}\"".format(self.config[TestConstants.USER_NAME_PARAM]))
        write_ttl = "@prefix acl: <http://www.w3.org/ns/auth/acl#> .\n" \
                    "<#writeauth> a acl:Authorization ;\n" \
                    "   acl:agent \"{0}\" ;\n" \
                    "   acl:mode acl:Read, acl:Write ;\n" \
                    "   acl:accessTo <{1}> ;\n" \
                    "   acl:default <{1}> .\n".format(self.config[TestConstants.USER_NAME_PARAM], write_location)
        r = self.do_put(write_acl, headers=headers, body=write_ttl)
        self.assertEqual(201, r.status_code, "Did not get expected response code")

        self.log("Verify that \"{0}\" can create a simple resource under write resource (POST)".format(self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_post(write_location, admin=False)
        self.assertEqual(201, r.status_code, "Did not get expected response code")

        uuid_value = str(uuid.uuid4())
        self.log("Verify that \"{0}\" can create a simple resource under write resource (PUT)".format(
            self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_put(write_location + "/" + uuid_value, admin=False)
        self.assertEqual(201, r.status_code, "Did not get expected response code")

        self.log("Verify that \"{0}\" CANNOT create a resource under target resource".format(self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_post(target_location, admin=False)
        self.assertEqual(403, r.status_code, "Did not get expected response code")

        self.log("Verify that \"{0}\" CANNOT create direct or indirect containers that reference target resources".format(self.config[TestConstants.USER_NAME_PARAM]))
        headers = {
            'Content-type': 'text/turtle',
            'Link': self.make_type(TestConstants.LDP_DIRECT)
        }
        direct_ttl = "@prefix ldp: <http://www.w3.org/ns/ldp#> .\n" \
                     "@prefix test: <http://example.org/test#> .\n" \
                     "<>  ldp:membershipResource <{0}> ;\n" \
                     "ldp:hasMemberRelation test:predicateToCreate .\n".format(target_location)
        r = self.do_post(write_location, headers=headers, body=direct_ttl, admin=False)
        self.assertEqual(403, r.status_code, "Did not get expected response code")

        headers = {
            'Content-type': 'text/turtle',
            'Link': self.make_type(TestConstants.LDP_INDIRECT)
        }
        indirect_ttl = "@prefix ldp: <http://www.w3.org/ns/ldp#> .\n" \
                       "@prefix test: <http://example.org/test#> .\n" \
                       "<> ldp:insertedContentRelation test:something ;\n" \
                       "ldp:membershipResource <{0}> ;\n" \
                       "ldp:hasMemberRelation test:predicateToCreate .\n".format(target_location)
        r = self.do_post(write_location, headers=headers, body=indirect_ttl, admin=False)
        self.assertEqual(403, r.status_code, "Did not get expected response code")

        self.log("Go ahead and create the indirect and direct containers as admin")
        r = self.do_post(write_location, headers=headers, body=direct_ttl)
        self.assertEqual(201, r.status_code, "Did not get expected response code")
        direct_location = self.get_location(r)
        r = self.do_post(write_location, headers=headers, body=indirect_ttl)
        self.assertEqual(201, r.status_code, "Did not get expected response code")
        indirect_location = self.get_location(r)

        self.log("Attempt to verify that \"{0}\" can not actually create relationships on the readonly resource via " \
                 "direct or indirect container".format(self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_post(direct_location, admin=False)
        self.assertEqual(403, r.status_code, "Did not get expected status code")
        r = self.do_post(indirect_location, admin=False)
        self.assertEqual(403, r.status_code, "Did not get expected status code")

        self.log("Verify that \"{0}\" can still create a simple resource under write resource (POST)".format(self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_post(write_location, admin=False)
        self.assertEqual(201, r.status_code, "Did not get expected response code")

        uuid_value = str(uuid.uuid4())
        self.log("Verify that \"{0}\" can still create a simple resource under write resource (PUT)".format(
            self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_put(write_location + "/" + uuid_value, admin=False)
        self.assertEqual(201, r.status_code, "Did not get expected response code")

    @Test
    def multipleAuthzCreatePermissiveSet(self):
        self.verifyAuthEnabled()

        self.log("Create a target container")
        r = self.do_post()
        self.assertEqual(201, r.status_code, "Did not get expected response code")
        target_location = FedoraAuthzTests.get_location(r)
        target_acl = self.getAclUri(r)

        double_ttl = "@prefix acl: <http://www.w3.org/ns/auth/acl#> .\n" \
                     "<#readonly> a acl:Authorization ;\n" \
                     "   acl:agent \"{0}\" ;\n" \
                     "   acl:mode acl:Read ;\n" \
                     "   acl:accessTo <{1}> .\n" \
                     "<#readwrite> a acl:Authorization ;\n" \
                     "   acl:agent \"{0}\" ;\n" \
                     "   acl:mode acl:Write ;\n" \
                     "   acl:accessTo <{1}> .\n".format(self.config[TestConstants.USER_NAME_PARAM], target_location)
        headers = {
            'Content-type': TestConstants.TURTLE_MIMETYPE
        }

        self.log("Add ACL with one read and one read/write authz.")
        r = self.do_put(target_acl, headers=headers, body=double_ttl)
        self.assertEqual(201, r.status_code, "Did not get expected response code")

        self.log("Check we can read")
        r = self.do_get(target_location, admin=False)
        self.assertEqual(200, r.status_code, "Did not get expected response code")

        self.log("Check we can write")
        headers = {
            'Content-type': TestConstants.SPARQL_UPDATE_MIMETYPE
        }
        body = "prefix dc: <http://purl.org/dc/elements/1.1/> INSERT { <> dc:title \"A new title\" } WHERE {}"
        r = self.do_patch(target_location, headers=headers, body=body)
        self.assertEqual(204, r.status_code, "Did not get expected response code")
