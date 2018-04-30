#!/bin/bash

if [ -f "./config" ]; then
 . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_rdf"

checkForReTest $PARENT

echo "Post RDF and check a property"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XPOST -H"Content-type: ${TURTLE}" --data-binary "@${RSCDIR}/object.ttl" -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT})
resultCheckInHeaders 201 "$HTTP_RES"
LOCATION=$(getLocationFromHeaders "$HTTP_RES")
checkTitle "An Object" $LOCATION

echo "Update with Prefer: handling=lenient and check the property was updated"
HTTP_RES=$(curl $CURL_OPTS -u${AUTH_USER}:${AUTH_PASS} -XPUT -H"${PREFER_LENIENT}" -H"Content-type: application/n-triples" --data-binary "<${LOCATION}> <http://purl.org/dc/elements/1.1/title> \"Updated Title\" ." ${LOCATION})
resultCheck 204 $HTTP_RES
checkTitle "Updated Title" $LOCATION

echo "Retrieve RDF in a variety of formats"
RDF_VARIANTS="text/turtle;charset=utf-8 application/rdf+xml;charset=utf-8 application/ld+json;charset=utf-8 application/n-triples;charset=utf-8 text/n3;charset=utf-8"
for MIME in $RDF_VARIANTS; do
  HTTP_RES=$(curl $CUSTOM_CURL_OPTS -u"${AUTH_USER}:${AUTH_PASS}" -H "Accept: $MIME" $LOCATION)
  resultCheckInHeaders 200 "$HTTP_RES"
  checkContentType $MIME "$HTTP_RES"
done

echo "Delete the object"
HTTP_RES=$(curl $CURL_OPTS -u${AUTH_USER}:${AUTH_PASS} -XDELETE $LOCATION)
resultCheck 204 "$HTTP_RES"

echo "Make sure it's gone"
HTTP_RES=$(curl $CURL_OPTS -u${AUTH_USER}:${AUTH_PASS} $LOCATION)
resultCheck 410 "$HTTP_RES"

cleanUpTests "$PARENT"
