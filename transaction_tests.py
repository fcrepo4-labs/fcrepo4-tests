#!/bin/env python

import TestConstants
from abstract_fedora_tests import FedoraTests, register_tests, Test
import json
import pyjq


@register_tests
class FedoraTransactionTests(FedoraTests):

    # Create test objects all inside here for easy of review
    CONTAINER = "/test_transaction"

    def get_transaction_provider(self):
        headers = {
            'Accept': TestConstants.JSONLD_MIMETYPE
        }
        r = self.do_get(self.getFedoraBase(), headers=headers)
        self.assertEqual(200, r.status_code, "Did not get expected response")
        body = r.content.decode('UTF-8')
        json_body = json.loads(body)
        tx_provider = pyjq.first('.[]."http://fedora.info/definitions/v4/repository#hasTransactionProvider" | .[]."@id"',
                                 json_body)
        return tx_provider

    @Test
    def doCommitTest(self):
        self.log("Running doCommitTest")

        tx_provider = self.get_transaction_provider()
        if tx_provider is None:
            self.log("Could not location transaction provider")
            self.log("Skipping test")
        else:
            self.log("Create a transaction")
            r = self.do_post(tx_provider)
            self.assertEqual(201, r.status_code, "Did not get expected response code")
            full_transaction_uri = self.get_location(r)
            transaction = full_transaction_uri.replace(self.getFedoraBase(), "")
            self.log("Transaction is {0}".format(transaction))

            self.log("Get status of transaction")
            r = self.do_get(full_transaction_uri)
            self.assertEqual(200, r.status_code, "Did not get expected response code")

            self.log("Create an container in the transaction")
            r = self.do_post(full_transaction_uri + self.CONTAINER)
            self.assertEqual(201, r.status_code, "Did not get expected response code")
            transaction_obj = self.get_location(r)

            self.log("Container is available inside the transaction")
            r = self.do_get(transaction_obj)
            self.assertEqual(200, r.status_code, "Did not get expected response code")

            self.log("Container not available outside the transaction")
            outside_location = transaction_obj.replace(transaction, "")
            r = self.do_get(outside_location)
            self.assertEqual(404, r.status_code, "Did not get expected response code")

            self.log("Commit transaction")
            r = self.do_post(full_transaction_uri + "/fcr:tx/fcr:commit")
            self.assertEqual(204, r.status_code, "Did not get expected response code")

            self.log("Container is now available outside the transaction")
            r = self.do_get(outside_location)
            self.assertEqual(200, r.status_code, "Did not get expected response code")

            self.log("Passed")

    @Test
    def doRollbackTest(self):
        self.log("Running doRollbackTest")

        tx_provider = self.get_transaction_provider()
        if tx_provider is None:
            self.log("Could not location transaction provider")
            self.log("Skipping test")
        else:
            self.log("Create a transaction")
            r = self.do_post(tx_provider)
            self.assertEqual(201, r.status_code, "Did not get expected response code")
            full_transaction_uri = self.get_location(r)
            transaction = full_transaction_uri.replace(self.getFedoraBase(), "")
            self.log("Transaction is {0}".format(transaction))

            self.log("Create an container in the transaction")
            r = self.do_post(full_transaction_uri + self.CONTAINER)
            self.assertEqual(201, r.status_code, "Did not get expected response code")
            transaction_obj = self.get_location(r)

            self.log("Container is available inside the transaction")
            r = self.do_get(transaction_obj)
            self.assertEqual(200, r.status_code, "Did not get expected response code")

            self.log("Container not available outside the transaction")
            outside_location = transaction_obj.replace(transaction, "")
            r = self.do_get(outside_location)
            self.assertEqual(404, r.status_code, "Did not get expected response code")

            self.log("Rollback transaction")
            r = self.do_post(full_transaction_uri + "/fcr:tx/fcr:rollback")
            self.assertEqual(204, r.status_code, "Did not get expected response code")

            self.log("Container is still not available outside the transaction")
            r = self.do_get(outside_location)
            self.assertEqual(404, r.status_code, "Did not get expected response code")

            self.log("Passed")
