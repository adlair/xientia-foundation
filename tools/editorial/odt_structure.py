"""Read-only structural validation of generated ODTs (F4.1 R1)."""
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

TEXT='{urn:oasis:names:tc:opendocument:xmlns:text:1.0}'
OFFICE='{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'
ROMAN={'I':1,'V':5,'X':10,'L':50,'C':100}

@dataclass(frozen=True)
class Heading:
    level: int
    title: str

def headings_from_odt(path):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None: raise ValueError('ODT ZIP dañado')
        root=ET.fromstring(archive.read('content.xml'))
    body=root.find(f'{OFFICE}body/{OFFICE}text')
    if body is None: raise ValueError('Cuerpo ODT ausente')
    result=[]
    for el in body.iter(TEXT+'h'):
        level=el.get(TEXT+'outline-level')
        if not level or not level.isdecimal():raise ValueError('Nivel ODF inválido')
        title=''.join(el.itertext()).strip()
        if title:result.append(Heading(int(level),title))
    return result

def roman_number(value):
    if not re.fullmatch(r'[IVXLCDM]+',value):raise ValueError('Número romano inválido')
    vals={'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}
    n=sum((-vals[c] if i+1<len(value) and vals[c]<vals[value[i+1]] else vals[c]) for i,c in enumerate(value))
    if n<=0 or n>3999:raise ValueError('Número romano fuera de rango')
    def encode(n):
        out=''
        for x,s in [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]:
            while n>=x:out+=s;n-=x
        return out
    if encode(n)!=value:raise ValueError('Número romano no canónico')
    return n

def validate_structure(volume, headings):
    if volume not in ('XV-001','XEP-0000'):raise ValueError('Volumen no admitido por R1')
    chapters=[];articles=[];sections=[]
    for h in headings:
        chapter=re.match(r'^Capítulo\s+([IVXLCDM]+)\s+—\s+\S',h.title)
        article=re.match(r'^Artículo\s+(\d+)\.\s+\S',h.title)
        section=re.match(r'^(\d+)\.(\d+)\.\s+\S',h.title)
        if h.title.startswith('Capítulo ') and not chapter:raise ValueError('Capítulo malformado')
        if h.title.startswith('Artículo ') and not article:raise ValueError('Artículo malformado')
        if chapter:
            if h.level!=1:raise ValueError('Capítulo fuera de nivel 1')
            chapters.append(roman_number(chapter.group(1)))
        if article:
            if volume!='XEP-0000' or h.level!=2:raise ValueError('Artículo inesperado o fuera de nivel 2')
            articles.append(int(article.group(1)))
        if section and volume=='XV-001':
            if h.level!=2:raise ValueError('Subsección fuera de nivel 2')
            sections.append((int(section.group(1)),int(section.group(2))))
    expected=15 if volume=='XV-001' else 11
    if chapters!=list(range(1,expected+1)):raise ValueError('Secuencia de capítulos inválida')
    if volume=='XEP-0000' and articles!=list(range(1,34)):raise ValueError('Secuencia de artículos inválida')
    if volume=='XV-001':
        last=(0,0)
        for pair in sections:
            if pair[0] not in chapters or pair[0]<last[0] or (pair[0]==last[0] and pair[1]!=last[1]+1) or (pair[0]!=last[0] and pair[1]!=1):
                raise ValueError('Subsecciones fuera de secuencia')
            last=pair
    titles=[h.title for h in headings if h.level==1]
    if volume=='XV-001':
        required=['Declaración de Visión','Prefacio','Referencias y criterios de verificación']
    else:required=['Declaración','Referencias']
    if any(titles.count(x)!=1 for x in required):raise ValueError('Secciones preliminares/finales incorrectas')
    return {'volume':volume,'chapters':len(chapters),'articles':len(articles),'subsections':len(sections),'headings':len(headings)}

def validate_odt(volume,path):
    return validate_structure(volume,headings_from_odt(path))
