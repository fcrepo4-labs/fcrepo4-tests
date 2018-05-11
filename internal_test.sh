#!/bin/bash
#  THIS IS ONLY TO VERIFY EXPECTED OUTCOMES FROM FUNCTIONS.
#  You probably only need to run this if you are experiencing false
#  positive failures.

if [ -f "./config" ]; then
 . "./config"
fi

echo "Test resultCheck"
expected=200
resultCheck 200 $expected
expected=404
resultCheck 404 $expected

echo "Test resultCheckString"
String="This is the String I am testing"
resultCheck "This is the String I am testing" "$String"
String="Superfly Jimmy Snuka"
resultCheck "Superfly Jimmy Snuka" "$String"

echo "Test resultCheckInHeaders"
Headers=$( cat "${RSCDIR}/internal_stubbing/basic_container_headers.txt")
resultCheckInHeaders 200 "$Headers"
Headers=$( cat "${RSCDIR}/internal_stubbing/404_response_headers.txt")
resultCheckInHeaders 404 "$Headers"
Headers=$( cat "${RSCDIR}/internal_stubbing/post_rdfsource_response_headers.txt")
resultCheckInHeaders 201 "$Headers"
Headers=$( cat "${RSCDIR}/internal_stubbing/post_nonrdfsource_response_headers.txt")
resultCheckInHeaders 201 "$Headers"
resultCheckInHeaders 100 "$Headers"

echo "Test getLocationFromHeaders"
Headers=$( cat "${RSCDIR}/internal_stubbing/post_rdfsource_response_headers.txt")
Location=$(getLocationFromHeaders "$Headers")
resultCheckString "http://localhost:8080/rest/test_versioning/11/be/fc/26/11befc26-6ba3-4d6d-a731-84d030f552b7" "$Location"
Headers=$( cat "${RSCDIR}/internal_stubbing/post_nonrdfsource_response_headers.txt")
Location=$(getLocationFromHeaders "$Headers")
resultCheckString "http://localhost:8080/rest/test_versioning/82/ab/b6/13/82abb613-5d7e-4f77-b310-c83729884f19" "$Location"

echo "Test checkContentType"
RDF_VARIANTS="text/turtle application/rdf+xml application/ld+json application/n-triples text/n3"
for i in $RDF_VARIANTS; do
  escaped=$( echo $i | sed -e 's/\//\\\//')
  Headers=$( cat "${RSCDIR}/internal_stubbing/basic_container_headers.txt" | sed -e "s/text\/turtle/${escaped}/" )
  checkContentType "$i;charset=utf-8" "$Headers"
done

echo "Skipping test checkTitle, requires a repository to access"

echo "Test assertLinkHeader"
Headers=$( cat "${RSCDIR}/internal_stubbing/basic_container_headers.txt")
assertLinkHeader "<http://www.w3.org/ns/ldp#BasicContainer>;rel=\"type\"" "$Headers"
assertLinkHeader "<http://www.w3.org/ns/ldp#Container>;rel=\"type\"" "$Headers"
assertLinkHeader "<http://localhost:8080/rest/test_versioning/fcr:acl>;rel=\"acl\"" "$Headers"
assertLinkHeader "<http://localhost:8080/static/constraints/ContainerConstraints.rdf>;rel=\"http://www.w3.org/ns/ldp#constrainedBy\"" "$Headers"

echo "Test countMementos"
Body=$( cat "${RSCDIR}/internal_stubbing/timemap_link_format.txt")
C=$(countMementos "$Body")
resultCheck 2 $C

echo "Test buildRfcDate"
EXPECTED="Fri, 14 Feb 1975 13:40:00 +0000"
DATE=$(buildRfcDate 1975 02 14 13 40 00)
resultCheck "$EXPECTED" "$DATE"
EXPECTED="Sat, 04 Aug 2001 00:00:00 +0000"
DATE=$(buildRfcDate 2001 08 04)
resultCheck "$EXPECTED" "$DATE"

echo "Test validateMementoDatetime"
Headers=$( cat "${RSCDIR}/internal_stubbing/binary_version_headers.txt")
EXPECTED="Fri, 27 Apr 2018 18:04:13 GMT"
validateMementoDatetime "$EXPECTED" "$Headers"
