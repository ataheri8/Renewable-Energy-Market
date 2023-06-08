import re
from typing import Any

from lxml import etree as ET


class AssertXMLEqualsMixin:
    def _remove_whitespace_and_newlines(self, xml_string: str) -> str:
        """Remove all whitespace and newlines from the XML string"""
        return re.sub(r">\s+<", "><", xml_string.replace("/n", "").strip())

    def _reformat_xml_string(self, xml_string: str) -> str:
        """Reformat the XML string to be pretty-printed"""
        reformatted_str = self._remove_whitespace_and_newlines(xml_string)
        xml_obj = ET.fromstring(reformatted_str)
        return self._xml_object_to_string(xml_obj)

    def _xml_object_to_string(self, xml_obj: Any) -> str:
        """Convert the XML object to a string and pretty-print"""
        return ET.tostring(xml_obj, pretty_print=True).decode("utf-8")

    def assert_xml_equals(self, expected_val: str, got_val: Any):
        """Assert that the expected XML string matches the XML object"""
        expected_value = self._reformat_xml_string(expected_val)
        got_value = self._xml_object_to_string(got_val)
        assert got_value == expected_value

    def assert_xml_str_equals(self, expected_val: str, got_val: str):
        """Assert that the expected XML string matches the XML string"""
        expected_value = self._reformat_xml_string(expected_val)
        got_value = self._reformat_xml_string(got_val)
        assert got_value == expected_value
