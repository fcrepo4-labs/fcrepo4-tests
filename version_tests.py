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

    def checkMementoCount(self, expected, uri, admin=None):
        if admin is None:
            admin = True
        if not uri.endswith("/" + TestConstants.FCR_VERSIONS):
            uri += "/" + TestConstants.FCR_VERSIONS
        headers = {
            'Accept': TestConstants.LINK_FORMAT_MIMETYPE
        }
        r = self.do_get(uri, headers=headers, admin=admin)
        self.checkResponse(200, r)
        self.checkValue(expected, self.count_mementos(r))

    @Test
    def doContainerVersioningTest(self):
        headers = {
            'Link': self.make_type(TestConstants.LDP_BASIC)
        }
        r = self.do_post(self.getBaseUri(), headers=headers)
        self.log("Create a basic container")
        self.checkResponse(201, r)
        location = self.get_location(r)

        version_endpoint = location + "/" + TestConstants.FCR_VERSIONS
        r = self.do_get(version_endpoint)
        self.checkResponse(200, r)

        self.log("Create a version")
        r = self.do_post(version_endpoint)
        self.checkResponse(201, r)

        self.log("Get the resource content")
        headers = {
            'Accept': TestConstants.JSONLD_MIMETYPE
        }
        r = self.do_get(location, headers=headers)
        self.checkResponse(200, r)
        body = r.content.decode('UTF-8').rstrip('\n')

        new_date = FedoraTests.get_rfc_date("2000-06-01 08:21:00")

        headers = {
            'Content-Type': TestConstants.JSONLD_MIMETYPE,
            'Prefer': TestConstants.PUT_PREFER_LENIENT,
            'Memento-Datetime': new_date
        }
        self.log("Check you must provide a valid body")
        r = self.do_post(version_endpoint, headers=headers, body="[]")
        self.checkResponse(400, r)

        self.log("Create a version with provided datetime")
        r = self.do_post(version_endpoint, headers=headers, body=body)
        self.checkResponse(201, r)
        memento_location = self.get_location(r)

        self.log("Try creating another version at the same location")
        r = self.do_post(version_endpoint, headers=headers, body=body)
        self.checkResponse(409, r)

        self.log("Check memento exists")
        r = self.do_get(memento_location)
        self.checkResponse(200, r)
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
        self.checkResponse(204, r)

        self.log("Try to patch the memento")
        r = self.do_patch(memento_location, headers=headers, body=sparql_body)
        self.checkResponse(405, r)

        self.log("Wait a second to change the time.")
        time.sleep(1)

        self.log("Create another version")
        r = self.do_post(version_endpoint)
        self.checkResponse(201, r)

        self.log("Count mementos")
        self.checkMementoCount(3, version_endpoint)

        self.log("Delete a Memento")
        r = self.do_delete(memento_location)
        self.checkResponse(204, r)

        self.log("Validate delete")
        r = self.do_get(memento_location)
        self.checkResponse(404, r)

        self.log("Validate delete with another count")
        self.checkMementoCount(2, version_endpoint)

        self.log("Create a memento at the deleted datetime")
        headers = {
            'Content-Type': TestConstants.JSONLD_MIMETYPE,
            'Prefer': TestConstants.PUT_PREFER_LENIENT,
            'Memento-Datetime': new_date
        }
        r = self.do_post(version_endpoint, headers=headers, body=body)
        self.checkResponse(201, r)

        self.log("Check the memento exists again")
        r = self.do_get(memento_location)
        self.checkResponse(200, r)

    @Test
    def doBinaryVersioningTest(self):
        headers = {
            'Link': self.make_type(TestConstants.LDP_NON_RDF_SOURCE),
            'Content-Type': 'text/csv'
        }
        files = {'file': ('report.csv', 'some,data,to,send\nanother,row,to,send\n')}

        r = self.do_post(self.getBaseUri(), headers=headers, files=files)

        self.log("Create a NonRdfSource")
        self.checkResponse(201, r)
        location = self.get_location(r)
        description_location = self.find_binary_description(r)

        version_endpoint = location + "/" + TestConstants.FCR_VERSIONS
        description_version_endpoint = description_location + "/" + TestConstants.FCR_VERSIONS

        self.log("Get version endpoint")
        r = self.do_get(version_endpoint)
        self.checkResponse(200, r)

        self.log("Get description version endpoint")
        r = self.do_get(description_version_endpoint)
        self.checkResponse(200, r)

        self.log("Create a version")
        r = self.do_post(version_endpoint)
        self.checkResponse(201, r)

        self.log("Try to create another version too quickly")
        r = self.do_post(version_endpoint)
        self.checkResponse(409, r)

        self.assertNotEqual(version_endpoint, description_version_endpoint)

        self.log("Try to create a version of the description quickly")
        r = self.do_post(description_version_endpoint)
        self.checkResponse(409, r)

        new_date = FedoraTests.get_rfc_date("2000-06-01 08:21:00")

        self.log("Create a version with provided datetime")
        headers = {
            'Content-Type': 'text/csv',
            'Memento-Datetime': new_date
        }
        r = self.do_post(version_endpoint, headers=headers, files=files)
        self.checkResponse(201, r)
        memento_location = self.get_location(r)

        self.log("Try creating another version at the same location")
        r = self.do_post(version_endpoint, headers=headers, files=files)
        self.checkResponse(409, r)

        self.log("Check memento exists")
        r = self.do_head(memento_location)
        self.checkResponse(200, r)
        found_datetime = r.headers['Memento-Datetime']
        self.assertIsNotNone(found_datetime, "Did not find Memento-Datetime header")
        self.assertEqual(0, self.compare_rfc_dates(new_date, found_datetime), "Returned Memento-Datetime did not match sent")

        self.log("PUT to the original resource")
        files = {'file': ('report.csv', 'some,data,to,send\nanother,row,to,send\nevent,more,data,tosend\n')}
        headers = {
            'Content-Type': 'text/csv'
        }
        r = self.do_put(location, headers=headers, files=files)
        self.checkResponse(204, r)

        self.log("Try to put to the memento")
        r = self.do_put(memento_location, headers=headers, files=files)
        self.checkResponse(405, r)

        self.log("Wait one second to change the time.")
        time.sleep(1)

        self.log("Create another version")
        r = self.do_post(version_endpoint)
        self.checkResponse(201, r)

        self.log("Count mementos")
        self.checkMementoCount(3, version_endpoint)

        self.log("Delete a Memento")
        r = self.do_delete(memento_location)
        self.checkResponse(204, r)

        self.log("Validate delete")
        r = self.do_get(memento_location)
        self.checkResponse(404, r)

        self.log("Validate delete with another count")
        self.checkMementoCount(2, version_endpoint)

        self.log("Create a memento at the deleted datetime")
        headers = {
            'Content-Type': TestConstants.JSONLD_MIMETYPE,
            'Prefer': TestConstants.PUT_PREFER_LENIENT,
            'Memento-Datetime': new_date
        }
        r = self.do_post(version_endpoint, headers=headers, files=files)
        self.checkResponse(201, r)

        self.log("Check the memento exists again")
        r = self.do_head(memento_location)
        self.checkResponse(200, r)

        self.log("Validate count of mementos again")
        self.checkMementoCount(3, version_endpoint)

    @Test
    def checkBinaryVersioning(self):
        headers = {
            'Link': self.make_type(TestConstants.LDP_NON_RDF_SOURCE),
            'Content-Type': 'text/csv'
        }
        files = {'file': ('report.csv', 'some,data,to,send\nanother,row,to,send\n')}

        self.log("Create a NonRdfSource")
        r = self.do_post(self.getBaseUri(), headers=headers, files=files)
        self.checkResponse(201, r)
        location = self.get_location(r)
        description_location = self.find_binary_description(r)

        binary_versions = location + "/" + TestConstants.FCR_VERSIONS
        metadata_versions = description_location + "/" + TestConstants.FCR_VERSIONS

        link_headers = {
            'Accept': TestConstants.LINK_FORMAT_MIMETYPE
        }

        self.log("Count Mementos of binary")
        r = self.do_get(binary_versions, headers=link_headers)
        self.checkResponse(200, r)
        self.checkValue(0, self.count_mementos(r))

        self.log("Count Mementos of binary description")
        r = self.do_get(metadata_versions, headers=link_headers)
        self.checkResponse(200, r)
        self.checkValue(0, self.count_mementos(r))

        self.log("Create version of binary from existing")
        r = self.do_post(binary_versions)
        self.checkResponse(201, r)

        self.log("Count Mementos of binary")
        self.checkMementoCount(1, binary_versions)

        self.log("Count Mementos of binary description")
        self.checkMementoCount(1, metadata_versions)

        self.log("Wait a second")
        time.sleep(1)

        self.log("Create version of binary metadata from existing")
        r = self.do_post(metadata_versions)
        self.checkResponse(201, r)

        self.log("Count Mementos of binary")
        self.checkMementoCount(1, binary_versions)

        self.log("Count Mementos of binary description")
        self.checkMementoCount(2, metadata_versions)

    @Test
    def createBinaryVersionsAtSameTime(self):
        headers = {
            'Link': self.make_type(TestConstants.LDP_NON_RDF_SOURCE),
            'Content-Type': 'text/csv'
        }
        files = {'file': ('report.csv', 'some,data,to,send\nanother,row,to,send\n')}

        self.log("Create a NonRdfSource")
        r = self.do_post(self.getBaseUri(), headers=headers, files=files)
        self.checkResponse(201, r)
        location = self.get_location(r)
        description_location = self.find_binary_description(r)

        r = self.do_get(description_location)
        new_body = "@prefix dc: <{0}> .\n".format(TestConstants.PURL_NS) + \
            r.text[0:-2] + ";\n dc:title \"New title\" .\n".format(TestConstants.PURL_NS)

        version_endpoint = location + "/" + TestConstants.FCR_VERSIONS
        description_version_endpoint = description_location + "/" + TestConstants.FCR_VERSIONS

        the_date = FedoraTests.get_rfc_date('2019-05-21 18:30:00')
        files = {'file': ('report.csv', 'some,data,to,send\nanother,row,to,send\nevent,more,data,tosend\n')}
        headers = {
            'Content-Type': 'text/csv',
            'Memento-Datetime': the_date
        }

        self.log("Make version for {0} of binary".format(the_date))
        r = self.do_post(version_endpoint, headers=headers, files=files)
        self.checkResponse(201, r)

        headers = {
            'Content-type': TestConstants.TURTLE_MIMETYPE,
            'Memento-Datetime': the_date,
            'Prefer': TestConstants.PUT_PREFER_LENIENT
        }

        self.log("Make version for {0} of binary description".format(the_date))
        r = self.do_post(description_version_endpoint, headers=headers, body=new_body)
        self.checkResponse(201, r)

        self.log("Count binary mementos")
        self.checkMementoCount(1, version_endpoint)

        self.log("Count binary description mementos")
        self.checkMementoCount(1, description_version_endpoint)
