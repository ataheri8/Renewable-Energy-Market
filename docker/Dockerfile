# this is a common Dockerfile for PM and DERWH. To run either one of them you need to set environment variable 'MODULE_TO_RUN' with acceptable value of pm (case sensitive) at run time. Please take a look at script run.sh so you can see how MODULE_TO_RUN is being used to run these modules

ARG BASE_IMAGE=dig-grid-artifactory.apps.ge.com/opus-one-docker/base/python:3.10-ubi8-minimal-latest

FROM --platform=linux/amd64 ${BASE_IMAGE} as requirements_export

COPY ./poetry.lock ./pyproject.toml ./
ARG POETRY_PACKAGE_OPT="--without=dev"
RUN pip install poetry\
    && poetry export -o requirements.txt --without-hashes "${POETRY_PACKAGE_OPT}"

#=============================================================================================
FROM --platform=linux/amd64 ${BASE_IMAGE}

# ARG GE_GRID_ARTIFACTORY_USER
# ARG GE_GRID_ARTIFACTORY_PW
ARG PM_UID="398"
ARG PM_GROUP=${PM_UID}:nobody
ARG PM_HOME="/opt/pm-core"

RUN mkdir ${PM_HOME}\
    && chown -R ${PM_GROUP} ${PM_HOME}

COPY --from=requirements_export --chown=${PM_GROUP} requirements.txt ${PM_HOME}/

# This is for future reference. We can use this to install packages from artifactory
# RUN PIP_EXTRA_INDEX_URL=https://${GE_GRID_ARTIFACTORY_USER}:${GE_GRID_ARTIFACTORY_PW}@dig-grid-artifactory.apps.ge.com/artifactory/api/pypi/opus-one-pypi-virtual/simple pip install -r ${PM_HOME}/requirements.txt --no-cache-dir
RUN pip install -r ${PM_HOME}/requirements.txt --no-cache-dir


COPY --chown=${PM_GROUP} ./src ${PM_HOME}/src
COPY --chown=${PM_GROUP} ./docker/scripts/run.sh ./pyproject.toml ${PM_HOME}/

WORKDIR ${PM_HOME}

USER ${PM_UID}
EXPOSE 8000/tcp

ENTRYPOINT ./run.sh
