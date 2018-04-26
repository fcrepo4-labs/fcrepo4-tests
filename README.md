# Fedora 4 Tests

These shell scripts are meant to be run against a standalone Fedora 4 instance. 

This will create, update and delete resources in the repository. So you may **not** want to use it on a production instance.

Also, this is doing a cursory test. It relies on the response from Fedora and does not verify changes to the RDF.

Note: in order to test authorization, please first verify that your Fedora repository in configured to use authorization.
Check the `repository.json` in use, and verify that the `security` block contains a `providers` list such as:

    "providers" : [
        { "classname" : "org.fcrepo.auth.common.ServletContainerAuthenticationProvider" }
    ]

## Usage

Copy the `config.tmpl` to `config`. Then edit the `config` file and review the default variables to ensure the tests are pointing at your repository. 

Run each/all/any of the test scripts.

## Tests implemented

### nested\_tests.sh
1. Create a container
2. Create a container inside the container from step 1
3. Create a binary inside the container from step 2
4. Delete the binary
5. Delete the container from step 1

### fixity\_tests.sh
1. Create a binary resource
2. Get a fixity result for that resource
3. Compare that the SHA-1 hash matches the expected value

### sparql\_tests.sh
1. Create a container
2. Set the dc:title of the container with a Patch request
3. Update the dc:title of the container with a Patch request
4. Create a binary
2. Set the dc:title of the binary with a Patch request
3. Update the dc:title of the binary with a Patch request

### transaction\_tests.sh
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

### version\_tests.sh
1. Create a container
1. Check for versions of the container
1. Enable versioning on the container
1. Create a version of the container with existing body
1. Create a version of the container with specific datetime
1. Try to create a version of the container with the same datetime
1. Update the container with a PATCH request
1. Create another version of the container with existing body
1. Count number of versions
1. Try to PATCH a version
1. Delete a version
1. Count number of versions again

### indirect\_tests.sh
1. Create a pcdm:Object
2. Create a pcdm:Collection
3. Create an indirect container "members" inside the pcdm:Collection
4. Create a proxy object for the pcdm:Object inside the **members** indirectContainer
5. Verify that the pcdm:Collection has the memberRelation property added pointing to the pcdm:Object

### authz\_tests.sh
1. Create a container called **cover**
2. Patch it to a pcdm:Object
3. Check for the pcdm:Object in the RDF
4. Create a container inside **cover** called **files**
5. Create a container called **my-acls**
6. Create a container called **acl** inside **my-acls**
7. Create a container called **authorization** inside **acl**
8. Patch **authorization** with a WebAC Authorization.
9. Patch **cover** to add **acl** as an access control.
10. Verify Anonymous can't access **cover**
11. Verify fedoraAdmin can access **cover**
12. Verify testadmin can access **cover**
13. Verify testuser can't access **cover**

### ldp\_containers.sh
1. Create a LDP Basic container
1. Validate the correct Link header type
1. Create a LDP Direct container
1. Validate the correct Link header type
1. Create a LDP Indirect container
1. Validate the correct Link header type