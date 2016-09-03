#!/bin/bash
if [ -f "./config" ]; then
  . "./config"
fi

# Create test objects all inside here for easy of review
PARENT="/test_camel"

$(command -v jq > /dev/null 2>&1)
if [ "$?" -eq "1" ]; then
  echo "We require jq for command line JSON parsing."
  echo "Please download, install it from https://stedolan.github.io/jq/"
  exit 1
fi

checkForReTest $PARENT

# Aviso
printf "\n"
echo "Success may not be immediate, we will wait up to 30 seconds."
printf "\n"

# Tests
echo "Create an object"
EXPECT_ID="${FEDORA_URL}${PARENT}/object_to_index"
HTTP_RES=$(curl $CURL_OPTS -XPUT -u${AUTH_USER}:${AUTH_PASS} -H"Content-type: text/turtle" --data-binary @${RSCDIR}/pcdm_container.ttl ${EXPECT_ID})
resultCheck 201 $HTTP_RES

# Check for indexing to Solr
COUNTER=1
RES=0

printf "%s" "Checking for item in Solr"
while [ "${COUNTER}" -le 30 -a "${RES}" -eq 0 ]; do 
  printf "."
  sleep 1
  if [ "$(expr ${COUNTER} % 5)" -eq "0" ]; then
    # Only execute the query every 5 seconds
    HTTP_RES=$(curl -s -XGET -u${AUTH_USER}:${AUTH_PASS} "${SOLR_URL}/select?q=id:%22${EXPECT_ID}%22&wt=json")
    RES=$(echo $HTTP_RES | jq .response.numFound)
  fi
  COUNTER=$(expr ${COUNTER} + 1)
done
printf "\n"
ID=$(echo $HTTP_RES | jq '.response.docs[0].id' | sed -e 's|"||g')
resultCheckString $EXPECT_ID $ID

# Check for indexing to Triplestore
COUNTER=1
LEN=0
printf "%s" "Checking for item in Triplestore"
QUERY="PREFIX dc: <http://purl.org/dc/elements/1.1/> SELECT ?o WHERE { <${EXPECT_ID}> dc:title ?o}"
while [ "${COUNTER}" -le 30 -a "${LEN}" -eq 0 ]; do 
  printf "."
  sleep 1
  if [ "$(expr ${COUNTER} % 5)" -eq "0" ]; then
    # Only execute the query every 5 seconds
    HTTP_RES=$(curl -s -X POST -H"Content-type: application/sparql-query" -H"Accept: application/sparql-results+json" --data "${QUERY}" "${TRIPLESTORE_URL}")
    LEN=$(echo ${HTTP_RES} | jq '.results.bindings | length')
  fi
  COUNTER=$(expr ${COUNTER} + 1)
done
printf "\n"
TITLE=$(echo ${HTTP_RES} | jq '.results.bindings[0].o.value' | sed -e 's|"||g')
resultCheckString "Object 1" "${TITLE}"


echo "All tests completed"
cleanUpTests "$PARENT"
