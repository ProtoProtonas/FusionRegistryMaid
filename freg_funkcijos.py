import os
import time
import xml.etree.ElementTree as et

from bs4 import BeautifulSoup as bs
from colorama import init, Back, Fore
from openpyxl import Workbook
from openpyxl.styles import Alignment
from xml.etree.ElementTree import Element, ElementTree

TO_CHOP_OFF = [' ', '\n', '\t', '\r', '\xa0']
TO_DELETE = ['\t', '\r']

def normalize_text(text_to_normalize):
    normalized_text = str(text_to_normalize)
    
    for symbol in TO_DELETE:
        if str(symbol) in normalized_text:
            normalized_text = normalized_text.replace(symbol, '')

    while normalized_text:
        if any(s == normalized_text[0] for s in TO_CHOP_OFF):
            normalized_text = normalized_text[1:]
        elif any(s == normalized_text[-1] for s in TO_CHOP_OFF):
            normalized_text = normalized_text[:-1]
        else:
            break

    return str(normalized_text)

def print_xml(element):
    text = et.tostring(element, encoding = 'unicode')
    text = remove_version_str(text)
    text = bs(text, 'lxml')
    text = text.prettify()
    text = text.replace('<html>', '')
    text = text.replace('</html>', '')
    text = text.replace('<body>', '')
    text = text.replace('</body>', '')
    text = normalize_text(text)
    return text

def sortCode(et):
    try:
        tag = et.tag
        tag = tag.split('}')[-1]
        if tag == 'Code':
            tag = 'z' + tag
        urn = et.get('urn')
        value = et.get('value')
        key = tag + '.' + value + '.' + str(urn)
        return key
    except:
        urn = ''
        value = ''
        key = tag + '.' + value + '.' + str(urn)
        return key

def openxml(filename):

    with open(filename, 'r', errors = 'ignore') as f:
        file = f.read()

    register_namespaces(file)

    root = et.parse(filename).getroot()
    return root

def register_namespaces(file):
    start = file.find('Structure') + 10
    end = file[start:].find('>') + start
    structure = file[start:end]
    
    namespaces = {}
    start = structure.find('"') + 1

    while start != 0:
        end = structure[start:].find('"') + start

        namespace_start = structure[:start].rfind(':') + 1
        namespace_end = structure[namespace_start:].find('=') + namespace_start

        namespace = structure[namespace_start:namespace_end]
        uri = structure[start:end]
        namespaces[namespace] = uri
        
        structure = structure[end+1:]        
        start = structure.find('"') + 1

    del namespaces['schemaLocation']
    for ns in namespaces:
        et.register_namespace(ns, namespaces[ns])

def remove_version_str(urn):
    try:
        start = urn.rfind('(')
        end = urn.rfind(')') + 1

        _ = float(urn[start + 1:end - 1])

        if start == -1 or end == -1:
            return urn
        else:
            return urn[:start] + '(1.0)' + urn[end:]
    except Exception:
        return urn

def remove_version_et(obj):
    try:
        urn = remove_version_str(obj.attrib['urn'])
        new_obj = obj
        new_obj.attrib['urn'] = urn
        return new_obj
    except:
        return obj
