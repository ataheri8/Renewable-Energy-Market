ARG BASE_IMAGE=dig-grid-artifactory.apps.ge.com/virtual-docker/flyway/flyway:latest

FROM --platform=linux/amd64 ${BASE_IMAGE}

ARG PM_UID="398"
ARG PM_HOME="/opt/pm-core"

RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -\
    && sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ focal-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'\
    && apt-get update\
    && apt-get install -y postgresql-client-14\
    && mkdir -p ${PM_HOME}\
    && chown -R ${PM_UID}:nogroup ${PM_HOME}\
    && rm -rf /var/lib/apt/lists/*

USER ${PM_UID}
COPY --chown=${PM_UID}:nogroup ./docker/scripts/* ${PM_HOME}/scripts/
COPY --chown=${PM_UID}:nogroup ./src/pm/migrations/* ${PM_HOME}/pm/migrations/

WORKDIR ${PM_HOME}

ENTRYPOINT [ "./scripts/init_db.sh" ]
