"""Shared schemas by all modules in restapi"""

import json
from typing import Optional

import marshmallow as ma
from flask_smorest.fields import Upload
from marshmallow import ValidationError, validate
from werkzeug.datastructures import FileStorage

from shared.system import configuration


class ErrorSchema(ma.Schema):
    """Default error schema"""

    code = ma.fields.Integer()
    status = ma.fields.String()
    message = ma.fields.String()
    errors = ma.fields.Dict()


class JSONFileSchema(ma.Schema):
    # constants to check file info
    MIMETYPE = "application/json"
    EXTENSION = ".json"
    # expected field
    file = Upload()

    def __init__(self, *args, schema: Optional[ma.Schema] = None, **kwargs):
        self.schema = schema
        super().__init__(*args, **kwargs)

    @ma.post_load
    def check_file(self, data: dict, **kwargs) -> dict:
        file = data["file"]

        self.check_file_mimetype(file)
        self.check_file_extension(file)
        dict_data = self.parse_file(file)

        if self.schema:
            return self.schema.load(dict_data)
        return dict_data

    def check_file_mimetype(self, json_file: FileStorage):
        if json_file.mimetype != self.MIMETYPE:
            raise ValidationError(f"Invalid file type, expected {self.MIMETYPE}")

    def check_file_extension(self, json_file: FileStorage):
        if json_file.filename:
            if not json_file.filename.endswith(self.EXTENSION):
                raise ValidationError(f"Invalid file extension, expected {self.EXTENSION}")

    def parse_file(self, json_file: FileStorage) -> dict:
        return json.loads(json_file.read())


class PaginatedRequestSchema(ma.Schema):
    """Base for a paginated request"""

    pagination_start = ma.fields.Integer(validate=validate.Range(min=1))
    pagination_end = ma.fields.Integer(validate=validate.Range(min=2))

    @ma.post_load
    def adjust_pagination_start_end(self, data, **kwargs):
        """Adjust the pagination parameters if required and returned the data"""
        config = configuration.get_config()
        if data.get("pagination_start") is None:
            data["pagination_start"] = 1
        if data.get("pagination_end") is not None:
            if data["pagination_end"] <= data["pagination_start"]:
                raise ValidationError(
                    "End value is less than start value", field_name="pagination_end"
                )
            if data["pagination_end"] - data["pagination_start"] >= config.PAGINATION_MAX_LIMIT:
                raise ValidationError(
                    "End value surpasses limit of 10,000", field_name="pagination_end"
                )
        if data.get("pagination_end") is None:
            data["pagination_end"] = data["pagination_start"] + config.PAGINATION_DEFAULT_LIMIT - 1
        return data


class PaginatedResponseSchema(ma.Schema):
    """Base for the paginated response.
    If subclassing this schema, overwrite `results` with the data you expect to return
    """

    pagination_start = ma.fields.Integer(required=True)
    pagination_end = ma.fields.Integer(required=True)
    count = ma.fields.Integer(required=True)
