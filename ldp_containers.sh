#!/bin/bash

if [ -f "./config" ]; then
  . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_ldp_containers"

checkForReTest $PARENT

echo "Create a Basic Container"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" -H"Link: <${LDP_BASIC}>; rel=\"type\"" -H"Slug: basicContainer" --data-binary "@${RSCDIR}/basic_container.ttl" ${FEDORA_URL}${PARENT})
resultCheckInHeaders 201 "$HTTP_RES"
getLocationFromHeaders "$HTTP_RES"

HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: ${JSONLD_MIMETYPE}" ${LOCATION})
resultCheckInHeaders 200 "$HTTP_RES"
assertLinkHeader "<$LDP_BASIC>;rel=\"type\"" "$HTTP_RES"

echo "Create a Direct Container"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" -H"Link: <${LDP_DIRECT}>; rel=\"type\"" -H"Slug: directContainer" --data-binary "@${RSCDIR}/direct_container.ttl" ${FEDORA_URL}${PARENT})
resultCheckInHeaders 201 "$HTTP_RES"
getLocationFromHeaders "$HTTP_RES"

HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: ${JSONLD_MIMETYPE}" ${LOCATION})
resultCheckInHeaders 200 "$HTTP_RES"
assertLinkHeader "<$LDP_DIRECT>;rel=\"type\"" "$HTTP_RES"

HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" -H"Link: <${LDP_INDIRECT}>; rel=\"type\"" -H"Slug: indirectContainer" --data-binary "@${RSCDIR}/indirect_container.ttl" ${FEDORA_URL}${PARENT})
resultCheckInHeaders 201 "$HTTP_RES"
getLocationFromHeaders "$HTTP_RES"

HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: ${JSONLD_MIMETYPE}" ${LOCATION})
resultCheckInHeaders 200 "$HTTP_RES"
assertLinkHeader "<$LDP_INDIRECT>;rel=\"type\"" "$HTTP_RES"


echo "All tests completed"
cleanUpTests "$PARENT"
