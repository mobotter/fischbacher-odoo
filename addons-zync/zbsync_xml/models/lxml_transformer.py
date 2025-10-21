# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from lxml import etree


def xml_to_dict(element):
    """
    Recursively converts an XML element to a dictionary.
    """
    if element.tag is etree.Comment:
        return None
    d = {element.tag: {} if element.attrib else None}
    children = list(element)
    if children:
        for child in children:
            cd = xml_to_dict(child)
            if child.tag in (d[element.tag] or []):
                if not isinstance(d[element.tag][child.tag], list):
                    d[element.tag][child.tag] = [d[element.tag][child.tag]]
                d[element.tag][child.tag].append(cd[child.tag] if cd else None)
            else:
                if d[element.tag] is None:
                    d[element.tag] = {}
                d[element.tag].update(cd)
    if element.attrib:
        d[element.tag].update(("@" + k, v) for k, v in element.attrib.items())
    if element.text:
        text = element.text.strip()
        if children or element.attrib:
            if text:
                d[element.tag]["#text"] = text
        else:
            d[element.tag] = text
    return d


def lxml_xml_string_to_dict(xml_string):
    """
    Converts an XML string to a dictionary.
    """
    root = etree.fromstring(xml_string)
    return xml_to_dict(root)
