from PyPDF2.pdf import PdfFileReader, PageObject
import urllib.request
import requests
from bs4 import BeautifulSoup
import numpy as np
import os
from urllib.parse import urljoin

import fitz


def extract_information(pdf_path):
    with open(pdf_path, 'rb') as f:
        pdf = PdfFileReader(f)
        pdf2 = PageObject(pdf=pdf)
        page = pdf.getPage(1)
        print(page.extractText())
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

if __name__ == '__main__':
   
    #File location that PDFs will be downloaded to in the virtual environment
    floc = "/home/dhunt/py-venv/2021-SULI-Text-Mining1/SULI-Text-Mining-Project"

    
    # Downloads pdf from website
    URL = "https://www.biorxiv.org/content/10.1101/2021.02.08.430359v2"
    response = requests.get(URL)
    soup= BeautifulSoup(response.text, "html.parser")     
    # results = soup.find(class_='article-dl-pdf-link')
    for link in soup.select("a[href$='.pdf']"):
    #Name the pdf files using the last portion of each link which are unique in this case
        filename = os.path.join(floc ,link['href'].split('/')[-1])
        with open(filename, 'wb') as f:
            f.write(requests.get(urljoin(URL,link['href'])).content)
        
    path = '2021.02.08.430359v2.full.pdf'

    #Print metadata - PyPDF2.pdf
    extract_information(path)
    
    #Print metadata - PyMuPDF
    doc = fitz.open(path)
    page = doc.load_page(0)
    met = doc.metadata
    print(met)

    ##prints text on a page 
    #text = page.get_text("html")
    #print(text)

