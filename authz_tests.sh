#!/bin/bash

if [ -f "./config" ]; then
 . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_authz"

checkForReTest $PARENT

# Tests
echo "Checking that authZ is enabled"
RANDOM=$(openssl rand -hex 16)

HTTP_RES=$(curl $CURL_OPTS -XGET -u${RANDOM}:${RANDOM} ${FEDORA_URL})
resultCheck 401 $HTTP_RES

echo "Create \"cover\" container"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/cover)
resultCheck 201 $HTTP_RES

echo "Make \"cover\" a pcdm:Object"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: application/sparql-update" --data-binary "@${RSCDIR}/cover2pcdmObject.sparql" ${FEDORA_URL}${PARENT}/cover)
resultCheck 204 $HTTP_RES

echo "Checking for pcdm:Object"
NS=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/cover | grep -e '@prefix \([a-z0-9]\+\): <http://pcdm.org/models#> ' | cut -d' ' -f2)
if [ -n "$NS" ]; then
  TYPE=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/cover | grep -e "${NS}Object")
  if [ -n "$TYPE" ]; then
    echo "Found type matching namespace ${NS}Object (Pass)"
  else
    echo "Did not find pcdm:Object in RDF"
    exit 1
  fi
else
  echo "Did not find PCDM namespace in returned RDF"
  exit 1
fi

echo "Create \"files\" inside \"cover\""
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/cover/files)
resultCheck 201 $HTTP_RES

echo "Create \"my-acls\" at root level"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/my-acls)
resultCheck 201 $HTTP_RES

echo "Create \"acl\" inside \"my-acls\""
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/my-acls/acl)
resultCheck 201 $HTTP_RES

echo "Create \"authorization\" inside \"acl\""
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/my-acls/acl/authorization)
resultCheck 201 $HTTP_RES

echo "Define \"authorization\""
HTTP_RES=$(sed "s/acl:agent \"adminuser\"/acl:agent \"${AUTH2_USER}\"/g" ${RSCDIR}/authorization.sparql | curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: application/sparql-update" --data-binary "@-" ${FEDORA_URL}${PARENT}/my-acls/acl/authorization)
resultCheck 204 $HTTP_RES

echo "Link \"acl\" to \"cover\""
HTTP_RES=$(sed -e "s~{{FEDORA_PATH}}~${FEDORA_PATH}~" ${RSCDIR}/link_acl_patch.sparql | curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: application/sparql-update" --upload-file - ${FEDORA_URL}${PARENT}/cover)
resultCheck 204 $HTTP_RES

echo "verifyAuthZ"
echo "Anonymous can't access \"cover\""
HTTP_RES=$(curl $CURL_OPTS -XGET ${FEDORA_URL}${PARENT}/cover)
resultCheck 401 $HTTP_RES

echo "fedoraAdmin can access \"cover\""
HTTP_RES=$(curl $CURL_OPTS -u${AUTH_USER}:${AUTH_PASS} -XGET ${FEDORA_URL}${PARENT}/cover)
resultCheck 200 $HTTP_RES

echo "adminuser can access \"cover\""
HTTP_RES=$(curl $CURL_OPTS -u${AUTH2_USER}:${AUTH2_PASS} -XGET ${FEDORA_URL}${PARENT}/cover)
resultCheck 200 $HTTP_RES

echo "testuser can't access \"cover\""
HTTP_RES=$(curl $CURL_OPTS -u${AUTH3_USER}:${AUTH3_PASS} -XGET ${FEDORA_URL}${PARENT}/cover)
resultCheck 403 $HTTP_RES

echo "All tests completed"
cleanUpTests "$PARENT"
