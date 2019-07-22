# test case'ai:
# 1. svarus grazus failiukas be jokiu balaganu
# 2. failiukas su vienu pasikartojanciu codelistu
# 3. failiukas su keliais pasikartojanciais codelistais
# 4. failiukas su vienu pasikartojanciu codelistu ir clashais jame
# 5. failiukas su keliais pasikartojanciais codelistais ir clashais visuose juose

import os
import xml.etree.ElementTree as et
import time

from bs4 import BeautifulSoup as bs
from colorama import init, Back, Fore
from freg_funkcijos import normalize_text, print_xml, openxml, register_namespaces, remove_version_et, remove_version_str
from openpyxl import Workbook
from openpyxl.cell import Cell
from openpyxl.styles import Alignment, Font
from xml.etree.ElementTree import Element, ElementTree

def sublist(sublist, full_list): # patikrina ar sublist masyvas yra full_list masyvo poaibis
    lst1 = list(full_list) # kad jau tikrai sąrašas būtų
    lst2 = list(sublist)
    ls1 = [element for element in lst1 if element in lst2]
    return ls1 == lst2

def ets_equal(et1, et2):
    tag1 = et1.tag
    tag2 = et2.tag
    if tag1 != tag2:
        return False

    attrib1 = str(et1.attrib) # reikia sukurti kopiją, kitaip modifikuojamas originalus objektas
    attrib2 = str(et2.attrib)
    attrib1 = remove_version_str(attrib1) # nustatoma 1.0 versija
    attrib2 = remove_version_str(attrib2)
    if attrib1 != attrib2:
        return False

    text1 = normalize_text(et1.text)
    text2 = normalize_text(et2.text)
    if text1 != text2:
        return False

    if (list(et1) == []) ^ (list(et2) == []): # jei vienas turi chlild elementų, o kitas ne
        return False

    if (list(et1) != []) and (list(et2) != []): # jei abu turi child elementų
        if not children_equal(et1, et2): # jei tie child elementai nėra lygūs
            return False

    return True

def children_equal(et1, et2):

    children = list(et1) + list(et2) # bendras visų vaikų sąrašas
    total_len = len(children)

    for i, child in enumerate(children):
        for n in range(i+1, len(children)):
            if ets_equal(child, children[n]):
                children[i] = 0 # dublikatams nustatoma žinoma reikšmė

    while 0 in children:
        children.remove(0) # žinoma reikšmė pašalinama
        if 2 * len(children) == total_len: # ar et1 ir et2 vaikai sutapo
            return True
            
    return False

def conflict(et1, et2): # ar et1 ir et2 aprašo tą pačią rakto reikšmę (t.y. konfliktuoja vienas su kitu)
    try: # gali mesti exception, kai bandoma pasiekti neegzistuojantį atributą (šiuo atveju 'value')
        value1 = et1.attrib['value']
        value2 = et2.attrib['value']
        if value1 == value2:
            return True
    except:
        try:
            if et1.tag == et2.tag == 'str:Name':
                lang1 = et1.attrib['xml:lang']
                lang2 = et2.attrib['xml:lang']
                if lang1 == lang2:
                    return True
        except:
            return False
        return False
    return False

def sortCode(et):
    try:
        urn = et.attrib['urn']
        key = urn.split('.')
        key = str((et.tag)) + key[-1]
        return key
    except:
        return '_'

def parse_xml_codelist(codelists, id):
    descriptions = []
    urns = []
    
    for codelist in codelists:   # codelist === vienos codelist versijos kodai (įrašai) -> "urn:sdmx:org.sdmx.infomodel.codelist.Codelist=LB:KS_APREPTIS_UVR(1.0).E"
        try:
            urns.append(codelist)
        except Exception as e:
            print('freg.py exception 1: ', e)
            pass

    urns.insert(0, descriptions) # kiekvienas description masyvas yra urns masyvo dalis (masyvų masyvas) ir yra vienos versijos codelistas

    descriptions = []
    conflicts = {}

    for codelist in urns: # skirtingos versijos su tuo pačiu id
        for code in codelist: # eina per visus vienos versijos įrašus
            flag = 0
            for element in descriptions: # tikrina, ar jau nėra tokio paties įrašo
                if ets_equal(element, code):
                    flag = 1

                elif conflict(element, code):
                    # patikrinti, ar vaikai lygūs
                    children = list(element) + list(code)
                    for i, child in enumerate(children):
                        for n in range(i+1, len(children)):
                            if ets_equal(child, children[n]):
                                children[i] = 0

                    while 0 in children:
                        children.remove(0)

                    if sublist(children, list(element)):
                        flag = 1
                        break

                    elif sublist(children, list(code)):
                        flag = 0
                        descriptions.remove(element)
                        break

                    # čia reikia padaryti, kad generuotų žodyną su konfliktais (KS_APREPTIS_UVR.A : [conflicting_element1, conflicting_element2, conflicting_element3])
                    conflict_id = code.attrib['urn']
                    conflict_id = conflict_id.split(':')[-1]
                    conflict_id = remove_version_str(conflict_id)

                    if conflict_id in conflicts:
                        if not any(ets_equal(code, elem) for elem in conflicts[conflict_id]):
                            conflicts[conflict_id].append(code)
                    else:
                        conflicts[conflict_id] = [element, code]
                    flag = 1
            if flag == 0:
                descriptions.append(code) # tvarkingai surūšiuotas masyvas nuo didžiausios versijos iki mažiausios
    descriptions.sort(key = sortCode)
    # gal tiesiog geriau grąžinti vieną jau paruoštą codelistą ir jį appendinti prie codelists childo (ir removint visus kitus pradinius codelistus su tuo id)????
    return descriptions, conflicts

def main(filename):
    init()
    rt = openxml('small_codelist.xml')
    _, codelists = list(rt)
    
    versions = {}
    final_conflict_array = []

    for codelist in codelists: # kiekvienai rakto versijai sukuriamas atskiras codelistas

        # visus codelistus su tuo pačiu id sugrupuoja į vieną masyvą
        id = codelist.attrib['id']
        if id in versions:
            versions[id].append(codelist)
        else:
            versions[id] = [codelist]

    for id in versions:
        new_codelist, conflicts = parse_xml_codelist(versions[id], id)

        # atsikrato visų versijų, išskyrus pirmą sąraše
        for version in versions[id][1:]:
            codelists.remove(version)
        
        # nustato pirmos versijos atributus (kad likusi versija tikrai būtų pirmoji)
        versions[id][0].attrib['version'] = '1.0'
        versions[id][0].attrib['urn'] = remove_version_str(versions[id][0].attrib['urn']) # nustato versiją į 1.0
        versions[id][0].attrib['isFinal'] = 'true'
        
        # iš likusios versijos codelisto išmeta VISUS kodus
        for code in reversed(versions[id][0]):
            versions[id][0].remove(code)

        # prie jau tuščios versijos prideda naujus ir sutvarkytus kodus
        for code in new_codelist:
            versions[id][0].append(remove_version_et(code))

        # sukuriamas parent, child masyvas ir pridedamas prie final_conflict_array masyvo
        parent = versions[id][0]
        final_conflict_array.append((parent, conflicts))

    # pasiruošiama darbui su excel
    wb = Workbook()
    ws = wb.active

    # konfliktai surašomi į excel dokumentą
    for _, conflicts in final_conflict_array:
        for id in conflicts:
            ws.append([id])
            key_values = []
            for elem in conflicts[id]:
                key_values.append(print_xml(elem))

            ws.append(key_values)

    #print(len(final_conflict_array))

    # set height and width of cells
    for i, row in enumerate(ws.iter_rows()):
        for cell in row:
            cell.alignment = Alignment(wrap_text = True) # nustatoma, kad viename Excel langelyje automatiškai perkeltų tekstą į kitą eilutę, taip nusistato ir stulpelio aukštis

    for col in ws.iter_cols():
        ws.column_dimensions[col[0].column_letter].width = 110 # nustatomas langelio plotis
    
    wb.save('%s.xlsx' % filename) # išsaugomas Excel dokumentas


     # pasiruošiama darbui su excel


    # set height and width of cells
    for i, row in enumerate(ws.iter_rows()):
        for cell in row:
            cell.alignment = Alignment(wrap_text = True) # nustatoma, kad viename Excel langelyje automatiškai perkeltų tekstą į kitą eilutę, taip nusistato ir stulpelio aukštis

    for col in ws.iter_cols():
        ws.column_dimensions[col[0].column_letter].width = 110 # nustatomas langelio plotis
    
    wb.save('%s.xlsx' % filename) # išsaugomas Excel dokumentas









    final_string = et.tostring(rt)
    with open('%s.xml' % filename, 'wb') as f:
        f.write(final_string) # išsaugomas xml failas, tačiau vietoje konfliktų prisegama pirma versija (vėliau parenkama, kokia norima)

    print(Back.GREEN + 'Programa baigė darbą sėkmingai' + Back.BLACK)

main('new_small_codelist')
