How to start postgress and kafka & Flask app:

This docker compose file starts the postgreSQL, Kafka  cluster with zookeeper & a flask app in docker containers and exposes their respective ports. 

## To stack up the all the containers
```
cd docker
docker compose -f docker-compose.yml up --build
```
or you could use poetry task to do that.

First install poetry dependencies by running this command
```
poetry install
```
then 
```
poetry run invoke stack-up --profile=testing
```


## To use Flask app:

The flask app runs on `localhost:3001` and the health check endpoint is `/health_check`


## To use Kafka & Zookeeper:

Connect to the Kafka cluster from your local machine via address localhost:9092

Connect to Zookeeper from your local machine via address localhost:32181

### To connect to Kafka docker container please run the following commands in order

```
docker exec -it kafka /bin/bash
```
Now you are in the docker container which is running kafka cluster


### To list all the topics 

```
/opt/bitnami/kafka/bin/kafka-topics.sh --list --bootstrap-server kafka:29092
```
### To create a new topic 

```
/opt/bitnami/kafka/bin/kafka-topics.sh --create --topic new-topic-name --bootstrap-server kafka:29092
```
### To write some data to the topic 

```
/opt/bitnami/kafka/bin/kafka-console-producer.sh --topic new-topic-name --bootstrap-server kafka:29092
```
### To read the data from the topic 
You can connect to kafka container again in a new terminal window and can start consuming the data while you write the data to the topic using above command

```
/opt/bitnami/kafka/bin/kafka-console-consumer.sh --topic new-topic-name  --from-beginning --bootstrap-server kafka:29092
```

## To use postgresSQL:

The PostgreSQL database server is running in the docker container which exposes its port 5432 to the local machine at 5432. Simply use any postgreSQL UI (pgAdmin is most famous one) and connect to localhost:5432. The username is `gridos` and password is `gridos`


## To install pre-commit git hooks:
This only needs to be run one time on initial setup or if they have been changed:
```
poetry run pre-commit install
```
If you want to run the hooks manually on all files:
```
poetry run pre-commit run --all-files
```

## To take down the all the containers
```
cd docker
docker compose -f docker-compose.yml down -vt 0
```
or

```
poetry run invoke stack-down --profile=testing
```

## Poetry tasks 
```
poetry run invoke --list
```
### To fixing the linting

```
poetry run invoke lint
```

### To fixing the types

```
poetry run invoke type-check
```

### To run the tests

```
poetry run invoke run-tests
```


### To run the flask app

```
poetry run invoke flask
```
