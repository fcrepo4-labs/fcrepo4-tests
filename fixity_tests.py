#!/bin/env python

import TestConstants
from abstract_fedora_tests import FedoraTests, register_tests, Test
import os.path
import pyjq
import json


@register_tests
class FedoraFixityTests(FedoraTests):

    # Create test objects all inside here for easy of review
    CONTAINER = "/test_fixity"

    # Sha1 fixity result for basic_image.jpg in the resource sub-directory
    FIXITY_RESULT = "urn:sha1:dec028a4400b4f7ed80ed1174e65179d6b57a0f2"

    @Test
    def aFixityTest(self):

        self.log("Create a binary")
        headers = {
            'Content-type': 'image/jpeg',
        }
        with open(os.path.join(os.getcwd(), 'resources', 'basic_image.jpg'), 'rb') as fp:
            data = fp.read()
            r = self.do_post(self.getBaseUri(), headers=headers, body=data)
            self.assertEqual(201, r.status_code, 'Did not create binary')
            location = self.get_location(r)

        fixity_endpoint = location + "/" + TestConstants.FCR_FIXITY
        self.log("Get a fixity result")
        headers = {
            'Accept': TestConstants.JSONLD_MIMETYPE
        }
        r = self.do_get(fixity_endpoint, headers=headers)
        self.assertEqual(200, r.status_code, "Can't get the fixity result")
        body = r.content.decode('UTF-8').rstrip('\ny')
        json_body = json.loads(body)
        fixity_id = pyjq.first('.[0]."http://www.loc.gov/premis/rdf/v1#hasFixity"| .[]?."@id"', json_body)
        fixity_result = pyjq.first('.[] | select(."@id" == "{0}") | '
                                   '."http://www.loc.gov/premis/rdf/v1#hasMessageDigest" | .[]?."@id"'.format(fixity_id),
                                   json_body)
        self.assertEqual(self.FIXITY_RESULT, fixity_result, "Fixity result was not a match for expected.")
