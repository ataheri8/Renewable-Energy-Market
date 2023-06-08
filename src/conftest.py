import os
from unittest.mock import patch

import pytest
from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine, text

from pm.tests import factories
from shared.system import configuration, database
from shared.system.database import Base
from shared.tasks.producer import Producer

load_dotenv()


# Override base env. vars. for testing (as necessary)
TEST_ENV_PARAMS = {
    "DB_NAME": "test",
}


def copy_dbs(source_db: str, dest_db: str):
    """Copy a database to a new database.
    Just copies the schema, not the data.
    """
    config = configuration.init_config(configuration.Config)
    user = config.DB_USERNAME
    password = config.DB_PASSWORD
    host = config.DB_HOST
    port = config.DB_PORT
    pg_str = lambda db: f"postgresql://{user}:{password}@{host}:{port}/{db}"  # noqa
    source_conn_str = pg_str(source_db)
    source_engine = create_engine(source_conn_str, isolation_level="AUTOCOMMIT")
    metadata = MetaData()
    metadata.reflect(bind=source_engine)
    with source_engine.connect() as conn:
        try:
            # can't use 'IF NOT EXISTS', text does not like it,
            # so just catch the exception and move on
            conn.execute(text(f"CREATE DATABASE {dest_db}"))
        except Exception:
            print(f"Database: {dest_db} already exists. Not created again.")
        conn.close()

    dest_conn_str = pg_str(dest_db)
    dest_engine = create_engine(dest_conn_str)

    metadata.drop_all(dest_engine)
    metadata.create_all(dest_engine)


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Set the env with TEST_ENV_PARAMS"""
    config = configuration.init_config(configuration.Config)
    copy_dbs(config.DB_NAME, TEST_ENV_PARAMS["DB_NAME"])
    for env_key, value in TEST_ENV_PARAMS.items():
        if value is not None:
            os.environ[env_key] = value
    configuration.init_config(configuration.Config)


@pytest.fixture(autouse=True)
def patch_kafka_producer():
    """Patch the send method globally. This will stop our unit tests
    trying to connect to the Kafka broker.
    """
    with patch("shared.tasks.producer.KafkaProducer"):
        # Reset the producer to None so we can check if it was used
        Producer._producer = None
        yield


@pytest.fixture()
def db_session():
    """Create then remove tables to reset database state between every test."""
    config = configuration.get_config()
    database.init(config)
    yield database.Session
    database.Session.rollback()
    for table in reversed(Base.metadata.sorted_tables):
        if table.name != "flyway_schema_history":
            sql_stmt = text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE;")
            database.Session.execute(sql_stmt)
    database.Session.commit()
    database.Session.close_all()


@pytest.fixture
def service_provider():
    """Return a Fake ServiceProvider."""
    return factories.ServiceProviderFactory()
