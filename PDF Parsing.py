from PyPDF2.pdf import PdfFileReader, PageObject
import urllib.request
import requests
from bs4 import BeautifulSoup
import numpy as np
import os
from urllib.parse import urljoin

#import fitz

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

#This function takes a list search queries and searches the bioRxiv for relevant articles and downloads them to the environment
def search_bioRxiv(queries):
    for query in queries:
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
                filename = os.path.join(floc ,link['href'].split('/')[-1])
                with open(filename, 'wb') as f:
                    f.write(requests.get(new_URL).content)

if __name__ == '__main__':
   
    #File location that PDFs will be downloaded to in the virtual environment
    #floc = "/home/dhunt/py-venv/2021-SULI-Text-Mining1/SULI-Text-Mining-Project"
    floc = "/hpcgpfs01/scratch/dhuntSULI2021/2021-SULI-Text-Mining/SULI-Text-Mining-Project/bioRxiv_Articles"

    #search_queries = ["P-loop NTPase", "P-loop GTPase", "Fe protein", "Walker A motif", "nitrogenase reductase", "Nif-like", "dinitrogenase", "MoFe protein", "heterotetramer", "Molybdenum nitrogenase"]
    search_queries = ["protein"]

    search_bioRxiv(search_queries)

    #Test PDF File Paths 
    # path = '2021.02.08.430359v2.full.pdf'
    path = '439992v1'

    #Print metadata - PyPDF2.pdf
    extract_information(path)
    
    #Print metadata - PyMuPDF
    # doc = fitz.open(path)
    # page = doc.load_page(0)
    # met = doc.metadata
    # print(met)

    ##prints text on a page 
    #text = page.get_text("html")
    #print(text)


   # Original Code to Download pdf from website based on given link with embeded PDF
    # #URL = "https://www.biorxiv.org/content/10.1101/2021.02.08.430359v2"
    # response = requests.get(URL)
    # soup= BeautifulSoup(response.text, "html.parser")     
    # # results = soup.find(class_='article-dl-pdf-link')
    # for link in soup.select("a[href$='.pdf']"):
    # #Name the pdf files using the last portion of each link which are unique in this case
    #     filename = os.path.join(floc ,link['href'].split('/')[-1])
    #     with open(filename, 'wb') as f:
    #         f.write(requests.get(urljoin(URL,link['href'])).content)