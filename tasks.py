import os
import psycopg2
from contextlib import contextmanager
from datetime import datetime

import colorama
from colorama import Fore, Style
from dotenv import load_dotenv
from invoke import task, Collection

colorama.just_fix_windows_console()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR_PATH = os.path.join(PROJECT_ROOT, "src")

load_dotenv()

APP_NAME = "pm"
APP_PORT = "3001"
DB_NAME = os.environ["DB_NAME"]
DB_USERNAME = os.environ["DB_USERNAME"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]

# Note: In calls to c.run(), we set `pyt=True` to retain coloured output in the terminal.
#       See: https://github.com/pyinvoke/invoke/issues/256


# These set of Invoke tasks make use of Namespaces.
# For more info, see: https://docs.pyinvoke.org/en/stable/concepts/namespaces.html

# Default Namespace
ns = Collection()


# Namespace: APP (Run app locally)
# -----------------------------------------------
application = Collection("app")


@task
def run_app(c):
    """Run flask in debug mode for PM"""
    with c.cd(SRC_DIR_PATH):
        c.run(
            f"flask --app {APP_NAME}.restapi.web --debug run -p {APP_PORT}",
            pty=True,
        )


@task
def run_relay_service(c):
    """Run the der gateway relay service"""
    with c.cd(SRC_DIR_PATH):
        c.run("python -m der_gateway_relay.main")


@task
def run_pm_worker(c):
    """Run the worker service for PM app"""
    with c.cd(SRC_DIR_PATH):
        c.run("python -m pm.worker")


@task
def run_pm_bucket_watcher(c):
    """Run the bucket watcher service for PM app"""
    with c.cd(SRC_DIR_PATH):
        c.run("python -m pm.bucket_watcher")


@task
def run_pm_scheduler(c):
    """Run the PM scheduler"""
    c.run("cd src && python -m pm.scheduler")


application.add_task(run_app, "run")
application.add_task(run_relay_service, "der-gateway-relay")
application.add_task(run_pm_scheduler, "scheduler")
application.add_task(run_pm_worker, "run-pm-worker")
application.add_task(run_pm_bucket_watcher, "run-pm-bucket-watcher")


@task
def gen_api_spec(c, fmt="json", output_generated_path_only=False):
    """Generates api spec (fmt=json|yaml) for PM and DerWh"""
    timestamp = datetime.strftime(datetime.now(), "%y%m%d-%H%M")
    API_SPEC_DIR_NAME = "apispec"
    apispec_path = os.path.join(PROJECT_ROOT, API_SPEC_DIR_NAME)
    file_name = f"{APP_NAME}_apispec_{timestamp}.{fmt}"

    os.environ["OFFLINE_MODE"] = "true"

    c.run(f"mkdir -p {API_SPEC_DIR_NAME}")

    with c.cd(SRC_DIR_PATH):
        c.run(
            f"flask --app {APP_NAME}.restapi.web openapi write --format={fmt} {apispec_path}/{file_name}",
            pty=True,
        )
    if output_generated_path_only:
        print(os.path.join(apispec_path, file_name))
    else:
        print("API Spec. Generated [✔]")
        print("-----------------------")
        print(f"Location: {apispec_path}")
        print(f"File Name: {file_name}")
        print("")


application.add_task(gen_api_spec)


@task
def gen_asyncapi_spec(c, fmt="json"):
    """Generate asyncapi spec (fmt=json|html)"""
    with c.cd(SRC_DIR_PATH):
        c.run(f"python -m {APP_NAME}.docs.generate_docs", pty=True)
        if fmt == "html":
            try:
                c.run("asyncapi --version")
            except Exception as e:
                print(e)
                print("Please run 'npm install -g @asyncapi/cli' to install the asyncapi CLI.")
                return
            c.run(
                f"asyncapi generate fromTemplate ./{APP_NAME}/docs/asyncapi-spec.json @asyncapi/html-template -o ../docs/asyncapi_html --force-write",
                pty=True,
            )


application.add_task(gen_asyncapi_spec)
# -----------------------------------------------


# Namespace: DB
# -----------------------------------------------
db = Collection("db")


@task
def drop_db(c):
    """Drop the databases for all apps"""
    with _get_db_cursor():
        _drop_db(DB_NAME)


db.add_task(drop_db, "drop")


@task
def flyway(c):
    """Run database migrations (via Flyway)"""

    print(Style.DIM)
    print("---")
    print("Flyway commands: https://documentation.red-gate.com/fd/commands-184127446.html")
    print("---")
    print(Style.RESET_ALL)

    with c.cd(SRC_DIR_PATH):
        _run_migrations(c)


db.add_task(flyway, "flyway")

# -----------------------------------------------


# Namespace: SEED (seed the database and kafka topics)
# -----------------------------------------------

seed = Collection("seed")


@task
def seed_database(c):
    """Seed the database"""
    _truncate_db(DB_NAME)
    print(f"Starting {APP_NAME} seeder...")
    with c.cd(SRC_DIR_PATH):
        c.run(f"python -m {APP_NAME}.seed.database")


@task
def seed_kafka(c, pm=False, der_warehouse=False, der_gateway=False):
    """Seed kafka with data from PM, DER Warehouse, and DER Gateway

    Each service can be specified with a flag.
    If no flags are specified, all services will be seeded.
    """
    print(f"Starting {APP_NAME} seeder...")
    with c.cd(SRC_DIR_PATH):
        cmd = ["python", "-m", f"{APP_NAME}.seed.kafka"]
        include_all = not pm and not der_warehouse and not der_gateway

        if include_all or pm:
            cmd.append("--pm")
        if include_all or der_warehouse:
            cmd.append("--der_warehouse")
        if include_all or der_gateway:
            cmd.append("--der_gateway")

        c.run(" ".join(cmd))


seed.add_task(seed_database, "database")
seed.add_task(seed_kafka, "kafka")
# -----------------------------------------------


# Namespace: LINTING
# -----------------------------------------------
linting = Collection("linting")


@task
def lint(c, check_only=""):
    """Run the following toolset on source: isort, autoflake, black, flake8

    Note: when check_only=True (intended for CI), the tools will be configured to emit warnings &
    errors. No source code changes will be made.
    """
    CHECK_ONLY_MODE = False
    if check_only in ["True", "true", "yes", "on", 1]:
        CHECK_ONLY_MODE = True

    with c.cd(PROJECT_ROOT):
        flag = "--check-only" if CHECK_ONLY_MODE else ""
        print("Running ISORT")
        print("-------------")
        c.run(f"poetry run isort {flag} --profile black src", pty=True)
        print("Done")

        flag = "-c" if CHECK_ONLY_MODE else ""
        print("")
        print("Running AUTOFLAKE")
        print("-------------")
        c.run(
            f"poetry run autoflake {flag} -ri --quiet --remove-all-unused-imports --remove-unused-variables src",
            pty=True,
        )
        print("Done")

        flag = "--check --diff --color" if CHECK_ONLY_MODE else ""
        print("")
        print("Running BLACK")
        print("-------------")
        c.run(f"poetry run black {flag} -t py310 --line-length 100 src", pty=True)
        print("Done")

        print("")
        print("Running FLAKE8")
        print("-------------")
        c.run("poetry run flake8 src", pty=True)
        print("Done")


linting.add_task(lint)


@task
def type_check(c):
    """Run mypy type checking on source"""
    print("Running MYPY")
    print("------------")
    c.run("poetry run mypy src --check-untyped-defs", pty=True)
    print("Done")


linting.add_task(type_check)
# -----------------------------------------------


# Namespace: STACK (Docker)
# -----------------------------------------------
stack = Collection("stack")


@task
def stack_up(c, profile="all", build=False):
    """Bring up the docker stack

    rebuild with the --build flag
    use profile=all to bring up all services, including the api, worker, and bucket_watcher
    services (default)
    use profile=dev to bring up the background services (postgres, kafka, kafka-ui, minio), but not
    the api, worker or bucket_watcher services
    use profile=testing to bring up just the database. Useful for writing unit tests with minimal
    overhead
    note environment variables in the .env file"""
    cmd = "docker compose -f docker/docker-compose.yml -p pmcore --env-file .env"
    if profile:
        cmd += f" --profile {profile}"
    cmd += " up"
    if build:
        cmd += " --build"
    # kafka listener is different for dev and non-dev profiles
    # in dev, kafka is running on the host machine, so we use localhost
    # in non-dev, kafka is running in a docker container, so we use the container name
    kafka_listener = "localhost" if profile == "dev" else "kafka"
    cmd = f"export KAFKA_LISTENER={kafka_listener} && {cmd}"
    c.run(cmd, pty=True)


stack.add_task(stack_up, "up")


@task
def stack_down(c, profile="all"):
    """Bring down the docker stack"""
    cmd = "docker compose -f docker/docker-compose.yml -p pmcore --env-file .env"
    if profile:
        cmd += f" --profile {profile}"
    cmd += " down -vt 0 --remove-orphans"
    # kafka listener is different for dev and non-dev profiles
    # in dev, kafka is running on the host machine, so we use localhost
    # in non-dev, kafka is running in a docker container, so we use the container name
    kafka_listener = "localhost" if profile == "dev" else "kafka"
    cmd = f"export KAFKA_LISTENER={kafka_listener} && {cmd}"
    c.run(cmd, pty=True)


stack.add_task(stack_down, "down")


@task
def stack_destroy(c, profile="all"):
    """Bring down the docker stack and destroy existing volumes"""
    cmd = "docker compose -f docker/docker-compose.yml -p pmcore --env-file .env"
    if profile:
        cmd += f" --profile {profile}"
    cmd += " down --rmi all --volumes --remove-orphans --timeout 0"
    c.run(cmd, pty=True)


stack.add_task(stack_destroy, "destroy")


@task
def stack_ps(c):
    """List the docker stack (info)"""

    cmd = "docker compose -f docker/docker-compose.yml -p pmcore --env-file .env"
    cmd += " ps --all"
    c.run(cmd, pty=True)


stack.add_task(stack_ps, "ps")


@task
def stack_logs(c, service=""):
    """logs the docker service"""

    cmd = "docker compose -f docker/docker-compose.yml -p pmcore --env-file .env"
    cmd += f" logs {service}"
    c.run(cmd, pty=True)


stack.add_task(stack_logs, "logs")


@task
def build_service(c, docker_file, tag="latest"):
    """build-service: convenience function

    Pass in arg for docker-file ('pmm')
    This rebuilds its docker image"""
    c.run(f"docker build -t {docker_file}:{tag} -f docker/{docker_file}.Dockerfile .", pty=True)


stack.add_task(build_service, "build")
# ===============================================


# Namespace: TESTING
# -----------------------------------------------
testing = Collection("testing")


@task()
def run_tests(c):
    """Run pytest for all apps with 95% cov. req"""
    with c.cd(SRC_DIR_PATH):
        c.run(
            "poetry run pytest -v --cov=pm --cov-config=../pyproject.toml --cov-fail-under=95",
            pty=True,
        )


testing.add_task(run_tests, "tests")


@task()
def run_tests_with_coverage(c):
    """Run pytest for all apps with 95% cov. req. + gen. cov. report"""
    with c.cd(SRC_DIR_PATH):
        c.run(
            "poetry run pytest -v --cov=pm --cov-config=../pyproject.toml --cov-fail-under=95 --cov-report html",
            pty=True,
        )


testing.add_task(run_tests_with_coverage, "coverage")
# -----------------------------------------------


# Helper Methods
# -----------------------------------------------


@contextmanager
def _get_db_cursor(db_name="postgres"):
    conn = psycopg2.connect(
        host=DB_HOST, user=DB_USERNAME, password=DB_PASSWORD, database=db_name, port=DB_PORT
    )
    conn.autocommit = True
    cur = conn.cursor()
    yield cur
    cur.close()
    conn.close()


def _truncate_db(db_name: str):
    with _get_db_cursor(db_name) as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'"
        )
        tables = cur.fetchall()
        if tables:
            for table in tables:
                cur.execute(f"TRUNCATE TABLE {table[0]} RESTART IDENTITY CASCADE")
            print(f"All tables in {db_name} database have been truncated")
        else:
            print(f"No tables found in {db_name} database")


def _drop_db(db_name: str):
    with _get_db_cursor() as cur:
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'")
        exists = cur.fetchone()
        if exists:
            cur.execute(f"DROP DATABASE {db_name}")
            print(f"Database {db_name} was dropped")
        else:
            print(f"Database {db_name} doesn't exist")


def _run_migrations(c):
    print(Fore.MAGENTA)
    print(f"Migrations: Targeting app: {APP_NAME}")
    print("-----------------------------------")
    print(Fore.RESET)
    flyway_image = "dig-grid-artifactory.apps.ge.com/virtual-docker/flyway/flyway:latest"
    cmd = "docker run --rm --network=core -v ./pm/migrations:/flyway/sql "
    cmd += f"{flyway_image} -user={DB_USERNAME} -password={DB_PASSWORD} "
    cmd += f"-url=jdbc:postgresql://postgresdb:5432/{DB_NAME} migrate"
    c.run(cmd, pty=True)


# ===============================================


# Register Namespaces
# -------------------
ns.add_collection(application)
ns.add_collection(db)
ns.add_collection(seed)
ns.add_collection(linting)
ns.add_collection(stack)
ns.add_collection(testing)
