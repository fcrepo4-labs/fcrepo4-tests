#!/bin/bash

if [ -f "./config" ]; then
 . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_fixity"

FIXITY_RESULT="<urn:sha1:dec028a4400b4f7ed80ed1174e65179d6b57a0f2>"

checkForReTest $PARENT

# Tests
echo "Create a binary"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: image/jpeg" --data-binary "@${RSCDIR}/basic_image.jpg" ${FEDORA_URL}${PARENT}/image)
resultCheck 201 $HTTP_RES

echo "Get a fixity result"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/image/fcr:fixity)
resultCheckInHeaders 200 "$HTTP_RES"
TEMP=( $(echo "$HTTP_RES" | grep 'premis:hasMessageDigest' | sed -e 's/^[[:blank:]]*//' -e 's/[[:blank:]]*$//') )
FIXITY=${TEMP[1]}


if [ -z "$FIXITY" ]; then
  echo "ERROR: Fixity result not found"
  echo "Please check ${FEDORA_URL}${PARENT}/image/fcr:fixity manually."
  exit 1
elif [ "$FIXITY" == "$FIXITY_RESULT" ]; then
  echo "Fixity result found and matches expected result"
  echo "(${FIXITY}) == (${FIXITY_RESULT})" 
else
  echo "ERROR: Unknown fixity error. Please compare the fixity results manually"
  echo "Please check ${FEDORA_URL}${PARENT}/image/fcr:fixity manually."
  exit 1
fi

echo "All tests completed"
cleanUpTests "$PARENT"
