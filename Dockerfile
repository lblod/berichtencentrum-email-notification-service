FROM mikidi/mu-python-template:python3-port
LABEL maintainer="info@redpencil.io"

ENV MU_APPLICATION_GRAPH "http://mu.semte.ch/graphs/public"
ENV MU_SPARQL_ENDPOINT "http://virtuoso:8890/sparql"
ENV MU_SPARQL_UPDATEPOINT "http://virtuoso:8890/sparql"

ENV RUN_INTERVAL 5
ENV OUTBOX_FOLDER_URI 'http://data.lblod.info/id/mail-folders/2'
