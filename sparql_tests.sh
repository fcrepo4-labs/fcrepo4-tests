#!/bin/sh

if [ -f "./config" ]; then
 . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_sparql"

HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT})
if [ "$HTTP_RES" != "201" ]; then
  echo "This test has been run. You need to remove this object and all it's children before re-running the test."
  read -p "Remove the test objects and re-run? (y/N) " RERUN
  if [ "$RERUN" == "Y" ] || [ "$RERUN" == "y" ]; then
    curl -o/dev/null -s -u${AUTH_USER}:${AUTH_PASS} -XDELETE ${FEDORA_URL}${PARENT}
    curl -s -o/dev/null -u${AUTH_USER}:${AUTH_PASS} -XDELETE ${FEDORA_URL}${PARENT}/fcr:tombstone
    HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT})
  else
    exit 1
  fi
fi

# Tests
echo "Create a container"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --data-binary "@${RSCDIR}/object.ttl" ${FEDORA_URL}${PARENT}/object)
resultCheck 201 $HTTP_RES
echo "OK"

echo "Set dc:title with SPARQL"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: application/sparql-update" --data-binary "@${RSCDIR}/set_title.sparql" ${FEDORA_URL}${PARENT}/object/fcr:metadata)
resultCheck 204 $HTTP_RES
echo "OK"

echo "Update dc:title with SPARQL"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: application/sparql-update" --data-binary "@${RSCDIR}/update_title.sparql" ${FEDORA_URL}${PARENT}/object/fcr:metadata)
resultCheck 204 $HTTP_RES
echo "OK"

echo "Create a binary"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: image/jpeg" --data-binary "@${RSCDIR}/basic_image.jpg" ${FEDORA_URL}${PARENT}/image)
resultCheck 201 $HTTP_RES
echo "OK"

echo "Set dc:title with SPARQL"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: application/sparql-update" --data-binary "@${RSCDIR}/set_title.sparql" ${FEDORA_URL}${PARENT}/image/fcr:metadata)
resultCheck 204 $HTTP_RES
echo "OK"

echo "Update dc:title with SPARQL"
HTTP_RES=$(curl $CURL_OPTS -XPATCH -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: application/sparql-update" --data-binary "@${RSCDIR}/update_title.sparql" ${FEDORA_URL}${PARENT}/image/fcr:metadata)
resultCheck 204 $HTTP_RES
echo "OK"

