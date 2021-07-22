#from _typeshed import NoneType
from fitz.fitz import Annot
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
from io import StringIO
import re
import os
#import pdftotext
from operator import is_not, itemgetter
from itertools import groupby
import fitz

def pymu(path):
    file = fitz.open(path)

    for page in file:
        text = page.getText("text")
        list = page.searchFor("fe protein")
        for l in list:
            print(l)
        #print(text)
        # txt = open(f'samplePDF.txt', 'a')
        # txt.writelines(text)
        # txt.close()

def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec='utf-8', laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set()
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
        interpreter.process_page(page)
    fp.close()
    device.close()
    str = retstr.getvalue()
    retstr.close()
    return str

def conv2txt(pdf):
    try:
        fp = open(pdf, 'rb')
        parser = PDFParser(fp)
        document = PDFDocument(parser)
        parser.set_document(document)

        # if not document.is_extractable:
        #     raise PDFTextExtractionNotAllowed
        if document.is_extractable:
        # apply the function and return the result
            result = document
    
        fp.close()
    except IOError:
        # the file doesn't exist or similar problem
        pass

    return result


# This functions loops through a given directory and retrieves annotation info
def dir_annot(dir):
    for filename in os.listdir(dir):        
        filename = dir + '/' + filename
        find_annot(filename)

# This function detects highlights within the PDF and extracts the info
def find_annot(pdf):
    doc = fitz.open(pdf)
    for page in doc:
        for ann in page.annots():
            all_annot_info = ann.info
            str = all_annot_info['content'].split(": ")
            for s in str:
                if "\r" in s:
                    s = s.replace('\r', " ")
                with open('Annotations.txt', 'a') as f:
                    f.write(s.strip()+'\n')
                print(s.strip()+'\n')
                


#############################################################################
#############################################################################
############## PYMUPDF Detecting Text Within Highlighted Text ###############

_threshold_intersection = 0.9

def _check_contain(r_word, points):
    """If `r_word` is contained in the rectangular area.

    The area of the intersection should be large enough compared to the
    area of the given word.

    Args:
        r_word (fitz.Rect): rectangular area of a single word.
        points (list): list of points in the rectangular area of the
            given part of a highlight.

    Returns:
        bool: whether `r_word` is contained in the rectangular area.
    """
    # `r` is mutable, so everytime a new `r` should be initiated.
    r = fitz.Quad(points).rect
    r.intersect(r_word)

    if r.getArea() >= r_word.getArea() * _threshold_intersection:
        contain = True
    else:
        contain = False
    return contain

def find_annot(path):      
    doc = fitz.open(path)
    page = doc[0]                    
    ann = page.firstAnnot
    # for ann in page.annots():
    #     text = ann.getText()
    #     #print(text)
    #     print(ann.info)
    words = page.getText("words")  # list of words on page
    words.sort(key=lambda w: (w[3], w[0]))  # ascending y, then x

    lines = []
    while ann:
        if ann.type[0] in (8, 9, 10, 11): # one of the 4 types above   
            #rect = ann.rect # this is the rectangle the annot covers
            # extract the text within that rect ...
            #annot = annot.next # None returned after last annot
            
            #mywords = [w for w in words if fitz.Rect(w[:4]).intersects(rect)]
            # group = groupby(mywords, key=lambda w: w[3])
            #for y1, gwords in group:
                #print(" ".join(w[4] for w in gwords))
            
            points = ann.vertices
            quad_count = int(len(points) / 4)
            sentences = ['' for i in range(quad_count)]
            for i in range(quad_count):
                r = fitz.Quad(points[i * 4 : i * 4 + 4]).rect
                for w in words:
                    if fitz.Rect(w[:4]) in r:
                        lines.append(w[4])

            #print(" ".join(lines))
                # word = [
                #     w for w in words if
                #     _check_contain(fitz.Rect(w[:4]), points)
                # ]
                # sentences[i] = ' '.join(w[4] for w in word)
                # sentence = ' '.join(sentences)
                
                # lines.append(sentence)
            
        ann = ann.next
            # highlight_words = []
            # for i in range(quad_count):
            #     r = fitz.Quad(points[i * 4 : i * 4 + 4]).rect
            # for w in words:
            #     if fitz.Rect(w[:4]) in r:
            #         highlight_words.append(w[4])

            # print(" ".join(highlight_words))
    return lines

def print_hightlight_text(rect):
    """Return text containted in the given rectangular highlighted area.

    Args:
        page (fitz.page): the associated page.
        rect (fitz.Rect): rectangular highlighted area.s
    """
    doc = fitz.open('2021.02.08.430359v2.full.pdf')
    pag = doc[0]     
    words = pag.getText("words")  # list of words on page
    words.sort(key=lambda w: (w[3], w[0]))  # ascending y, then x
    mywords = [w for w in words if fitz.Rect(w[:4]).intersects(rect)]
    group = groupby(mywords, key=lambda w: w[3])
    for y1, gwords in group:
        print(" ".join(w[4] for w in gwords))

################################# END #######################################
#############################################################################
#############################################################################

if __name__ == '__main__':
    path = 'bioRxiv_Articles copy/872879v1.full.pdf'
    path2 = '2021.02.08.430359v2.full.pdf'
    path3 = 'astro-ph0001004.pdf'
    # x = conv2txt(path)
    # x = convert_pdf_to_txt(path)
    # t = elim_ref(x)
    # isWords(t)
    # delete_files('bioRxiv_Articles2')

    #pymu(path)
    #z = find_page(path2)
    # y = find_annot(z)
    # print_hightlight_text(y)

    dir_annot('Sample_annotation by Dale')
    dir_annot('MoFe_annotation_by_Dale')
