#!/bin/sh

if [ -f "./config" ]; then
 . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_versioning"

checkForReTest $PARENT

CUSTOM_CURL_OPTS="-s --no-keepalive -i"

echo "Create an container"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --data-binary "@${RSCDIR}/object.ttl" ${FEDORA_URL}${PARENT}/object1)
resultCheck 201 $HTTP_RES

echo "Check for versions of the container"
HTTP_RES=$(curl $CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheck 404 $HTTP_RES

echo "Create a version of the container"
HTTP_RES=$(curl $CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"Slug: version1" ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheck 201 $HTTP_RES

echo "Try to create a version of the container with the same label"
HTTP_RES=$(curl $CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"Slug: version1" ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheck 409 $HTTP_RES

echo "Update the container with a Patch request"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: application/sparql-update" --data-binary "@${RSCDIR}/update_title.sparql" ${FEDORA_URL}${PARENT}/object1)
resultCheck 204 $HTTP_RES

echo "Create another version of the container"
HTTP_RES=$(curl $CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"Slug: version2" ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheck 201 $HTTP_RES

echo "Try to delete the current version"
HTTP_RES=$(curl $CURL_OPTS -XDELETE -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1/fcr:versions/version2)
resultCheck 400 $HTTP_RES

echo "Revert to previous version"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1/fcr:versions/version1)
resultCheck 204 $HTTP_RES

echo "Delete the newer version"
HTTP_RES=$(curl $CURL_OPTS -XDELETE -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1/fcr:versions/version2)
resultCheck 204 $HTTP_RES

echo "All tests completed"
