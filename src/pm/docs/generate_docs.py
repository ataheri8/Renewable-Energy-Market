import json

from pm.topics import DOCUMENTED_TOPICS
from shared.tools.asyncapi import generate_asyncapi_spec


def generate_spec():
    print("generating spec from topics...")
    async_spec = generate_asyncapi_spec(DOCUMENTED_TOPICS, title="PM Kafka Topics")  # type: ignore  # noqa
    path = "pm/docs/asyncapi-spec.json"
    with open(f"./{path}", "w") as f:
        print(f"writing spec to {path}...")
        json.dump(async_spec, f, indent=4)
        print("finished!")


if __name__ == "__main__":
    generate_spec()
