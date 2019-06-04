#!/bin/env python

import TestConstants
from abstract_fedora_tests import FedoraTests, register_tests, Test
import uuid
import datetime
import requests
import json
import pyjq


@register_tests
class FedoraCamelTests(FedoraTests):

    # Create test objects all inside here for easy of review.
    CONTAINER = "/test_camel"

    # How many seconds to wait for indexing to Solr and/or triplestore.
    CONTAINER_WAIT = 30

    def run_tests(self):
        if not (self.hasSolrUrl() and self.hasTriplestoreUrl()):
            print("**** Cannot run camel tests without a Solr and/or Triplestore base url ****")
        else:
            super().run_tests()

    @Test
    def CamelCreateObject(self):
        self.log("Create an object")
        internal_id = str(uuid.uuid4())
        expected_url = self.getBaseUri() + "/" + internal_id
        headers = {
            'Slug': internal_id,
            'Content-type': TestConstants.TURTLE_MIMETYPE
        }
        r = self.do_post(headers=headers, body=TestConstants.PCDM_CONTAINER_TTL)
        self.assertEqual(201, r.status_code, "Did not get expected response code")

        if self.hasSolrUrl():
            self.log("Checking for item in Solr")
            solr_response = self.timedQuery('querySolr', 'solrNumFound', expected_url)
            if solr_response is not None:
                self.assertEqual(expected_url, self.getIdFromSolr(solr_response), "Did not find ID in Solr.")
            else:
                self.fail("Timed out waiting to find record in Solr.")

        if self.hasTriplestoreUrl():
            self.log("Checking for item in Triplestore")
            triplestore_response = self.timedQuery('queryTriplestore', 'triplestoreNumFound', expected_url)
            if triplestore_response is not None:
                self.assertEqual(TestConstants.PCDM_CONTAINER_TITLE, self.getIdFromTriplestore(triplestore_response),
                                 "Did not find ID in Triplestore")
            else:
                self.fail("Timed out waiting to find record in Triplestore")

    # Utility functions.
    def timedQuery(self, query_method, check_method, query_value):
        query_func = getattr(self, query_method, None)
        check_func = getattr(self, check_method, None)
        if query_func is None or check_func is None:
            Exception("Can't find expected methods {0}, {1}".format(query_method, check_method))
        current_time = datetime.datetime.now()
        end_time = current_time + datetime.timedelta(seconds=self.CONTAINER_WAIT)
        last_query = None
        while current_time <= end_time:
            # If a multiple of 5 seconds has passed since the last query, do the query
            if last_query is None or (current_time - last_query).seconds >= 5:
                last_query = datetime.datetime.now()
                response = query_func(query_value)
                if check_func(response) is not None:
                    return response
            current_time = datetime.datetime.now()
        return None

    def hasSolrUrl(self):
        try:
            return self.config[TestConstants.SOLR_URL_PARAM] is not None and \
               len(self.config[TestConstants.SOLR_URL_PARAM].strip()) > 0
        except KeyError:
            return False

    def hasTriplestoreUrl(self):
        try:
            return self.config[TestConstants.TRIPLESTORE_URL_PARAM] is not None and \
               len(self.config[TestConstants.TRIPLESTORE_URL_PARAM].strip()) > 0
        except KeyError:
            return False

    def solrNumFound(self, response):
        body = response.content.decode('UTF-8')
        json_body = json.loads(body)
        num_found = pyjq.first('.response.numFound', json_body)
        if num_found is not None and int(num_found) > 0:
            return num_found
        return None

    def querySolr(self, expected_id):
        solr_select = self.config[TestConstants.SOLR_URL_PARAM].rstrip('/') + "/select"
        params = {
            'q': 'id:"' + expected_id + '"',
            'wt': 'json'
        }
        r = requests.get(solr_select, params=params)
        self.assertEqual(200, r.status_code, "Did not query Solr successfully.")
        return r

    def getIdFromSolr(self, response):
        body = response.content.decode('UTF-8')
        json_body = json.loads(body)
        found_title = pyjq.first('.response.docs[].id', json_body)
        return found_title

    def queryTriplestore(self, expected_id):
        query = "PREFIX dc: <http://purl.org/dc/elements/1.1/> SELECT ?o WHERE { <" + expected_id + "> dc:title ?o}"
        headers = {
            'Content-type': TestConstants.SPARQL_QUERY_MIMETYPE,
            'Accept': TestConstants.SPARQL_RESULT_JSON_MIMETYPE
        }
        r = requests.post(self.config[TestConstants.TRIPLESTORE_URL_PARAM], headers=headers, data=query)
        self.assertEqual(200, r.status_code, 'Did not query Triplestore successfully.')
        return r

    def triplestoreNumFound(self, response):
        body = response.content.decode('UTF-8')
        json_body = json.loads(body)
        # This results a list of matching bindings, so it can be an empty list.
        num_found = pyjq.all('.results.bindings[].o', json_body)
        if num_found is not None and len(num_found) > 0:
            return num_found
        return None

    def getIdFromTriplestore(self, response):
        body = response.content.decode('UTF-8')
        json_body = json.loads(body)
        found_id = pyjq.first('.results.bindings[].o.value', json_body)
        return found_id
