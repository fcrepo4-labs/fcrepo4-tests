#!/bin/bash

if [ -f "./config" ]; then
 . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_transaction"

checkForReTest $PARENT

# Tests
echo "Create a transaction"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}/fcr:tx)
resultCheckInHeaders 201 "$HTTP_RES"
if getLocationFromHeaders "$HTTP_RES"
then
  TRANSACTION=$( echo "${LOCATION}" | sed -e "s|${FEDORA_URL}||" | tr -d "\n\r")
  echo "Transaction is (${TRANSACTION})"
  
  echo "Get status of transaction"
  HTTP_RES=$(curl $CURL_OPTS -XGET -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${TRANSACTION})
  resultCheck 200 $HTTP_RES
  
  echo "Create an container in the transaction"
  HTTP_RES=$(curl $CURL_OPTS -XPUT  -u${AUTH_USER}:${AUTH_PASS}  ${FEDORA_URL}${TRANSACTION}${PARENT}/transactionObj)
  resultCheck 201 $HTTP_RES
  
  echo "Container is available inside the transaction"
  HTTP_RES=$(curl $CURL_OPTS -XGET  -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${TRANSACTION}${PARENT}/transactionObj)
  resultCheck 200 $HTTP_RES
  
  echo "Container not available outside the transaction"
  HTTP_RES=$(curl $CURL_OPTS -XGET  -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/transactionObj)
  resultCheck 404 $HTTP_RES
  
  echo "Commit transaction"
  HTTP_RES=$(curl $CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${TRANSACTION}/fcr:tx/fcr:commit)
  resultCheck 204 $HTTP_RES
  
  echo "Container is now available outside the transaction"
  HTTP_RES=$(curl $CURL_OPTS -XGET  -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/transactionObj)
  resultCheck 200 $HTTP_RES
  
fi

echo "Create a second transaction"
HTTP_RES=$(curl $CUSTOM_CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}/fcr:tx)
resultCheckInHeaders 201 "$HTTP_RES"
if getLocationFromHeaders "$HTTP_RES"
then
  TRANSACTION=$( echo "${LOCATION}" | sed -e "s|${FEDORA_URL}||" | tr -d "\n\r")
  echo "Transaction is (${TRANSACTION})"
  
  echo "Create an object in the transaction"
  HTTP_RES=$(curl $CURL_OPTS -XPUT  -u${AUTH_USER}:${AUTH_PASS}  ${FEDORA_URL}${TRANSACTION}${PARENT}/transactionObj2)
  resultCheck 201 $HTTP_RES
  
  echo "Container is available inside the transaction"
  HTTP_RES=$(curl $CURL_OPTS -XGET  -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${TRANSACTION}${PARENT}/transactionObj2)
  resultCheck 200 $HTTP_RES
  
  echo "Container not available outside the transaction"
  HTTP_RES=$(curl $CURL_OPTS -XGET  -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/transactionObj2)
  resultCheck 404 $HTTP_RES
  
  echo "Rollback transaction"
  HTTP_RES=$(curl $CURL_OPTS -XPOST -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${TRANSACTION}/fcr:tx/fcr:rollback)
  resultCheck 204 $HTTP_RES
  
  echo "Container is still not available outside the transaction"
  HTTP_RES=$(curl $CURL_OPTS -XGET  -u${AUTH_USER}:${AUTH_PASS} ${FEDORA_URL}${PARENT}/transactionObj2)
  resultCheck 404 $HTTP_RES
  
  echo "All tests completed"
fi

cleanUpTests "$PARENT"
