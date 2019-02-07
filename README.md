# Fedora 4 Tests

These python tests are meant to be run against a standalone Fedora 4 instance. 

This will create, update and delete resources in the repository. So you may **not** want to use it on a production instance.

Also, this is doing a cursory test. It does some verification of RDF, and patches are always welcome.

Note: in order to test authorization, please first verify that your Fedora repository in configured to use authorization.
Check the `repository.json` in use, and verify that the `security` block contains a `providers` list such as:

    "providers" : [
        { "classname" : "org.fcrepo.auth.common.ServletContainerAuthenticationProvider" }
    ]

## Installation

This has been designed for Python 3, but should be backwards compatible.

To install:
1. Clone this directory
1. In the fcrepo4-tests directory run 
    * `pip install -r requirements.txt` for python 2.*
    * `pip3 install -r requirements.txt` for python 3.*
    
    to install dependencies
1. Run the tests with the config file switch (`-c`), ie. `./testrunner.py -c config.yml.example`

## Usage

The `testrunner.py` has many configuration options, but essentially it needs to know.
1. The base URL of your Fedora
1. The Admin username
1. The Admin password
1. A second user's name
1. A second user's password
1. A third user's name
1. A third user's password

The `config.yml.example` has an example setup for a default Fedora running with `mvn jetty:run`

To see all options run
```
./testrunner.py --help
```

### Multiple configurations

You can store multiple configurations in one config file, then you can use the `-n|--site_name` option to choose a 
different configuration.

For example, with this `config.yml`

```
default:
  baseurl: http://localhost:8080/rest 
  admin_user: fedoraAdmin
  admin_password: fedoraAdmin 
  user1: testuser
  password1: testpass 
  user2: testuser2
  password2: testpass
second_site:
  baseurl: http://someserver:8080/fcrepo/rest 
  admin_user: theBoss
  admin_password: bossesPW
  user1: user1
  password1: password1
  user2: user2
  password2: password2
```

To use the `second_site` configuration, simply start the testrunner with
```
./testrunner.py -c config.yml -n second_site
``` 

If a configuration cannot be found or the `-n|--site_name` argument is not present we default to the `default` profile.

### Isolate tests
You can also choose to run only a subset of all tests using the `-t|--tests` argument. It accepts a comma separated list
of the following values which indicate which tests to run.
* `authz` - Authorization tests
* `basic` - Basic interaction tests
* `sparql` - Sparql operation tests
* `rdf` - RDF serialization tests
* `version` - Versioning tests
* `transaction` - Transcation tests
* `fixity` - Binary fixity tests

Without this parameter all the above tests will be run.

To run only the `authz` and `sparql` tests you would execute:
```
./testrunner.py -c config.yml -t authz,sparql
```

## Tests implemented

### authz
1. Create a container called **cover**
1. Patch it to a pcdm:Object
1. Verify no ACL exists
1. Add an ACL to **cover**
1. Create a container inside **cover** called **files**
1. Verify Anonymous can't access **cover**
1. Verify admin user can access **cover**
1. Verify regular user 1 can access **cover**
1. Verify regular user 2 can't access **cover**

### basic
1. Create a container
1. Create a container inside the container from step 1
1. Create a binary inside the container from step 2
1. Delete the binary
1. Delete the container from step 1
1. Create a LDP Basic container
1. Validate the correct Link header type
1. Create a LDP Direct container
1. Validate the correct Link header type
1. Create a LDP Indirect container
1. Validate the correct Link header type

### fixity
1. Create a binary resource
1. Get a fixity result for that resource
1. Compare that the SHA-1 hash matches the expected value

### sparql
1. Create a container
1. Set the dc:title of the container with a Patch request
1. Update the dc:title of the container with a Patch request
1. Verify the title
1. Create a binary
1. Set the dc:title of the binary with a Patch request
1. Update the dc:title of the binary with a Patch request
1. Verify the title
1. Create a container
1. Update the title to text with Unicode characters
1. Verify the title 

### transaction
1. Create a transaction
2. Get the status of the transaction
3. Create a container in the transaction
4. Verify the container is available in the transaction
5. Verify the container is **not** available outside the transaction
6. Commit the transaction
7. Verify the container is now available outside the transaction
8. Create a second transaction
3. Create a container in the transaction
4. Verify the container is available in the transaction
5. Verify the container is **not** available outside the transaction
6. Rollback the transaction
7. Verify the container is still **not** available outside the transaction

### version
1. Create a container
1. Check for versions of the container
1. Create a version of the container with existing body
1. Create a version of the container with specific datetime
1. Try to create a version of the container with the same datetime
1. Update the container with a PATCH request
1. Try to PATCH the Memento
1. Create another version of the container with existing body
1. Count number of versions
1. Delete a version
1. Verify deletion
1. Count number of versions again
1. Create Memento at deleted memento's datetime
1. Verify Memento exists

### indirect
1. Create a pcdm:Object
2. Create a pcdm:Collection
3. Create an indirect container "members" inside the pcdm:Collection
4. Create a proxy object for the pcdm:Object inside the **members** indirectContainer
5. Verify that the pcdm:Collection has the memberRelation property added pointing to the pcdm:Object
