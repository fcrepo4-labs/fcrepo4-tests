#!/bin/env python

import TestConstants
from abstract_fedora_tests import FedoraTests, register_tests, Test
import json
import pyjq


@register_tests
class FedoraIndirectTests(FedoraTests):

    # Create test objects all inside here for ease of review/removal
    CONTAINER = "/test_indirect"

    @Test
    def doPcdmIndirect(self):
        self.log("Create a PCDM container")
        basic_headers = {
            'Link': self.make_type(TestConstants.LDP_BASIC),
            'Content-type': 'text/turtle'
        }
        r = self.do_post(self.getBaseUri(), headers=basic_headers, body=TestConstants.OBJECT_TTL)
        self.assertEqual(201, r.status_code, "Did not get expected status code")
        pcdm_container_location = self.get_location(r)

        self.log("Create a PCDM Collection")
        r = self.do_post(self.getBaseUri(), headers=basic_headers, body=TestConstants.OBJECT_TTL)
        self.assertEqual(201, r.status_code, "Did not get expected status code")
        pcdm_collection_location = self.get_location(r)

        self.log("Create indirect container inside PCDM collection")
        indirect_headers = {
            'Link': self.make_type(TestConstants.LDP_INDIRECT),
            'Content-type': 'text/turtle'
        }
        pcdm_indirect = "@prefix dc: <http://purl.org/dc/elements/1.1/> ." \
                        "@prefix pcdm: <http://pcdm.org/models#> ." \
                        "@prefix ore: <http://www.openarchives.org/ore/terms/> ." \
                        "@prefix ldp: <http://www.w3.org/ns/ldp#> ." \
                        "<> dc:title \"Members Container\" ;" \
                        " ldp:membershipResource <{0}> ;" \
                        " ldp:hasMemberRelation pcdm:hasMember ;" \
                        " ldp:insertedContentRelation ore:proxyFor .".format(pcdm_collection_location)
        r = self.do_post(pcdm_collection_location, headers=indirect_headers, body=pcdm_indirect)
        self.assertEqual(201, r.status_code, "Did not get expected status code")
        members_location = self.get_location(r)

        self.log("Create a proxy object")
        pcdm_proxy = "@prefix pcdm: <http://pcdm.org/models#>" \
                     "@prefix ore: <http://www.openarchives.org/ore/terms/>" \
                     "<> a pcdm:Object ;" \
                     "ore:proxyFor <{0}> .".format(pcdm_container_location)
        r = self.do_post(members_location, headers=basic_headers, body=pcdm_proxy)
        self.assertEqual(201, r.status_code, "Did not get expected status code")

        self.log("Check PCDM Collection for a new pcmd:hasMember property to PCDM container")
        headers = {
            'Accept': TestConstants.JSONLD_MIMETYPE
        }
        r = self.do_get(pcdm_collection_location, headers=headers)
        self.assertEqual(200, r.status_code, "Did not get expected status code")

        body = r.content.decode('UTF-8')
        body_json = json.loads(body)
        hasmembers = pyjq.all('.[] | ."http://pcdm.org/models#hasMember" | .[]."@id"', body_json)
        found_member = False
        for member in hasmembers:
            if member == pcdm_container_location:
                found_member = True
        self.assertTrue(found_member, "Did not find hasMember property")
