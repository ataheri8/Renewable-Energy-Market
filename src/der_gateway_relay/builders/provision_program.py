from typing import Any

from lxml import etree as ET

PROVISION_PROGRAM_LIST_TAG = "ProgramDataList"
PROVISION_PROGRAM_LIST_NAMESPACE = "com:ge:ieee2030:registration:rest:dto"
PROVISION_PROGRAM_TAG = "ProgramData"

PROGRAM_LIFECYCLE_TAG = "programLifeCycleStatus"
PROGRAM_LIFECYCLE_STATE = "registered"


class ProvisionProgramBuilder:
    """Converts the program creation xml to the provisioning xml"""

    def _remove_namespaces_from_tree(self, xml_tree: Any):
        """Removes the namespace from the previous root element from the xml tree"""
        for elem in xml_tree.getiterator():
            elem.tag = ET.QName(elem).localname
        ET.cleanup_namespaces(xml_tree)

    def _add_lifecycle_element(self, program_data_elem: Any):
        """Adds the lifecycle element to the program data element"""
        lifecycle_elem = ET.SubElement(program_data_elem, PROGRAM_LIFECYCLE_TAG)
        lifecycle_elem.text = PROGRAM_LIFECYCLE_STATE
        program_data_elem.append(lifecycle_elem)

    def replace_tags_for_provisioning(self, xml_tree: Any) -> Any:
        """Replaces the program creation tags with the provisioning tags"""
        program_list = ET.Element(
            PROVISION_PROGRAM_LIST_TAG,
            all="0",
            results="0",
            xmlns=PROVISION_PROGRAM_LIST_NAMESPACE,
        )
        for elem in xml_tree:
            elem.tag = PROVISION_PROGRAM_TAG
            self._add_lifecycle_element(elem)
            program_list.append(elem)
        self._remove_namespaces_from_tree(program_list)
        return program_list

    @classmethod
    def build(cls, program_xml_str: str) -> str:
        xml_tree = ET.fromstring(program_xml_str)
        new_xml_tree = cls().replace_tags_for_provisioning(xml_tree)
        return ET.tostring(new_xml_tree).decode("utf-8")
