#!/bin/sh

if [ -f "./config" ]; then
 . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_fixity"

checkForReTest $PARENT

# Tests
echo "Create a binary"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: image/jpeg" --data-binary "@${RSCDIR}/basic_image.jpg" ${FEDORA_URL}${PARENT}/image)
resultCheck 201 $HTTP_RES

echo "Get a fixity result"
HTTP_RES=$(curl $CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/image/fcr:fixity)
resultCheck 200 $HTTP_RES

echo "All tests completed"
read -p "Remove any test objects created? (Y/n) " DELETE
if [ "$DELETE" == "y" ] || [ "$DELETE" == 'y' ] || [ "$DELETE" == "" ]; then
  cleanUpPath "$PARENT"
fi
