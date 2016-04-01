#!/bin/sh

if [ -f "./config" ]; then
  . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_nested"

HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT})
if [ "$HTTP_RES" != "201" ]; then
  if [ "$HTTP_RES" == "000" ]; then
    echo "Attempted to run test but received odd results (HTTP status of $HTTP_RES). Is Fedora4 running?"
    exit 1
  else
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
fi

# Tests
echo "Create an object"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --data-binary "@${RSCDIR}/object.ttl" ${FEDORA_URL}${PARENT}/object1)
resultCheck 201 $HTTP_RES
echo "OK"

echo "Create an object in an object"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --data-binary "@${RSCDIR}/object.ttl" ${FEDORA_URL}${PARENT}/object1/object2)
resultCheck 201 $HTTP_RES
echo "OK"

echo "Create binary inside an object inside an object"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: image/jpeg" --data-binary "@${RSCDIR}/basic_image.jpg" ${FEDORA_URL}${PARENT}/object1/object2/picture)
resultCheck 201 $HTTP_RES
echo "OK"

