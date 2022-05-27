
CONFIG_FILE_PARAM = "config_file"
SITE_NAME_PARAM = "site_name"
BASE_URL_PARAM = "baseurl"
ADMIN_USER_PARAM = "admin_user"
ADMIN_PASS_PARAM = "admin_password"
USER_NAME_PARAM = "user1"
USER_PASS_PARAM = "password1"
USER2_NAME_PARAM = "user2"
USER2_PASS_PARAM = "password2"
LOG_FILE_PARAM = "logfile"
SELECTED_TESTS_PARAM = "selected_tests"
SOLR_URL_PARAM = "solrurl"
TRIPLESTORE_URL_PARAM = "triplestoreurl"
# Via RFC 7231 3.3
PAYLOAD_HEADERS = ['Content-Length', 'Content-Range', 'Trailer', 'Transfer-Encoding']

# Fedora specific constants
FEDORA_NS = "http://fedora.info/definitions/v4/repository#"
FCR_VERSIONS = "fcr:versions"
FCR_FIXITY = "fcr:fixity"
SERVER_MANAGED = FEDORA_NS + "ServerManaged"
INBOUND_REFERENCE = FEDORA_NS + "InboundReferences"
EMBEDED_RESOURCE = FEDORA_NS + "EmbedResources"

GET_PREFER_MINIMAL = "return=minimal"
PUT_PREFER_LENIENT = "handling=lenient; received=\"minimal\""

# This is used with the make_prefer_header() function in abstract_fedora_tests
PREFER_PATTERN = "return=representation; {0}=\"{1}\""

RFC_1123_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"

# General Mime and LDP constants
JSONLD_MIMETYPE = "application/ld+json"
SPARQL_UPDATE_MIMETYPE = "application/sparql-update"
TURTLE_MIMETYPE = "text/turtle"
SPARQL_QUERY_MIMETYPE = "application/sparql-query"
SPARQL_RESULT_JSON_MIMETYPE = "application/sparql-results+json"
LINK_FORMAT_MIMETYPE = "application/link-format"

LDP_NS = "http://www.w3.org/ns/ldp#"
LDP_CONTAINER = LDP_NS + "Container"
LDP_BASIC = LDP_NS + "BasicContainer"
LDP_DIRECT = LDP_NS + "DirectContainer"
LDP_INDIRECT = LDP_NS + "IndirectContainer"
LDP_RESOURCE = LDP_NS + "Resource"
LDP_NON_RDF_SOURCE = LDP_NS + "NonRDFSource"

MEMENTO_NS = "http://mementoweb.org/ns#"
MEM_ORIGINAL_RESOURCE = MEMENTO_NS + "OriginalResource"
MEM_TIMEGATE = MEMENTO_NS + "TimeGate"
MEM_TIMEMAP = MEMENTO_NS + "TimeMap"
MEM_MEMENTO = MEMENTO_NS + "Memento"

ACL_NS = "http://www.w3.org/ns/auth/acl#"

PURL_NS = "http://purl.org/dc/elements/1.1/"

# Test constructs
OBJECT_TTL = "@prefix dc: <http://purl.org/dc/elements/1.1/> ." \
             "@prefix pcdm: <http://pcdm.org/models#> ." \
             "<> a pcdm:Object ;" \
             "dc:title \"An Object\" ."

PCDM_CONTAINER_TITLE = "PCDM Container"

PCDM_CONTAINER_TTL = "@prefix dc: <http://purl.org/dc/elements/1.1/> ." \
                     "@prefix pcdm: <http://pcdm.org/models#> ." \
                     "<> a pcdm:Object ;" \
                     "dc:title \"{0}\" .".format(PCDM_CONTAINER_TITLE)
