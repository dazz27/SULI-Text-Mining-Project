from PyPDF2.pdf import PdfFileReader, PageObject
import urllib.request
import requests
from bs4 import BeautifulSoup
import numpy as np
import os
from urllib.parse import urljoin
#from pdf2image import convert_from_path

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
    


if __name__ == '__main__':
   
    #File location that PDFs will be downloaded to in the virtual environment
    floc = "/home/dhunt/py-venv/2021-SULI-Text-Mining1/SULI-Text-Mining-Project/bioRxiv_Articles/"
    #floc = "/home/dhunt/py-venv/2021-SULI-Text-Mining1/SULI-Text-Mining-Project/bioRxiv_Articles2/"
    #floc = "/hpcgpfs01/scratch/dhuntSULI2021/2021-SULI-Text-Mining/SULI-Text-Mining-Project/bioRxiv_Articles/"

    #search_queries = ["P-loop NTPase", "P-loop GTPase", "Fe protein", "Walker A motif", "nitrogenase reductase", "Nif-like", "dinitrogenase", "MoFe protein", "heterotetramer", "Molybdenum nitrogenase"]
    #search_queries = ["fe AND protein AND crystal"]
    search_queries = ["MoFe protein nitrogenase", "Molybdenum-iron protein nitrogenase", "MoFeP nitrogenase", "MoFe protein crystallization", "Molybdenum-iron protein crystallization", "MoFeP crystallization", "MoFe protein crystal structure", "Molybdenum-iron protein crystal structure", "MoFeP crystal structure", "MoFe protein crystallized", "Molybdenum-iron protein crystallized", "MoFeP crystallized"]

    search_bioRxiv(search_queries)

    #srun -p volta -A nlp -sbu -t 24:00:00 -N1 --gres=gpu:8 -J test \
    
    #Test PDF File Paths 
    # path = '2021.02.08.430359v2.full.pdf'
    path = 'bioRxiv_Articles/2021.07.01.450417v1.full.pdf'

    #Print metadata - PyPDF2.pdf
    #extract_information(path)

    #get_web_metadata("https://www.biorxiv.org/content/10.1101/2021.05.13.443919v2")

    # Store Pdf with convert_from_path function
    # images = convert_from_path(path)

    # for i in range(len(images)):
    #     # Save pages as images in the pdf
    #     images[i].save('page'+ str(i) +'.jpg', 'JPEG'
    
    #Print metadata - PyMuPDF
    # doc = fitz.open(path)
    # page = doc[0]
    # #met = doc.metadata
    # links = page.get_toc()
    # print(links)

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