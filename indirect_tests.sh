#!/bin/bash

if [ -f "./config" ]; then
  . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_indirect"

checkForReTest $PARENT

# Tests
echo "Create a PCDM object"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --data-binary @${RSCDIR}/pcdm_container.ttl ${FEDORA_URL}${PARENT}/object1)
resultCheck 201 $HTTP_RES

echo "Create a PCDM Collection"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --data-binary @${RSCDIR}/pcdm_collection.ttl ${FEDORA_URL}${PARENT}/collection)
resultCheck 201 $HTTP_RES
echo "OK"

# Rewrite the indirect container turtle to use the correct fedora path and parent
INDIRECT=$(sed -e "s|{{PCDM_COLLECTION}}|${FEDORA_PATH}${PARENT}/collection|" "${RSCDIR}/pcdm_indirect.ttl")

echo "Create an indirect container inside collection called members"
HTTP_RES=$(echo "${INDIRECT}" | curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --upload-file - ${FEDORA_URL}${PARENT}/collection/members)
resultCheck 201 $HTTP_RES

# Rewrite the proxyFor object turtle to use the correct fedora path and parent
PROXY=$(sed -e "s|{{PROXY_FOR}}|${FEDORA_PATH}${PARENT}/object1|" "${RSCDIR}/pcdm_proxy.ttl")

echo "Create a proxy to the PCDM object inside members"
HTTP_RES=$(echo "$PROXY" | curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --upload-file - ${FEDORA_URL}${PARENT}/collection/members/proxy1)
resultCheck 201 $HTTP_RES

echo "Checking for pcdm:hasMember property on PCDM collection to PCDM object"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/collection)
resultCheckInHeaders 200 "$HTTP_RES"

HAS_MEMBER=$(echo "$HTTP_RES" | grep -e '\(pcdm\|ns[0-9]\+\):hasMember' | sed -e 's/^\s*//' -e 's/\s*$//' -e 's/Member\s*/Member /' | cut -d' ' -f2)
if [ -z "$HAS_MEMBER" ]; then
  echo "ERROR: Could not locate pcdm:hasMember property on Collection"
  echo "Please check ${FEDORA_URL}${PARENT}/collection manually."
  exit 1
elif [ "$HAS_MEMBER" == "<${FEDORA_URL}${PARENT}/object1>" ]; then
  echo "Found pcdm:hasMember property on Collection to Object"
else
  echo "ERROR: Unknown error finding indirect container added property on Collection"
  echo "Please check ${FEDORA_URL}${PARENT}/collection manually."
  exit 1
fi

echo "Completed all tests"
cleanUpTests $PARENT
