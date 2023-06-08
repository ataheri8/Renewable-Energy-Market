import inspect

import pytest
from colorama import Fore

from pm.restapi import web


@pytest.fixture
def client():
    """Create a test flask client"""
    app = web.create_app()
    yield app.test_client()


def color_gherkin_language(docstring: str, keyword_color: Fore.CYAN) -> str:
    GHERKIN_KEYWORDS = ["given", "when", "then", "and", "but"]
    docstring = docstring.lower()
    for keyword in GHERKIN_KEYWORDS:
        docstring = docstring.replace(
            keyword,
            f"{keyword_color}{keyword.capitalize()}{Fore.RESET}",
        )
    return docstring


def pytest_itemcollected(item: pytest.Item):
    doc = inspect.getdoc(item.obj)
    if doc:
        colorised_doc = color_gherkin_language(doc, Fore.CYAN)
        item._nodeid = f"{item._nodeid} \n\n {colorised_doc} "
