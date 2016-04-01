#!/bin/sh

if [ -f "./config" ]; then
  . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_nested"

checkForReTest $PARENT

# Tests
echo "Create a container"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --data-binary "@${RSCDIR}/object.ttl" ${FEDORA_URL}${PARENT}/object1)
resultCheck 201 $HTTP_RES

echo "Create a container in a container"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --data-binary "@${RSCDIR}/object.ttl" ${FEDORA_URL}${PARENT}/object1/object2)
resultCheck 201 $HTTP_RES

echo "Create binary inside a container inside a container"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: image/jpeg" --data-binary "@${RSCDIR}/basic_image.jpg" ${FEDORA_URL}${PARENT}/object1/object2/picture)
resultCheck 201 $HTTP_RES

echo "Delete binary"
HTTP_RES=$(curl $CURL_OPTS -XDELETE -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1/object2/picture)
resultCheck 204 $HTTP_RES

echo "Delete container with a container inside it"
HTTP_RES=$(curl $CURL_OPTS -XDELETE -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1)
resultCheck 204 $HTTP_RES

echo "All Tests Completed"
read -p "Remove any test objects created? (Y/n) " DELETE
if [ "$DELETE" == "y" ] || [ "$DELETE" == 'y' ] || [ "$DELETE" == "" ]; then
  cleanUpPath "$PARENT"
fi
