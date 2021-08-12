from PyPDF2.pdf import PdfFileReader, PageObject
import urllib.request
import requests
from bs4 import BeautifulSoup
import numpy as np
import os
from urllib.parse import urljoin

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

from operator import itemgetter, truediv
from bisect import bisect_left, bisect_right
from PyPDF2.pdf import PdfFileReader, PageObject

#Printing metadata from PDF using PyPDF2
def extract_information(pdf_path):
    with open(pdf_path, 'rb') as f:
        pdf = PdfFileReader(f)
        pdf2 = PageObject(pdf=pdf)
        information = pdf.getDocumentInfo()
        number_of_pages = pdf.getNumPages()
        text = pdf2.getContents()

    txt = f"""
    Information about {pdf_path}: 

    Author: {information.author}
    Creator: {information.creator}
    Producer: {information.producer}
    Subject: {information.subject}
    Title: {information.title}
    Number of pages: {number_of_pages}
    Contents: {text}
    """

    print(txt)
    
    return information

#Extracting Text from PDF using PyPDF2
def extract_text(pdf_path):
    with open(pdf_path, 'rb') as f:
        pdf = PdfFileReader(f)
        #pdf2 = PageObject(pdf=pdf)
        number_of_pages = pdf.getNumPages()
        pageobj = pdf.getPage(number_of_pages+1)
        text = pageobj.extractText()
        
        pdf_text = ""
        for num in range(number_of_pages):
            page = pdf.getPage(num)
            pdf_text += page.extractText()

    #return pdf_text
    return text

#Determines whether or not a file exists within a directory
def file_exists(file):
    ind = os.path.exists(file)
    return ind

#This function takes a list search queries and searches the bioRxiv for relevant articles and downloads them to the environment
def search_bioRxiv(queries):
    page_num = 1
    for query in queries:
        directory = query
        path = os.path.join(floc, directory)
        os.mkdir(path)
        query = query.replace(" ", "%252B")
        URL = "https://www.biorxiv.org/search/" + query + "%20jcode%3Abiorxiv%20numresults%3A75%20sort%3Arelevance-rank%20format_result%3Astandard"
        req = urllib.request.Request(URL, headers={'User-Agent' : "Magic Browser"})
        response = urllib.request.urlopen( req )
        html = response.read()

        # Parsing response
        soup = BeautifulSoup(html, 'html.parser')

        # Extracting number of results
        resultStats = soup.find(id="page-title").string
        print(resultStats)

        #Retrieving page numbers
        if(soup.find('div', class_='highwire-list page-group-items item-list')):
            page_list = soup.find('div', class_='highwire-list page-group-items item-list')
            pages = page_list.find_all('a')
            page_num = int(pages[-1].get_text())
            print(page_num)

        #Accessing articles
        for x in range(0, page_num):
            y = str(x)
            URL = "https://www.biorxiv.org/search/" + query + "%20jcode%3Abiorxiv%20numresults%3A75%20sort%3Arelevance-rank%20format_result%3Astandard?page=" + y
            req = urllib.request.Request(URL, headers={'User-Agent' : "Magic Browser"})
            response = urllib.request.urlopen( req )
            html = response.read()

            # Parsing response
            soup = BeautifulSoup(html, 'html.parser')

            results = soup.find_all(href=True, class_='highwire-cite-linked-title')
            for link in results:
                new_URL = "https://www.biorxiv.org" + link['href'] + ".full.pdf"
                #Name the pdf files using the last portion of each link which are unique in this case
                filename = os.path.join(path, link['href'].split('/')[-1] + ".full.pdf")
                # with open(filename, 'wb') as f:
                #     f.write(requests.get(new_URL).content)
                if file_exists(filename) == True:
                    print("File Already Exists")
                elif file_exists(filename) == False:
                    with open(filename, 'wb') as f:
                        f.write(requests.get(new_URL).content)

#Retrieves metadata embeded in bioRxiv webpage                       
def get_web_metadata(URL):
    req = urllib.request.Request(URL, headers={'User-Agent' : "Magic Browser"})
    response = urllib.request.urlopen( req )
    html = response.read()

    # Parsing response
    soup = BeautifulSoup(html, 'html.parser')
    
    #Retrieve metadata from bioRxiv webpage
    meta_data = soup.find('head')
    meta = meta_data.find_all('meta')
    print(meta)


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
                with open('SULI 2021/Annotations2.txt', 'a') as f:
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

def find_annot2(path):      
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

# This function converts PDF to text using PyMuPDF
def pymu(path):
    with fitz.open(path) as file:
        string = ""
        for page in file:
            string+= page.getText("text")
        return string


# This function converts PDF to text using PYPDF2
def pyPDF(path):
    # creating a pdf file object  
    string = ""
    with open(path, 'rb') as f:
        print(path)
        pdf = PdfFileReader(f)
        num = pdf.numPages
        for n in range(num):
            page = pdf.getPage(n)
            string += page.extractText()
    # creating a pdf reader object 
    return string

########################################################################
########################################################################
################### Converting to text using PDF Miner #################

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
            return result
    except IOError:
        # the file doesn't exist or similar problem
        pass

########################## END ################################
###############################################################
###############################################################

def _parse_pages(document):
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
            
    text_content = [] # a list of strings, each representing text collected from each page of the doc
    for i, page in enumerate(PDFPage.get_pages(document)):
        interpreter.process_page(page)
        # receive the LTPage object for this page
        layout = device.get_result()
        # layout is an LTPage object which may contain child objects like LTTextBox, LTFigure, LTImage, etc.
        text_content.append(parse_lt_objs(layout.objs, (i+1)))
    
    return text_content

# This function returns a string with the text in a pdf prior to the references section
def elim_ref(str):
    if str.find("\nReferences"):
        x = str.rpartition('\nReferences')      
        x = x[0]
        return x
    elif str.find("\nREFERENCES"):
        x = str.rpartition('\nREFERENCES')
        x = x[0]
        return x
    else:
        return str

    
# This function checks if the below words are in the string
def isWords(str):
    if re.search('Fe', str) and re.search('protein', str, flags=re.IGNORECASE) and re.search('crystal', str, flags=re.IGNORECASE):
        return True
    else:
        return False


# This function deletes files from within a directory if the keywords within the function 
# above are not found in the article before the references section
def delete_files(dir):
    count = 0
    for filename in os.listdir(dir):        
        filename = dir + '/' + filename
        pdf_string = pymu(filename)
        pdf_string_wo_ref = elim_ref(pdf_string)
        result = isWords(pdf_string_wo_ref)
        if result == True:
            continue
        else:
            os.remove(filename)
            count = count+1
    print(count)

# This function converts PDF files to text files only containing the text before the references section
def conv2txt_wo_ref(dir):
    for filename in os.listdir(dir):        
        file = dir + '/' + filename
        pdf_string = pymu(file)
        pdf_string_wo_ref = elim_ref(pdf_string)
        with open(dir + '/' + filename +'.txt', 'w', encoding="utf-8") as f:
                f.write(pdf_string_wo_ref)

# This functions determines how many files in a directory are empty or not
def isTagged(dir):
    count = 0
    for filename in os.listdir(dir):
        filename = dir + '/' + filename   
        if os.stat(filename).st_size == 0:
            count = count + 1
        else:
            count = count
    return count

# This funstion converted all the pdf files to text files in
def pymupdf_gen(dir):
    for root, dirs, files in os.walk(dir):
        for name in files:
            if name.endswith(".pdf"):
                with fitz.open(name) as file:
                    string = ""
                    for page in file:
                        string+= page.getText("text")
                        with open(root + '/' + dirs + '/' + name +'.txt', 'w') as f:
                            f.write(string)
                            
if __name__ == '__main__':
    
    path = 'SULI 2021/MoFe_PDB/1-s2.0-S0021925818367590-main_DK.pdf'
    #Printing metadata from PDF using PyPDF2
    extract_information(path)
    
    #Determines whether or not a file exists within a directory
    print(file_exists(path))  
    
    #File location that PDFs will be downloaded to in the virtual environment
    floc = "SULI 2021/testFolder"
    
    #Search query to be searched in bioRxiv simple search
    search_queries = ["P-loop NTPase AND fe"]
    
    #Searched bioRxiv using passed query, prints number of results, and ownloads them to floc
    search_bioRxiv(search_queries)
    
    #URL of the landing pape for a bioRxiv article
    URL = 'https://www.biorxiv.org/content/10.1101/420133v1'
    
    #Retrieves metadata embeded in bioRxiv webpage                       
    #get_web_metadata(URL)
    
    path2 = 'SULI 2021/Fe Articles/041772v1.full.pdf'
    
    #Converts PDF to text using PyMuPDF
    text = pymu(path2)
    print(text)
    
    text_wo_ref = elim_ref(text)
    print(text_wo_ref)
    
    #Checks if the below words are in the string
    print(isWords(text))
    
    floc2 = 'SULI 2021/testFolder/P-loop NTPase AND fe'
    # This function deletes files from within a directory if the keywords within the isWords() function 
    # are not found in the article before the references section. It also prints how many files were deleted.
    delete_files(floc2)
    
    # This function converts PDF files to text files only containing the text before the references section
    conv2txt_wo_ref(floc2)

    dir_annot('SULI 2021/MoFe_PDB')
    
    #Determines how many files in a directory are empty or not
    print(isTagged(floc))
    
    pymupdf_gen('data')
    