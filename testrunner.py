#!/usr/bin/env python

import argparse
import TestConstants
import os
import os.path
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from basic_interaction_tests import FedoraBasicIxnTests
from version_tests import FedoraVersionTests
from fixity_tests import FedoraFixityTests
from rdf_tests import FedoraRdfTests
from sparql_tests import FedoraSparqlTests
from transaction_tests import FedoraTransactionTests
from authz_tests import FedoraAuthzTests
from indirect_tests import FedoraIndirectTests
from camel_tests import FedoraCamelTests


class FedoraTestRunner:

    # Tuples of parameter name and mandatory status
    config_params = [
        (TestConstants.BASE_URL_PARAM, True),
        (TestConstants.ADMIN_USER_PARAM, True),
        (TestConstants.ADMIN_PASS_PARAM, True),
        (TestConstants.USER_NAME_PARAM, True),
        (TestConstants.USER_PASS_PARAM, True),
        (TestConstants.USER2_NAME_PARAM, True),
        (TestConstants.USER2_PASS_PARAM, True),
        (TestConstants.LOG_FILE_PARAM, False),
        (TestConstants.SELECTED_TESTS_PARAM, False),
        (TestConstants.SOLR_URL_PARAM, False),
        (TestConstants.TRIPLESTORE_URL_PARAM, False)
    ]
    config = {}
    logger = None

    def set_up(self, args):
        self.parse_cmdline_args(args)
        self.check_config()

    def load_config(self, file, site):
        if os.path.exists(file):
            if os.access(file, os.R_OK):
                with open(file, 'r') as fp:
                    yml = load(fp.read())
                    self.config = yml.get(site)

    def parse_cmdline_args(self, args):
        filename = eval('args.' + TestConstants.CONFIG_FILE_PARAM)
        if filename is not None:
            sitename = eval('args.' + TestConstants.SITE_NAME_PARAM)
            if sitename is not None:
                self.load_config(filename, sitename)
        for param_name, param_status in self.config_params:
            if param_name == TestConstants.CONFIG_FILE_PARAM or param_name == TestConstants.SITE_NAME_PARAM:
                continue
            try:
                tmpA = eval("args." + param_name)
                if tmpA is not None:
                    self.config[param_name] = tmpA
            except AttributeError:
                if param_status:
                    parser.error("Could not find configuration parameter {}".format(param_name))

    def check_config(self):
        for param_name, param_status in self.config_params:
            try:
                if self.config[param_name] is not None:
                    pass
            except KeyError:
                if param_status:
                    raise Exception("Missing config parameter (" + param_name + ")")

    def run_tests(self):
        for test in self.config[TestConstants.SELECTED_TESTS_PARAM]:
            if test == 'all' or test == 'basic':
                nested = FedoraBasicIxnTests(self.config)
                nested.run_tests()
            if test == 'all' or test == 'version':
                versioning = FedoraVersionTests(self.config)
                versioning.run_tests()
            if test == 'all' or test == 'fixity':
                fixity = FedoraFixityTests(self.config)
                fixity.run_tests()
            if test == 'all' or test == 'rdf':
                rdf = FedoraRdfTests(self.config)
                rdf.run_tests()
            if test == 'all' or test == 'sparql':
                sparql = FedoraSparqlTests(self.config)
                sparql.run_tests()
            if test == 'all' or test == 'transaction':
                transaction = FedoraTransactionTests(self.config)
                transaction.run_tests()
            if test == 'all' or test == 'authz':
                authz = FedoraAuthzTests(self.config)
                authz.run_tests()
            if test == 'all' or test == 'indirect':
                indirect = FedoraIndirectTests(self.config)
                indirect.run_tests()
            if test == 'camel':
                camel = FedoraCamelTests(self.config)
                camel.run_tests()

    def main(self, args):
        self.set_up(args)
        self.run_tests()


def csv_list(string):
    if ',' in string:
        output = list(set([x for x in string.split(',') if len(x) > 0]))
    elif len(string) > 0:
        output = string
    else:
        output = list()
    return output


class CSVAction(argparse.Action):
    valid_options = ["authz", "basic", "sparql", "rdf", "version", "transaction", "fixity", "indirect", "camel"]

    def __call__(self, parser, args, values, option_string=None):
        if isinstance(values, list):
            invalid = [x for x in values if x not in self.valid_options]
        else:
            invalid = [values] if values not in self.valid_options else []
            values = [values]

        if len(invalid) > 0:
            if len(invalid) == 1:
                exception_text = "The option \"{0}\" is not valid, choose from {1}"
            else:
                exception_text = "The options \"{0}\" are not valid, choose from {1}"

            raise argparse.ArgumentError(self, exception_text.format(",".join(invalid), ",".join(self.valid_options)))
        setattr(args, self.dest, values)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Fedora Tester runs a series of tests against an instance of the "
                                                 "community implementation of the Fedora API specification.")
    parser.add_argument('-c', '--' + TestConstants.CONFIG_FILE_PARAM, dest=TestConstants.CONFIG_FILE_PARAM,
                        help="Location of the configuration file")
    parser.add_argument('-n', '--' + TestConstants.SITE_NAME_PARAM, dest=TestConstants.SITE_NAME_PARAM,
                        default="default", help="Select a specific site from your Yaml config file.")
    parser.add_argument('-b', '--' + TestConstants.BASE_URL_PARAM, dest=TestConstants.BASE_URL_PARAM,
                        help="Base url of the Fedora repository.")
    parser.add_argument('-a', '--' + TestConstants.ADMIN_USER_PARAM, dest=TestConstants.ADMIN_USER_PARAM,
                        help="Admin username")
    parser.add_argument('-s', '--' + TestConstants.ADMIN_PASS_PARAM, dest=TestConstants.ADMIN_PASS_PARAM,
                        help="Admin password")
    parser.add_argument('-u', '--' + TestConstants.USER_NAME_PARAM, dest=TestConstants.USER_NAME_PARAM,
                        help="First regular username")
    parser.add_argument('-p', '--' + TestConstants.USER_PASS_PARAM, dest=TestConstants.USER_PASS_PARAM,
                        help="First regular user password.")
    parser.add_argument('-j', '--' + TestConstants.USER2_NAME_PARAM, dest=TestConstants.USER2_NAME_PARAM,
                        help="Second regular username")
    parser.add_argument('-k', '--' + TestConstants.USER2_PASS_PARAM, dest=TestConstants.USER2_PASS_PARAM,
                        help="Second regular user password")
    parser.add_argument('-t', '--tests', dest="selected_tests", help='Comma separated list of which tests to run from '
                        '{0}. Defaults to running all tests'.format(", ".join(CSVAction.valid_options)),
                        default=['all'], type=csv_list, action=CSVAction)

    args = parser.parse_args()
    tests = FedoraTestRunner()
    tests.main(args)
