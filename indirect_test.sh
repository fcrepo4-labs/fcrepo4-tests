#!/bin/sh

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

echo "Rewrite the indirect container turtle to use the correct fedora path and parent"
INDIRECT=$(sed -e "s|{{PCDM_COLLECTION}}|${FEDORA_PATH}${PARENT}/collection|" "${RSCDIR}/pcdm_indirect.ttl")

echo "Create an indirect container inside collection called members"
HTTP_RES=$(echo "${INDIRECT}" | curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --upload-file - ${FEDORA_URL}${PARENT}/collection/members)
resultCheck 201 $HTTP_RES

echo "Rewrite the proxyFor object turtle to use the correct fedora path and parent"
PROXY=$(sed -e "s|{{PROXY_FOR}}|${FEDORA_PATH}${PARENT}/object1|" "${RSCDIR}/pcdm_proxy.ttl")

echo "Create a proxy to the PCDM object inside members"
HTTP_RES=$(echo "$PROXY" | curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --upload-file - ${FEDORA_URL}${PARENT}/collection/members/proxy1)
resultCheck 201 $HTTP_RES

echo "Checking for pcdm:hasMember property on PCDM collection to PCDM object"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/collection)
resultCheckInHeaders 200 "$HTTP_RES"
HAS_MEMBER=$(echo "$HTTP_RES" | grep ':hasMember')
echo "has member $HAS_MEMBER"
echo "headers $HTTP_RES"

cleanUpTests $PARENT
