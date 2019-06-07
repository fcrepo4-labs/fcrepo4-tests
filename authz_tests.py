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
        if 401 != r.status_code:
            self.log("It appears that authentication is not enabled on your repository.")
            quit()

    @staticmethod
    def getAclUri(response):
        acls = FedoraAuthzTests.get_link_headers(response)
        try:
            return acls['acl'][0]
        except KeyError:
            Exception("No acl link header found")

    @Test
    def doAuthTests(self):
        self.verifyAuthEnabled()

        self.log("Create \"cover\" container")
        r = self.do_put(self.getBaseUri() + "/cover")
        self.checkResponse(201, r)
        cover_location = self.get_location(r)
        cover_acl = FedoraAuthzTests.getAclUri(r)

        self.log("Make \"cover\" a pcdm:Object")
        sparql = "PREFIX pcdm: <http://pcdm.org/models#>" \
                 "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>" \
                 "INSERT { <> rdf:type pcdm:Object } WHERE { }"
        headers = {
            'Content-type': TestConstants.SPARQL_UPDATE_MIMETYPE
        }
        r = self.do_patch(cover_location, headers=headers, body=sparql)
        self.checkResponse(204, r)

        self.log("Verify no current ACL")
        r = self.do_get(cover_acl)
        self.checkResponse(404, r)

        self.log("Add ACL to \"cover\"")
        headers = {
            'Content-type': 'text/turtle'
        }
        body = self.COVER_ACL.format(cover_location, self.config[TestConstants.USER_NAME_PARAM])
        r = self.do_put(cover_acl, headers=headers, body=body)
        self.checkResponse(201, r)

        self.log("Create \"files\" inside \"cover\"")
        r = self.do_put(cover_location + "/files")
        self.checkResponse(201, r)
        files_location = self.get_location(r)
        files_acl = FedoraAuthzTests.getAclUri(r)

        self.log("Anonymous can't access \"cover\"")
        r = self.do_get(cover_location, admin=None)
        self.checkResponse(401, r)

        self.log("Anonymous can't access \"cover/files\"")
        r = self.do_get(files_location, admin=None)
        self.checkResponse(401, r)

        self.log("{0} can access \"cover\"".format(self.config[TestConstants.ADMIN_USER_PARAM]))
        r = self.do_get(cover_location)
        self.checkResponse(200, r)

        self.log("{0} can access \"cover/files\"".format(self.config[TestConstants.ADMIN_USER_PARAM]))
        r = self.do_get(files_location)
        self.checkResponse(200, r)

        self.log("{0} can access \"cover\"".format(self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_get(cover_location, admin=False)
        self.checkResponse(200, r)

        self.log("{0} can access \"cover/files\"".format(self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_get(files_location, admin=False)
        self.checkResponse(200, r)

        auth = self.create_auth(self.config[TestConstants.USER2_NAME_PARAM],
                                self.config[TestConstants.USER2_PASS_PARAM])
        self.log("{0} can't access \"cover\"".format(self.config[TestConstants.USER2_NAME_PARAM]))
        r = self.do_get(cover_location, admin=auth)
        self.checkResponse(403, r)

        self.log("{0} can't access \"cover/files\"".format(self.config[TestConstants.USER2_NAME_PARAM]))
        r = self.do_get(files_location, admin=auth)
        self.checkResponse(403, r)

        self.log("Verify \"cover/files\" has no ACL")
        r = self.do_get(files_acl)
        self.checkResponse(404, r)

        self.log("PUT Acl to \"cover/files\" to allow access for {0}".format(self.config[TestConstants.USER2_NAME_PARAM]))
        headers = {
            'Content-type': 'text/turtle'
        }
        body = self.FILES_ACL.format(files_location, self.config[TestConstants.USER2_NAME_PARAM])
        r = self.do_put(files_acl, headers=headers, body=body)
        self.checkResponse(201, r)

        self.log("{0} can't access \"cover\"".format(self.config[TestConstants.USER2_NAME_PARAM]))
        r = self.do_get(cover_location, admin=auth)
        self.checkResponse(403, r)

        self.log("{0} can access \"cover/files\"".format(self.config[TestConstants.USER2_NAME_PARAM]))
        r = self.do_get(files_location, admin=auth)
        self.checkResponse(200, r)

    @Test
    def doDirectIndirectAuthTests(self):
        self.verifyAuthEnabled()

        self.log("Create a target container")
        r = self.do_post()
        self.checkResponse(201, r)
        target_location = self.get_location(r)
        target_acl = FedoraAuthzTests.getAclUri(r)

        self.log("Create a write container")
        r = self.do_post()
        self.checkResponse(201, r)
        write_location = self.get_location(r)
        write_acl = FedoraAuthzTests.getAclUri(r)

        self.log("Make sure the /target resource is readonly")
        target_ttl = "@prefix acl: <{2}> .\n"\
                     "<#readauthz> a acl:Authorization ;\n" \
                     "  acl:agent \"{0}\" ;\n" \
                     "  acl:mode acl:Read ;\n" \
                     "  acl:accessTo <{1}> .\n".format(self.config[TestConstants.USER_NAME_PARAM], target_location,
                                                       TestConstants.ACL_NS)
        headers = {
            'Content-type': 'text/turtle'
        }
        r = self.do_put(target_acl, headers=headers, body=target_ttl)
        self.checkResponse(201, r)

        self.log("Make sure the write resource is writable by \"{0}\"".format(self.config[TestConstants.USER_NAME_PARAM]))
        write_ttl = "@prefix acl: <{2}> .\n" \
                    "<#writeauth> a acl:Authorization ;\n" \
                    "   acl:agent \"{0}\" ;\n" \
                    "   acl:mode acl:Read, acl:Write ;\n" \
                    "   acl:accessTo <{1}> ;\n" \
                    "   acl:default <{1}> .\n".format(self.config[TestConstants.USER_NAME_PARAM], write_location,
                                                      TestConstants.ACL_NS)
        r = self.do_put(write_acl, headers=headers, body=write_ttl)
        self.checkResponse(201, r)

        self.log("Verify that \"{0}\" can create a simple resource under write resource (POST)".format(self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_post(write_location, admin=False)
        self.checkResponse(201, r)

        uuid_value = str(uuid.uuid4())
        self.log("Verify that \"{0}\" can create a simple resource under write resource (PUT)".format(
            self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_put(write_location + "/" + uuid_value, admin=False)
        self.checkResponse(201, r)

        self.log("Verify that \"{0}\" CANNOT create a resource under target resource".format(self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_post(target_location, admin=False)
        self.checkResponse(403, r)

        self.log("Verify that \"{0}\" CANNOT create direct or indirect containers that reference target resources".format(self.config[TestConstants.USER_NAME_PARAM]))
        headers = {
            'Content-type': 'text/turtle',
            'Link': self.make_type(TestConstants.LDP_DIRECT)
        }
        direct_ttl = "@prefix ldp: <{0}> .\n" \
                     "@prefix test: <http://example.org/test#> .\n" \
                     "<>  ldp:membershipResource <{1}> ;\n" \
                     "ldp:hasMemberRelation test:predicateToCreate .\n".format(TestConstants.LDP_NS, target_location)
        r = self.do_post(write_location, headers=headers, body=direct_ttl, admin=False)
        self.checkResponse(403, r)

        headers = {
            'Content-type': 'text/turtle',
            'Link': self.make_type(TestConstants.LDP_INDIRECT)
        }
        indirect_ttl = "@prefix ldp: <{0}> .\n" \
                       "@prefix test: <http://example.org/test#> .\n" \
                       "<> ldp:insertedContentRelation test:something ;\n" \
                       "ldp:membershipResource <{1}> ;\n" \
                       "ldp:hasMemberRelation test:predicateToCreate .\n".format(TestConstants.LDP_NS, target_location)
        r = self.do_post(write_location, headers=headers, body=indirect_ttl, admin=False)
        self.checkResponse(403, r)

        self.log("Go ahead and create the indirect and direct containers as admin")
        r = self.do_post(write_location, headers=headers, body=direct_ttl)
        self.checkResponse(201, r)
        direct_location = self.get_location(r)
        r = self.do_post(write_location, headers=headers, body=indirect_ttl)
        self.checkResponse(201, r)
        indirect_location = self.get_location(r)

        self.log("Attempt to verify that \"{0}\" can not actually create relationships on the readonly resource via " \
                 "direct or indirect container".format(self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_post(direct_location, admin=False)
        self.assertEqual(403, r.status_code, "Did not get expected status code")
        r = self.do_post(indirect_location, admin=False)
        self.assertEqual(403, r.status_code, "Did not get expected status code")

        self.log("Verify that \"{0}\" can still create a simple resource under write resource (POST)".format(self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_post(write_location, admin=False)
        self.checkResponse(201, r)

        uuid_value = str(uuid.uuid4())
        self.log("Verify that \"{0}\" can still create a simple resource under write resource (PUT)".format(
            self.config[TestConstants.USER_NAME_PARAM]))
        r = self.do_put(write_location + "/" + uuid_value, admin=False)
        self.checkResponse(201, r)

    @Test
    def multipleAuthzCreatePermissiveSet(self):
        self.verifyAuthEnabled()

        self.log("Create a target container")
        r = self.do_post()
        self.checkResponse(201, r)
        target_location = self.get_location(r)
        target_acl = FedoraAuthzTests.getAclUri(r)

        double_ttl = "@prefix acl: <{2}> .\n" \
                     "<#readonly> a acl:Authorization ;\n" \
                     "   acl:agent \"{0}\" ;\n" \
                     "   acl:mode acl:Read ;\n" \
                     "   acl:accessTo <{1}> .\n" \
                     "<#readwrite> a acl:Authorization ;\n" \
                     "   acl:agent \"{0}\" ;\n" \
                     "   acl:mode acl:Write ;\n" \
                     "   acl:accessTo <{1}> .\n".format(self.config[TestConstants.USER_NAME_PARAM], target_location,
                                                        TestConstants.ACL_NS)
        headers = {
            'Content-type': TestConstants.TURTLE_MIMETYPE
        }

        self.log("Add ACL with one read and one write authz for the same URI.")
        r = self.do_put(target_acl, headers=headers, body=double_ttl)
        self.checkResponse(201, r)

        self.log("Check we can read")
        r = self.do_get(target_location, admin=False)
        self.checkResponse(200, r)

        self.log("Check we can write")
        headers = {
            'Content-type': TestConstants.SPARQL_UPDATE_MIMETYPE
        }
        body = "prefix dc: <{0}> INSERT {{ <> dc:title \"A new title\" }} WHERE {{}}".format(TestConstants.PURL_NS)
        r = self.do_patch(target_location, headers=headers, body=body)
        self.checkResponse(204, r)

    @Test
    def testAllThingsPointTogether(self):
        self.verifyAuthEnabled()

        self.log("Create a target binary")
        headers = {
            'Content-type': 'text/plain',
            'Link': self.make_type(TestConstants.LDP_NON_RDF_SOURCE)
        }
        r = self.do_post(headers=headers, body="this is a test payload")
        self.checkResponse(201, r)
        binary_location = self.get_location(r)
        expected_acl = binary_location + "/fcr:acl"
        acl_location = FedoraAuthzTests.getAclUri(r)
        binary_description = self.find_binary_description(r)

        self.assertNotEqual(binary_location, binary_description)

        self.log("Check binary's acl link header is correct.")
        self.checkValue(expected_acl, acl_location)

        self.log("Check binary description's acl link header is correct")

        r = self.do_get(binary_location)
        self.checkResponse(200, r)
        acl_location = FedoraAuthzTests.getAclUri(r)
        self.checkValue(expected_acl, acl_location)

        self.log("Check binary timemap's acl link header is correct.")
        binary_versions = binary_location + "/fcr:versions"
        r = self.do_get(binary_versions)
        self.checkResponse(200, r)
        acl_location = FedoraAuthzTests.getAclUri(r)
        self.checkValue(expected_acl, acl_location)

        self.log("Create a version of binary")
        r = self.do_post(parent=binary_versions)
        self.checkResponse(201, r)
        memento_location = self.get_location(r)

        self.log("Check memento's acl link header is correct")
        r = self.do_get(memento_location)
        self.checkResponse(200, r)
        acl_location = FedoraAuthzTests.getAclUri(r)
        self.checkValue(expected_acl, acl_location)

        self.log("Check binary description timemap's acl link header is correct.")
        binary_metadata_versions = binary_description + "/fcr:versions"
        r = self.do_get(binary_metadata_versions)
        self.checkResponse(200, r)
        acl_location = FedoraAuthzTests.getAclUri(r)
        self.checkValue(expected_acl, acl_location)

        # metadata version is same datetime, so create it.
        metadata_memento_location = binary_metadata_versions + memento_location[memento_location.rfind('/'):]

        self.log("Check metadata memento's acl link header is correct")
        r = self.do_get(metadata_memento_location)
        self.checkResponse(200, r)
        acl_location = FedoraAuthzTests.getAclUri(r)
        self.checkValue(expected_acl, acl_location)

        self.log("Try to get the ACL")
        r = self.do_get(acl_location)
        self.checkResponse(404, r)

    @Test
    def binaryAndMetadataShareACL(self):
        self.verifyAuthEnabled()

        self.log("Create a target binary")
        headers = {
            'Content-type': 'text/plain',
            'Link': self.make_type(TestConstants.LDP_NON_RDF_SOURCE)
        }
        r = self.do_post(headers=headers, body="this is a test payload")
        self.checkResponse(201, r)
        binary_location = self.get_location(r)
        acl_location = FedoraAuthzTests.getAclUri(r)
        binary_description = self.find_binary_description(r)

        self.log("Add ACL allowing write to metadata but not binary for user")
        binary_acl = "@prefix acl: <{0}> .\n" \
                     "<#binary> a acl:Authorization ;\n" \
                     "  acl:mode acl:Write ;\n" \
                     "  acl:accessTo <{1}> ;\n" \
                     "  acl:agent \"{2}\" .\n".format(TestConstants.ACL_NS, binary_location,
                                                      self.config[TestConstants.USER_NAME_PARAM])
        headers = {
            'Content-type': TestConstants.TURTLE_MIMETYPE
        }
        r = self.do_put(acl_location, headers=headers, body=binary_acl)
        self.checkResponse(201, r)

        self.log("Try to read binary")
        r = self.do_head(binary_location, admin=False)
        self.checkResponse(403, r)

        self.log("Try to write binary")
        headers = {
            'Content-type': 'text/plain'
        }
        r = self.do_put(binary_location, headers=headers, body="This is a new body", admin=False)
        self.checkResponse(204, r)

        self.log("Try to read the metadata")
        r = self.do_get(binary_description, admin=False)
        self.checkResponse(403, r)

        self.log("Try to patch metadata")
        patch_body = "prefix dc: <{0}> INSERT DATA {{ <> dc:title \"Updated title\"}}".format(TestConstants.PURL_NS)
        headers = {
            'Content-type': TestConstants.SPARQL_UPDATE_MIMETYPE
        }
        r = self.do_patch(binary_description, patch_body, headers=headers, admin=False)
        self.checkResponse(204, r)
