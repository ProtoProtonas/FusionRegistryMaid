import os
import xml.etree.ElementTree as et
import time

from bs4 import BeautifulSoup as bs
from colorama import init, Back, Fore
from freg_funkcijos import normalize_text, openxml, register_namespaces, remove_version_et, remove_version_str
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment
from xml.etree.ElementTree import Element, ElementTree

def open_xlsx(filename):
    wb = load_workbook(filename)
    return wb.active

def parse_str_to_element(child):
    elem = et.fromstring(child)
    return elem


def main(filename):
    init()
    ws = open_xlsx('%s.xlsx' % filename)
    
    rt = openxml('%s.xml' % filename)
    _, codelists = list(rt)


    rows = list(ws.iter_rows())
    for i, row in enumerate(rows):
        # kas antroje eilutėje yra raktai ir konfliktuojančios jų reikšmės
        if i % 2 == 0:
            parent = row[0].value
        else:
            row_value = ''

            for elem in row:
                if elem.value != None:
                    row_value = elem.value # row_value - vienoje eilutėje esančio snippeto reikšmė

            child = row_value
            child = parse_str_to_element(child) # string paverčiamas į etree.elemeent objektą
            
            # ieškoma codelisto su tokiu pačiu id, kaip parent
            for codelist in codelists:
                for code in codelist:
                    if 'urn' in code.attrib:
                        code_id = code.attrib['urn']
                        code_id = code_id.split(':')[-1]
                        code_id = remove_version_str(code_id)
                        if code_id == parent:
                            # pašalinamas kažkoks kodas (galimai ir teisingas) ir jo vietoj pridedamas tikrai teisingas
                            codelist.remove(code)
                            codelist.append(remove_version_et(child))
                            break

    final_string = et.tostring(rt)
    with open('%s.xml' % filename, 'wb') as f:
        f.write(final_string)

    print(Back.GREEN + 'Failas išsaugotas sėkmingai' + Back.BLACK)



main('new_small_codelist')
