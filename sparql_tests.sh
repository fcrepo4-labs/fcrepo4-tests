#!/bin/sh

if [ -f "./config" ]; then
 . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_sparql"

checkForReTest $PARENT

# Tests
echo "Create a container"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --data-binary "@${RSCDIR}/object.ttl" ${FEDORA_URL}${PARENT}/object)
resultCheck 201 $HTTP_RES

echo "Set dc:title with SPARQL"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: application/sparql-update" --data-binary "@${RSCDIR}/set_title.sparql" ${FEDORA_URL}${PARENT}/object/fcr:metadata)
resultCheck 204 $HTTP_RES

echo "Update dc:title with SPARQL"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: application/sparql-update" --data-binary "@${RSCDIR}/update_title.sparql" ${FEDORA_URL}${PARENT}/object/fcr:metadata)
resultCheck 204 $HTTP_RES

echo "Create a binary"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: image/jpeg" --data-binary "@${RSCDIR}/basic_image.jpg" ${FEDORA_URL}${PARENT}/image)
resultCheck 201 $HTTP_RES

echo "Set dc:title with SPARQL"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: application/sparql-update" --data-binary "@${RSCDIR}/set_title.sparql" ${FEDORA_URL}${PARENT}/image/fcr:metadata)
resultCheck 204 $HTTP_RES

echo "Update dc:title with SPARQL"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: application/sparql-update" --data-binary "@${RSCDIR}/update_title.sparql" ${FEDORA_URL}${PARENT}/image/fcr:metadata)
resultCheck 204 $HTTP_RES

echo "All tests completed"
cleanUpTests $PARENT
