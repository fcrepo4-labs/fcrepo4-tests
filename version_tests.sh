#!/bin/bash

if [ -f "./config" ]; then
 . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_versioning"

checkForReTest $PARENT

echo "Container tests\n\n"
echo "Create a container"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: ${TURTLE}" --data-binary "@${RSCDIR}/object.ttl" ${FEDORA_URL}${PARENT}/object1)
resultCheck 201 $HTTP_RES

echo "Check for versions of the container"
HTTP_RES=$(curl $CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheck 404 $HTTP_RES

if [ -f "${TEMP_DIR}/version1" ]; then
  `rm ${TEMP_DIR}/version1`
fi

echo "Enable versioning"
BODY=$(curl -s -o "${TEMP_DIR}/version1" -XGET -u${AUTH_USER}:${AUTH_PASS} -H"${PREFER_OMIT_SERVER_MANAGED}" -H"Accept: ${TURTLE}" ${FEDORA_URL}${PARENT}/object1)
if [ ! -f "${TEMP_DIR}/version1" ]; then
  echo "ERROR: Unable to save the RDF to your \$TEMP_DIR ($TEMP_DIR), cannot continue"
  exit 1 
fi
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"${PREFER_LENIENT}" -H"Content-type: ${TURTLE}" -H"Link: <${VERSIONED_RESOURCE}>;rel=\"type\"" -d"@${TEMP_DIR}/version1" ${FEDORA_URL}${PARENT}/object1)
resultCheck 204 $HTTP_RES
if [ -f "${TEMP_DIR}/version1" ]; then
  `rm ${TEMP_DIR}/version1`
fi

echo "Check for versions of the container"
HTTP_RES=$(curl $CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheck 200 $HTTP_RES

echo "Create a version of the container"
HTTP_RES=$(curl $CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheck 201 $HTTP_RES

BODY=$(curl -s -o "${TEMP_DIR}/version1" -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: ${TURTLE}" ${FEDORA_URL}${PARENT}/object1)
if [ ! -f "${TEMP_DIR}/version1" ]; then
  echo "ERROR: Unable to save the RDF to your \$TEMP_DIR, cannot continue"
  exit 1 
fi

DATE=$(buildRfcDate 2000 06 1 8 21 00)
echo "Make a version with a specific datetime"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"${PREFER_LENIENT}" -H"Content-type: ${TURTLE}" -H"Memento-Datetime: ${DATE}" -d"@${TEMP_DIR}/version1" ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheckInHeaders 201 "$HTTP_RES"
MEMENTO_LOCATION=$(getLocationFromHeaders "$HTTP_RES")

echo "Try to create a version of the container with the same date"
HTTP_RES=$(curl $CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"${PREFER_LENIENT}" -H"Content-type: ${TURTLE}" -H"Memento-Datetime: ${DATE}" -d"@${TEMP_DIR}/version1" ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheck 409 $HTTP_RES

echo "Check Memento exists"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${MEMENTO_LOCATION})
resultCheckInHeaders 200 "$HTTP_RES"
Expected_date=$( echo "$DATE" | sed -Ee 's/\+[0-9]{4}/GMT/')
validateMementoDatetime "$Expected_date" "$HTTP_RES"

echo "Update the container with a Patch request"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: ${SPARQL_UPDATE}" --data-binary "@${RSCDIR}/update_title.sparql" ${FEDORA_URL}${PARENT}/object1)
resultCheck 204 $HTTP_RES

echo "Try to PATCH a memento"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: ${SPARQL_UPDATE}" --data-binary "@${RSCDIR}/update_title.sparql" ${MEMENTO_LOCATION})
resultCheck 405 $HTTP_RES

# Need to delay or it will give a 409 for having two Mementos for the same second.
sleep 1

echo "Create another version of the container"
HTTP_RES=$(curl $CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheck 201 $HTTP_RES

echo "Count versions"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: application/link-format" ${FEDORA_URL}${PARENT}/object1/fcr:versions)
COUNT=$(countMementos "$HTTP_RES")
resultCheck 3 $COUNT

echo "Delete a Memento"
HTTP_RES=$(curl $CURL_OPTS -XDELETE -u${AUTH_USER}:${AUTH_PASS} ${MEMENTO_LOCATION})
resultCheck 204 $HTTP_RES

echo "Validate delete with count of versions"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: application/link-format" ${FEDORA_URL}${PARENT}/object1/fcr:versions)
COUNT=$(countMementos "$HTTP_RES")
resultCheck 2 $COUNT

echo "Try to put a version with the delete datetime"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"${PREFER_LENIENT}" -H"Content-type: ${TURTLE}" -H"Memento-Datetime: ${DATE}" -d"@${TEMP_DIR}/version1" ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheckInHeaders 201 "$HTTP_RES"
MEMENTO_LOCATION=$(getLocationFromHeaders "$HTTP_RES")

echo "Get the Memento"
HTTP_RES=$(curl $CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${MEMENTO_LOCATION})
resultCheck 200 $HTTP_RES

if [ -f "${TEMP_DIR}/version1" ]; then
  `rm ${TEMP_DIR}/version1`
fi

echo "Binary tests\n\n"
echo "Create a binary"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: image/jpeg" --data-binary "@${RSCDIR}/basic_image.jpg" ${FEDORA_URL}${PARENT})
resultCheckInHeaders 201 "$HTTP_RES"
LOCATION=$(getLocationFromHeaders "$HTTP_RES")

echo "Check for versions of the binary"
HTTP_RES=$(curl $CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${LOCATION}/fcr:versions)
resultCheck 404 $HTTP_RES

echo "Check for versions of the binary description"
HTTP_RES=$(curl $CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${LOCATION}/fcr:metadata/fcr:versions)
resultCheck 404 $HTTP_RES

echo "Enable versioning on the binary"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"${PREFER_LENIENT}" -H"Content-type: image/jpeg" -H"Link: <${VERSIONED_RESOURCE}>;rel=\"type\"" -d"@${TEMP_DIR}/basic_image" ${LOCATION})
resultCheck 204 $HTTP_RES

echo "Check for versions of the binary"
HTTP_RES=$(curl $CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${LOCATION}/fcr:versions)
resultCheck 200 $HTTP_RES

echo "Create a version of the binary"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} ${LOCATION}/fcr:versions)
resultCheckInHeaders 201 "$HTTP_RES"
MEMENTO_LOCATION=$(getLocationFromHeaders "$HTTP_RES")
MEMENTO_DESC_LOCATION=$( echo "$MEMENTO_LOCATION" | sed -e 's/fcr:versions/fcr:metadata\/fcr:versions/' )

echo "Get the Memento"
HTTP_RES=$(curl $CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${MEMENTO_LOCATION})
resultCheck 200 $HTTP_RES

echo "Get the Description Memento"
HTTP_RES=$(curl $CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${MEMENTO_DESC_LOCATION})
resultCheck 200 $HTTP_RES

echo "Try to PUT the binary memento"
echo "curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H\"Content-type: image/jpeg\" --data-binary \"@${RSCDIR}/basic_image.jpg\" ${MEMENTO_LOCATION}"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: image/jpeg" --data-binary "@${RSCDIR}/basic_image.jpg" ${MEMENTO_LOCATION})
resultCheck 405 $HTTP_RES

echo "Try to PATCH the binary memento description"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: ${SPARQL_UPDATE}" --data-binary "@${RSCDIR}/update_title.sparql" ${MEMENTO_DESC_LOCATION})
resultCheck 405 $HTTP_RES

echo "Create a specific datetime version of binary"
DATE=$(buildRfcDate 2000 05 23 17 34 45)
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: image/jpeg" -H"Memento-Datetime: ${DATE}" --data-binary "@${RSCDIR}/basic_image.jpg" ${LOCATION}/fcr:versions)
resultCheckInHeaders 201 "$HTTP_RES"
MEMENTO_LOCATION=$(getLocationFromHeaders "$HTTP_RES")
MEMENTO_DESC_LOCATION=$( echo "$MEMENTO_LOCATION" | sed -e 's/fcr:versions/fcr:metadata\/fcr:versions/' )

echo "Try to create another binary version with same datetime"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: image/jpeg" -H"Memento-Datetime: ${DATE}" --data-binary "@${RSCDIR}/basic_image.jpg" ${LOCATION}/fcr:versions)
resultCheckInHeaders 409 "$HTTP_RES"

echo "Check Memento exists"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${MEMENTO_LOCATION})
resultCheckInHeaders 200 "$HTTP_RES"
Expected_date=$( echo "$DATE" | sed -Ee 's/\+[0-9]{4}/GMT/')
validateMementoDatetime "$Expected_date" "$HTTP_RES"

echo "Check description does NOT exist"
HTTP_RES=$(curl $CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${MEMENTO_DESC_LOCATION})
resultCheck 404 $HTTP_RES

if [ -f "${TEMP_DIR}/memento_desc1" ]; then
  `rm ${TEMP_DIR}/memento_desc1`
fi
HTTP_RES=$(curl -s -XGET -u${AUTH_USER}:${AUTH_PASS} -o "${TEMP_DIR}/memento_desc1" -H"Accept: ${TURTLE}" ${LOCATION}/fcr:metadata)
if [ ! -f "${TEMP_DIR}/memento_desc1" ]; then
  echo "ERROR: Unable to save the RDF to your \$TEMP_DIR ($TEMP_DIR), cannot continue"
  exit 1
fi

echo "Putting the binary description body for the previous Memento"
HTTP_RES=$(curl $CURL_OPTS -POST -u${AUTH_USER}:${AUTH_PASS} -H"${PREFER_LENIENT}" -H"Content-type: ${TURTLE}" --data-binary "@${TEMP_DIR}/memento_desc1" -H"Memento-Datetime: ${DATE}" ${LOCATION}/fcr:metadata/fcr:versions)
resultCheck 201 "$HTTP_RES"

echo "Now the description memento exists"
HTTP_RES=$(curl $CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${MEMENTO_DESC_LOCATION})
resultCheck 200 $HTTP_RES

echo "Count versions of binary"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: application/link-format" ${LOCATION}/fcr:versions)
COUNT=$(countMementos "$HTTP_RES")
resultCheck 2 $COUNT

echo "Count versions of binary description"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: application/link-format" ${LOCATION}/fcr:metadata/fcr:versions)
COUNT=$(countMementos "$HTTP_RES")
resultCheck 2 $COUNT



echo "Delete a binary memento"
HTTP_RES=$(curl $CURL_OPTS -XDELETE -u${AUTH_USER}:${AUTH_PASS} ${MEMENTO_LOCATION})
resultCheck 204 $HTTP_RES

echo "Count versions of binary"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: application/link-format" ${LOCATION}/fcr:versions)
COUNT=$(countMementos "$HTTP_RES")
resultCheck 1 $COUNT

echo "Count versions of binary description"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: application/link-format" ${LOCATION}/fcr:metadata/fcr:versions)
COUNT=$(countMementos "$HTTP_RES")
resultCheck 1 $COUNT

echo "Putting a new binary body to the deleted datetime"
HTTP_RES=$(curl $CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: image/jpeg" -H"Memento-Datetime: ${DATE}" --data-binary "@${RSCDIR}/basic_image.jpg" ${LOCATION}/fcr:versions)
resultCheck 201 "$HTTP_RES"

echo "Count versions of binary"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: application/link-format" ${LOCATION}/fcr:versions)
COUNT=$(countMementos "$HTTP_RES")
resultCheck 2 $COUNT

echo "Count versions of binary description"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: application/link-format" ${LOCATION}/fcr:metadata/fcr:versions)
COUNT=$(countMementos "$HTTP_RES")
resultCheck 1 $COUNT



echo "Putting the binary description body for the previous Memento"
HTTP_RES=$(curl $CURL_OPTS -POST -u${AUTH_USER}:${AUTH_PASS} -H"${PREFER_LENIENT}" -H"Content-type: ${TURTLE}" --data-binary "@${TEMP_DIR}/memento_desc1" -H"Memento-Datetime: ${DATE}" ${LOCATION}/fcr:metadata/fcr:versions)
resultCheck 201 "$HTTP_RES"

echo "Delete a binary description memento"
HTTP_RES=$(curl $CURL_OPTS -XDELETE -u${AUTH_USER}:${AUTH_PASS} ${MEMENTO_DESC_LOCATION})
resultCheck 204 $HTTP_RES

echo "Count versions of binary"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: application/link-format" ${LOCATION}/fcr:versions)
COUNT=$(countMementos "$HTTP_RES")
resultCheck 2 $COUNT

echo "Count versions of binary description"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: application/link-format" ${LOCATION}/fcr:metadata/fcr:versions)
COUNT=$(countMementos "$HTTP_RES")
resultCheck 1 $COUNT

echo "Putting a new binary description body to the deleted datetime"
echo "curl $CURL_OPTS -POST -u${AUTH_USER}:${AUTH_PASS} -H\"${PREFER_LENIENT}\" -H\"Content-type: ${TURTLE}\" --data-binary \"@${TEMP_DIR}/memento_desc1\" -H\"Memento-Datetime: ${DATE}\" ${LOCATION}/fcr:metadata/fcr:versions"
HTTP_RES=$(curl $CURL_OPTS -POST -u${AUTH_USER}:${AUTH_PASS} -H"${PREFER_LENIENT}" -H"Content-type: ${TURTLE}" --data-binary "@${TEMP_DIR}/memento_desc1" -H"Memento-Datetime: ${DATE}" ${LOCATION}/fcr:metadata/fcr:versions)
resultCheck 201 "$HTTP_RES"

echo "Count versions of binary"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: application/link-format" ${LOCATION}/fcr:versions)
COUNT=$(countMementos "$HTTP_RES")
resultCheck 2 $COUNT

echo "Count versions of binary description"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: application/link-format" ${LOCATION}/fcr:metadata/fcr:versions)
COUNT=$(countMementos "$HTTP_RES")
resultCheck 2 $COUNT



echo "All tests completed"
cleanUpTests "$PARENT"
