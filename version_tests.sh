#!/bin/bash

if [ -f "./config" ]; then
 . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_versioning"

checkForReTest $PARENT

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
  echo "ERROR: Unable to save the RDF to your \$TEMP_DIR, cannot continue"
  exit 1 
fi
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"${PREFER_LENIENT}" -H"Content-type: ${TURTLE}" -H"Link: <${VERSIONED_RESOURCE}>;rel=\"type\"" -d"@${TEMP_DIR}/version1" ${FEDORA_URL}${PARENT}/object1)
resultCheck 204 $HTTP_RES
if [ -f "${TEMP_DIR}/version1" ]; then
  `rm ${TEMP_DIR}/version1`
fi

echo "Create a version of the container"
HTTP_RES=$(curl $CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheck 201 $HTTP_RES

BODY=$(curl -s -o "${TEMP_DIR}/version1" -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: ${TURTLE}" ${FEDORA_URL}${PARENT}/object1)
if [ ! -f "${TEMP_DIR}/version1" ]; then
  echo "ERROR: Unable to save the RDF to your \$TEMP_DIR, cannot continue"
  exit 1 
fi

echo "Make a version with a specific datetime"
HTTP_RES=$(curl $CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"${PREFER_LENIENT}" -H"Content-type: ${TURTLE}" -H"Memento-Datetime: Thu, 01 Jun 2000 08:00:00 +0000" -d"@${TEMP_DIR}/version1" ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheck 201 $HTTP_RES

echo "Try to create a version of the container with the same date"
HTTP_RES=$(curl $CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} -H"${PREFER_LENIENT}" -H"Content-type: ${TURTLE}" -H"Memento-Datetime: Thu, 01 Jun 2000 08:00:00 +0000" -d"@${TEMP_DIR}/version1" ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheck 409 $HTTP_RES

echo "Update the container with a Patch request"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: ${SPARQL_UPDATE}" --data-binary "@${RSCDIR}/update_title.sparql" ${FEDORA_URL}${PARENT}/object1)
resultCheck 204 $HTTP_RES

# Need to delay or it will give a 409 for having two Mementos for the same second.
sleep 1

echo "Create another version of the container"
HTTP_RES=$(curl $CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1/fcr:versions)
resultCheck 201 $HTTP_RES

echo "Count versions"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: application/link-format" ${FEDORA_URL}${PARENT}/object1/fcr:versions)
COUNT=$(countMementos "$HTTP_RES")
if [ $COUNT -ne 3 ]; then
  echo "ERROR: Memento count error. Expected 3, actual ${COUNT}"
  return 1
else
  echo "3 == ${COUNT} (Pass)"
fi

echo "Try to PATCH a memento"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: ${SPARQL_UPDATE}" --data-binary "@${RSCDIR}/update_title.sparql" ${FEDORA_URL}${PARENT}/object1/fcr:versions/20000601080000)
resultCheck 405 $HTTP_RES

echo "Delete a Memento"
HTTP_RES=$(curl $CURL_OPTS -XDELETE -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/object1/fcr:versions/20000601080000)
resultCheck 204 $HTTP_RES

echo "Validate delete with count of versions"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} -H"Accept: application/link-format" ${FEDORA_URL}${PARENT}/object1/fcr:versions)
COUNT=$(countMementos "$HTTP_RES")
if [ $COUNT -ne 2 ]; then
  echo "ERROR: Memento count error. Expected 2, actual ${COUNT}"
  return 1
else
  echo "2 == ${COUNT} (Pass)"
fi

if [ -f "${TEMP_DIR}/version1" ]; then
  `rm ${TEMP_DIR}/version1`
fi

echo "All tests completed"
cleanUpTests "$PARENT"
