# Program Management Core

Most recent updates:

- 18 May 2023 by Suhird
- 19 Apr 2023 by Ryan
- 18 Jan 2023 by Julian

Please maintain this guide with your own updates and experiences. This is a
living document.

Detailed sources: Please check these for setting up your own environment:
there's GE specific stuff in here but also general stuff that's useful for any
Python project.

- [Documentation and On-Boarding](https://opusonesolutions.atlassian.net/l/cp/k0NBb5Ex)
- [Program Mgmt. Confluence](https://opusonesolutions.atlassian.net/wiki/spaces/PGRM/overview?homepageId=2860254285)
- [developer onboarding](https://opusonesolutions.atlassian.net/wiki/spaces/PGRM/pages/2863104246/Developer+Onboarding)

## Table Of Contents

[[_TOC_]]

## Invoke tasks

Many operations have been formalized into invoke tasks.

```bash
poetry run invoke TASK ARGS
```

| Task                    | Description                                                                                     |
| ----------------------- | ----------------------------------------------------------------------------------------------- |
| app.der-gateway-relay   | Run the der gateway relay service                                                               |
| app.gen-api-spec        | Generates api spec (fmt=json|yaml) for PM and DerWh                                             |
| app.gen-asyncapi-spec   | Generate asyncapi spec (fmt=json|html)                                                          |
| app.run                 | Run Flask                                                                                       |
| db.create               | Create the databases for all apps                                                               |
| db.drop                 | Drop the databases for all apps                                                                 |
| db.flyway               | Run database migrations (via Flyway)                                                            |
| linting.lint            | Run the following toolset on source: isort, autoflake, black, flake8                            |
| linting.type-check      | Run mypy type checking on source                                                                |
| seed.database           | Seed the database                                                                               |
| seed.kafka              | Seed kafka with data from PM, DER Warehouse, and DER Gateway                                    |
| stack.build-service     | build-service: convenience function                                                             |
| stack.destroy           | Bring down the docker stack and destroy volumes                                                 |
| stack.down              | Bring down the docker stack                                                                     |
| stack.ps                | List the docker stack (info)                                                                    |
| stack.up                | Bring up the docker stack (profile=all|dev|testing)                                             |
| testing.coverage        | Run pytest for all apps with 95% cov. req. + gen. cov. report                                   |
| testing.tests           | Run pytest for all apps with 95% cov. req                                                       |

## Supporting services

There is a docker compose file in the root of the project.
This will start up various supporting services, such as:

Flask application

- pm.restapi.web
- <http://localhost:3001>

PostgreSQL database

- localhost:5432 database is 'pmcore'

MinIO (file bucket)

- MinIO ObjectStore UI <http://localhost:9001/login>
- user/pass is "gridosgridos"

Kafka

- UI for Apache Kafka <http://localhost:8080/>

Audit Logging Service

- Clone the repo <https://gitlab.com/opusonesolutions/zeus/core/audit-logging-service.git>
- The repo should be in the same folder structure level as `core`
- ```user_home_directory
  program_mgmt
    core
      src
        ...
    audit-logging-service
      src
        ...

- API url for Audit Logging Service <http://localhost:3003/>

Messaging Service
- Clone the repo <https://gitlab.com/opusonesolutions/zeus/core/messaging-service.git>
- The repo should be in the same folder structure level as `core` similar to audit-logging-service
- ```user_home_directory
  program_mgmt
    core
      src
        ...
    audit-logging-service
      src
        ...
    messaging-service
      src
        ...

- API url for Messaging Service  <http://localhost:3004/>

Der Warehouse

- Clone the repo <https://gitlab.com/opusonesolutions/zeus/der-model-manager/der-warehouse.git>
- Note, keep the same port (DB_PORT) in the .env file for PM core, Audit logging service, DerWh since they all share the same database container.
- ```user_home_directory
  program_mgmt
    core
      src
        ...
    der-warehouse
      src
        ...


## stack.up

We won't be starting docker compose directly; we have a convenience script for
that.

--profile will be either all, dev or testing

Each profile will load a different set of images

all

- pmcore
- zookeeper
- kafka
- kafka-ui
- postgresdb
- minio
- api
- worker
- scheduler
- bucket_watcher
- audit_logging_db_migrations
- audit_logging_service
- messaging_db_migrations
- messaging_service

dev

- pmcore
- zookeeper
- kafka
- kafka-ui
- postgresdb
- minio

testing

- pmcore
- postgresdb

audit
- postgresdb
- audit_logging_service_db_migrations
- audit_loggin_service_api

messaging
- postgresdb
- messaging-db-migrations
- messaging_service

An example loading the dev profile and forcing a fresh build:

```bash
poetry run invoke stack.up --profile=dev --build
```

## Running the application

The flask application main entry point is `pm.restapi.web:app`

In root of the project there is a .env file which defines the Flask app as well.

You can use the invoke task:

```bash
poetry run invoke app.run
```

Or you can run flask manually if you want to alter the parameters.

```bash
cd src
poetry run flask --app pm.restapi.web run
```

This command will also create the database for the app if it doesn't exist.

## Dependencies & environment

These are managed with [poetry](https://python-poetry.org/docs/#installation).

Install poetry with whichever method you prefer:

```bash
pip3 install --user poetry

OR 

brew install poetry

OR

curl -sSL https://install.python-poetry.org | python3 -
```

Create a virtual environment with:

```bash
poetry install
```

This will install all dependencies and create a virtual environment for you.

periodically you'll need to update your dependencies with:

```bash
poetry update
```

For more useful poetry - see below.

## Some useful poetry commands

```bash
poetry install
poetry add <package>
poetry remove <package>
poetry update
```

ie: if there's a new dependency, add it with:

```bash
poetry add <package>
```

To update your dependencies, run:

```bash
poetry update
```

## Day to day development

Here's some useful notes and things useful to know. Please add to this as you
learn more.

### Routes

You can view the routes with:

```bash
cd src
poetry run flask routes
```

### About Invoke

Invoke is a python version of rake or make.
It's used to run various tasks, such as running the project, tests, linting,
etc.

You can see the available tasks with looking in 'tasks.py' in the root of the
project or by:

```bash
poetry run invoke --list
```

Note: underscores in task function names have to be replaced with dashes when
running the task.

### Running tests

```bash
poetry run invoke testing.tests
```

We're aiming for 95% test coverage so please add tests for any new code.
TDD approach is highly encouraged.

### Dropping the databases

```bash
poetry run invoke db.drop
```

Drops all project's databases

### Creating the databases

```bash
poetry run invoke create.db
```

Creates all project's databases

### Seeding the projects

Database

```bash
poetry run invoke seed.database
```

The seed command will drop and recreate the database for the project selected,
then it will seed the database using the seed package in each project.

Kafka

The Kafka seed system will use objects from the database, so be sure to run
`seed.database` first.

Additionally, if your stack is created using `--profile dev` you can run `seed.kafka`
from your dev machine.

Like so for the PM application:

```bash
poetry run invoke seed.kafka
```

The application specific flags you can use

```text
--pm
--der_warehouse
--der_gateway
```

Not including an application flag will generate seed data for all applications.

If your stack was created using `--profile all` you will need to ssh into a container
and do it from in there.

The terminal in Docker Desktop can suffice for this, `api` would have the libraries
you need.

```bash
python -m pm.seed.kafka
```

### Generating the AsyncAPI documentation

We are documenting our Kafka topics with AsyncAPI <https://www.asyncapi.com/>

The spec can be generated like this:

```bash
poetry run app.gen-asyncapi-spec
```

This will output a JSON file in `src/<project>/docs/asyncapi-spec.json`

You can also generate an HTML version of the documentation

**Note**: You will need to install the AsyncAPI CLI to generate the html docs.
To install:

make sure you have node and npm installed

```bash
npm install -g @asyncapi/cli
```

Once the dependencies are installed, run

```bash
poetry run app.gen-asyncapi-spec --fmt html
```

The files will be available at docs/asyncapi_html/index.html.

To view, drag and drop the index.html into your favourite browser!

## Known bugs and workarounds

### confluent-kafka won't install on M1 macs

```text
#0 25.93       /tmp/pip-install-ex5ck6u1/confluent-kafka_915f1b54d72c419a8ba9b2b2891bbc7b/src/confluent_kafka/src/confluent_kafka.h:23:10: fatal error: librdkafka/rdkafka.h: No such file or directory
#0 25.93          23 | #include <librdkafka/rdkafka.h>
#0 25.93             |          ^~~~~~~~~~~~~~~~~~~~~~
#0 25.93       compilation terminated.
#0 25.93       error: command '/usr/bin/gcc' failed with exit code 1
#0 25.93       [end of output]
#0 25.93   
#0 25.93   note: This error originates from a subprocess, and is likely not a problem with pip.
#0 25.93 error: legacy-install-failure
#0 25.93 
#0 25.93 × Encountered error while trying to install package.
#0 25.93 ╰─> confluent-kafka
```

Basically no build is available for this chip yet, and to build it locally there
are some dependencies that need to be setup.

<https://medium.com/@sri.vkrnt/using-confluent-kafka-on-apple-silicon-5d9150d198a3>

Running the project locally will function like this, however running a docker
container on Apple M1 will require some changes to the `Dockerfile.local`.

On Apple M1 machines we can set the Dockerfile to generate as linux/amd64 to
workaround missing or old libraries.

This maneuver may need to be done for other packages that don't have wheels for Apple Silicone yet as well.

```bash
#FROM python:3.10.11-bullseye

# if Apple M1 is missing built libraries, set the image to linux/amd64
FROM --platform=linux/amd64 python:3.10.11-bullseye
```

### FATAL:  database "pmcore" does not exist

```bash
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to
server at "postgresdb" (172.21.0.3), port 5432 failed: FATAL:  database
"pmcore" does not exist
```

You can manually run `poetry run invoke db.create` to create the databases, then
run stack.up again with the volume in place.

### The seed.kafka invoke task gives a networking error

Something like this shows up when you try to seed Kafka with messages.

```text
%3|1681328480.843|FAIL|rdkafka#producer-1| [thrd:kafka:9092/1001]: kafka:9092/1001: Failed to resolve 'kafka:9092': Name or service not known (after 2219ms in state CONNECT)
%3|1681328482.943|FAIL|rdkafka#producer-1| [thrd:kafka:9092/1001]: kafka:9092/1001: Failed to resolve 'kafka:9092': Name or service not known (after 2100ms in state CONNECT, 1 identical error(s) suppressed)
%3|1681328516.227|FAIL|rdkafka#producer-1| [thrd:kafka:9092/1001]: kafka:9092/1001: Failed to resolve 'kafka:9092': Temporary failure in name resolution (after 10010ms in state CONNECT)
```

The containers you are working with are not allowing connections from your development machine, so will need to 
ssh into it and execute the seed script directly.

You can use the Docker Desktop terminal for this

```bash
python -m pm.seed.kafka
```

