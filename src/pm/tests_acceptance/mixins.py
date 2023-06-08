import pathlib


class TestDataMixin:
    """Mixin for getting test data from test_data folder"""

    def _get_test_data_path(self, filename: str):
        path = str(pathlib.Path(__file__).parent)
        return path + "/test_data/" + filename
