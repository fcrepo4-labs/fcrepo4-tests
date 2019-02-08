#!/bin/env python

import TestConstants
from abstract_fedora_tests import FedoraTests, register_tests, Test
import time


@register_tests
class FedoraVersionTests(FedoraTests):

    # Create test objects all inside here for easy of review
    CONTAINER = "/test_version"

    @staticmethod
    def count_mementos(response):
        body = response.content.decode('UTF-8')
        mementos = [x for x in body.split('\n') if x.find("rel=\"memento\"") >= 0]
        return len(mementos)

    @Test
    def doContainerVersioningTest(self):
        self.log("Running doContainerVersioningTest")
        headers = {
            'Link': self.make_type(TestConstants.LDP_BASIC)
        }
        r = self.do_post(self.getBaseUri(), headers=headers)
        self.log("Create a basic container")
        self.assertEqual(201, r.status_code, "Did not create container")
        location = self.get_location(r)

        version_endpoint = location + "/" + TestConstants.FCR_VERSIONS
        r = self.do_get(version_endpoint)
        self.assertEqual(200, r.status_code, "Did not find versions where we should")

        self.log("Create a version")
        r = self.do_post(version_endpoint)
        self.assertEqual(201, r.status_code, 'Did not create a version')

        self.log("Get the resource content")
        headers = {
            'Accept': TestConstants.JSONLD_MIMETYPE
        }
        r = self.do_get(location, headers=headers)
        self.assertEqual(200, r.status_code, "Could not get the resource")
        body = r.content.decode('UTF-8').rstrip('\n')

        new_date = FedoraTests.get_rfc_date("2000-06-01 08:21:00")

        self.log("Create a version with provided datetime")
        headers = {
            'Content-Type': TestConstants.JSONLD_MIMETYPE,
            'Prefer': TestConstants.PUT_PREFER_LENIENT,
            'Memento-Datetime': new_date
        }
        r = self.do_post(version_endpoint, headers=headers, body="[]")
        self.assertEqual(400, r.status_code, "Empty body should cause Bad request")

        r = self.do_post(version_endpoint, headers=headers, body=body)
        self.assertEqual(201, r.status_code, "Did not create memento will body.")
        memento_location = self.get_location(r)

        self.log("Try creating another version at the same location")
        r = self.do_post(version_endpoint, headers=headers, body=body)
        self.assertEqual(409, r.status_code, "Did not get conflict trying to create a second memento")

        self.log("Check memento exists")
        r = self.do_get(memento_location)
        self.assertEqual(200, r.status_code, "Memento was not found")
        found_datetime = r.headers['Memento-Datetime']
        self.assertIsNotNone(found_datetime, "Did not find Memento-Datetime header")
        self.assertEqual(0, self.compare_rfc_dates(new_date, found_datetime), "Returned Memento-Datetime did not match sent")

        self.log("Patch the original resource")
        sparql_body = "prefix dc: <http://purl.org/dc/elements/1.1/> " \
                      "DELETE { <> dc:title ?o . }" \
                      "INSERT { <> dc:title \"Updated title\" . }" \
                      "WHERE { <> dc:title ?o . }"
        headers = {
            "Content-Type": TestConstants.SPARQL_UPDATE_MIMETYPE
        }
        r = self.do_patch(location, headers=headers, body=sparql_body)
        self.assertEqual(204, r.status_code, "Unable to patch")

        self.log("Try to patch the memento")
        r = self.do_patch(memento_location, headers=headers, body=sparql_body)
        self.assertEqual(405, r.status_code, "Did not get denied PATCH request.")

        # Delay one second to ensure we don't POST at the same time
        time.sleep(1)

        self.log("Create another version")
        r = self.do_post(version_endpoint)
        self.assertEqual(201, r.status_code, 'Did not create a version')

        self.log("Count mementos")
        headers = {
            'Accept': 'application/link-format'
        }
        r = self.do_get(version_endpoint, headers=headers)
        self.assertEqual(200, r.status_code, "Did not get the fcr:versions content")
        self.assertEqual(3, FedoraVersionTests.count_mementos(r), "Incorrect number of Mementos")

        self.log("Delete a Memento")
        r = self.do_delete(memento_location)
        self.assertEqual(204, r.status_code, "Did not delete the Memento")

        self.log("Validate delete")
        r = self.do_get(memento_location)
        self.assertEqual(404, r.status_code, "Memento was not gone")

        self.log("Validate delete with another count")
        r = self.do_get(version_endpoint, headers=headers)
        self.assertEqual(200, r.status_code, "Did not get the fcr:versions content")
        self.assertEqual(2, FedoraVersionTests.count_mementos(r), "Incorrect number of Mementos")

        self.log("Create a memento at the deleted datetime")
        headers = {
            'Content-Type': TestConstants.JSONLD_MIMETYPE,
            'Prefer': TestConstants.PUT_PREFER_LENIENT,
            'Memento-Datetime': new_date
        }
        r = self.do_post(version_endpoint, headers=headers, body=body)
        self.assertEqual(201, r.status_code, "Did not create version with specific date and body")

        self.log("Check the memento exists again")
        r = self.do_get(memento_location)
        self.assertEqual(200, r.status_code, "Memento was not found")

        self.log("Passed")

    @Test
    def doBinaryVersioningTest(self):
        self.log("Running doBinaryVersioningTest")

        headers = {
            'Link': self.make_type(TestConstants.LDP_NON_RDF_SOURCE),
            'Content-Type': 'text/csv'
        }
        files = {'file': ('report.csv', 'some,data,to,send\nanother,row,to,send\n')}

        r = self.do_post(self.getBaseUri(), headers=headers, files=files)

        self.log("Create a NonRdfSource")
        self.assertEqual(201, r.status_code, "Did not create NonRdfSource")
        location = self.get_location(r)

        version_endpoint = location + "/" + TestConstants.FCR_VERSIONS
        r = self.do_get(version_endpoint)
        self.assertEqual(200, r.status_code, "Did not find versions where we should")

        self.log("Create a version")
        r = self.do_post(version_endpoint)
        self.assertEqual(201, r.status_code, 'Did not create a version')

        new_date = FedoraTests.get_rfc_date("2000-06-01 08:21:00")

        self.log("Create a version with provided datetime")
        headers = {
            'Content-Type': 'text/csv',
            'Memento-Datetime': new_date
        }
        r = self.do_post(version_endpoint, headers=headers, files=files)
        self.assertEqual(201, r.status_code, "Did not create version with specific date and body")
        memento_location = self.get_location(r)

        self.log("Try creating another version at the same location")
        r = self.do_post(version_endpoint, headers=headers, files=files)
        self.assertEqual(409, r.status_code, "Did not get conflict trying to create a second memento")

        self.log("Check memento exists")
        r = self.do_head(memento_location)
        self.assertEqual(200, r.status_code, "Memento was not found")
        found_datetime = r.headers['Memento-Datetime']
        self.assertIsNotNone(found_datetime, "Did not find Memento-Datetime header")
        self.assertEqual(0, self.compare_rfc_dates(new_date, found_datetime), "Returned Memento-Datetime did not match sent")

        self.log("PUT to the original resource")
        files = {'file': ('report.csv', 'some,data,to,send\nanother,row,to,send\nevent,more,data,tosend\n')}
        headers = {
            'Content-Type': 'text/csv'
        }
        r = self.do_put(location, headers=headers, files=files)
        self.assertEqual(204, r.status_code, "Unable to put")

        self.log("Try to put to the memento")
        r = self.do_put(memento_location, headers=headers, files=files)
        self.assertEqual(405, r.status_code, "Did not get denied PUT request.")

        # Delay one second to ensure we don't POST at the same time
        time.sleep(1)

        self.log("Create another version")
        r = self.do_post(version_endpoint)
        self.assertEqual(201, r.status_code, 'Did not create a version')

        self.log("Count mementos")
        headers = {
            'Accept': 'application/link-format'
        }
        r = self.do_get(version_endpoint, headers=headers)
        self.assertEqual(200, r.status_code, "Did not get the fcr:versions content")
        self.assertEqual(3, FedoraVersionTests.count_mementos(r), "Incorrect number of Mementos")

        self.log("Delete a Memento")
        r = self.do_delete(memento_location)
        self.assertEqual(204, r.status_code, "Did not delete the Memento")

        self.log("Validate delete")
        r = self.do_get(memento_location)
        self.assertEqual(404, r.status_code, "Memento was not gone")

        self.log("Validate delete with another count")
        r = self.do_get(version_endpoint, headers=headers)
        self.assertEqual(200, r.status_code, "Did not get the fcr:versions content")
        self.assertEqual(2, FedoraVersionTests.count_mementos(r), "Incorrect number of Mementos")

        self.log("Create a memento at the deleted datetime")
        headers = {
            'Content-Type': TestConstants.JSONLD_MIMETYPE,
            'Prefer': TestConstants.PUT_PREFER_LENIENT,
            'Memento-Datetime': new_date
        }
        r = self.do_post(version_endpoint, headers=headers, files=files)
        self.assertEqual(201, r.status_code, "Did not create version with specific date and body")

        self.log("Check the memento exists again")
        r = self.do_head(memento_location)
        self.assertEqual(200, r.status_code, "Memento was not found")

        self.log("Passed")

