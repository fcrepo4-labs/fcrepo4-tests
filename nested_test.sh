#!/bin/sh

if [ -f "./config" ]; then
  . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_nested"

checkForReTest $PARENT

# Tests
echo "Create an container"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --data-binary "@${RSCDIR}/object.ttl" ${FEDORA_URL}${PARENT}/object1)
resultCheck 201 $HTTP_RES

echo "Create an container in an container"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --data-binary "@${RSCDIR}/object.ttl" ${FEDORA_URL}${PARENT}/object1/object2)
resultCheck 201 $HTTP_RES

echo "Create binary inside an container inside an container"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: image/jpeg" --data-binary "@${RSCDIR}/basic_image.jpg" ${FEDORA_URL}${PARENT}/object1/object2/picture)
resultCheck 201 $HTTP_RES

echo "Delete binary"
HTTP_RES=$(curl $CURL_OPTS -XDELETE -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1/object2/picture)
resultCheck 204 $HTTP_RES

echo "Delete container with an container inside it"
HTTP_RES=$(curl $CURL_OPTS -XDELETE -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1)
resultCheck 204 $HTTP_RES

echo "All Tests Completed"
