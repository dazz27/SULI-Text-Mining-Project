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
from operator import itemgetter, truediv
from itertools import groupby
import fitz
from bisect import bisect_left, bisect_right
from PyPDF2.pdf import PdfFileReader, PageObject

class SortedCollection(object):
    def __init__(self, iterable=(), key=None):
        self._given_key = key
        key = (lambda x: x) if key is None else key
        decorated = sorted((key(item), item) for item in iterable)
        self._keys = [k for k, item in decorated]
        self._items = [item for k, item in decorated]
        self._key = key

    def _getkey(self):
        return self._key

    def _setkey(self, key):
        if key is not self._key:
            self.__init__(self._items, key=key)

    def _delkey(self):
        self._setkey(None)

    key = property(_getkey, _setkey, _delkey, 'key function')

    def clear(self):
        self.__init__([], self._key)

    def copy(self):
        return self.__class__(self, self._key)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, i):
        return self._items[i]

    def __iter__(self):
        return iter(self._items)

    def __reversed__(self):
        return reversed(self._items)

    def __repr__(self):
        return '%s(%r, key=%s)' % (
            self.__class__.__name__,
            self._items,
            getattr(self._given_key, '__name__', repr(self._given_key))
        )

    def __reduce__(self):
        return self.__class__, (self._items, self._given_key)

    def __contains__(self, item):
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return item in self._items[i:j]

    def index(self, item):
        'Find the position of an item.  Raise ValueError if not found.'
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return self._items[i:j].index(item) + i

    def count(self, item):
        'Return number of occurrences of item'
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return self._items[i:j].count(item)

    def insert(self, item):
        'Insert a new item.  If equal keys are found, add to the left'
        k = self._key(item)
        i = bisect_left(self._keys, k)
        self._keys.insert(i, k)
        self._items.insert(i, item)

    def insert_right(self, item):
        'Insert a new item.  If equal keys are found, add to the right'
        k = self._key(item)
        i = bisect_right(self._keys, k)
        self._keys.insert(i, k)
        self._items.insert(i, item)

    def remove(self, item):
        'Remove first occurence of item.  Raise ValueError if not found'
        i = self.index(item)
        del self._keys[i]
        del self._items[i]

    def find(self, k):
        'Return first item with a key == k.  Raise ValueError if not found.'
        i = bisect_left(self._keys, k)
        if i != len(self) and self._keys[i] == k:
            return self._items[i]
        raise ValueError('No item found with key equal to: %r' % (k,))

    def find_le(self, k):
        'Return last item with a key <= k.  Raise ValueError if not found.'
        i = bisect_right(self._keys, k)
        if i:
            return self._items[i-1]
        raise ValueError('No item found with key at or below: %r' % (k,))

    def find_lt(self, k):
        'Return last item with a key < k.  Raise ValueError if not found.'
        i = bisect_left(self._keys, k)
        if i:
            return self._items[i-1]
        raise ValueError('No item found with key below: %r' % (k,))

    def find_ge(self, k):
        'Return first item with a key >= equal to k.  Raise ValueError if not found'
        i = bisect_left(self._keys, k)
        if i != len(self):
            return self._items[i]
        raise ValueError('No item found with key at or above: %r' % (k,))

    def find_gt(self, k):
        'Return first item with a key > k.  Raise ValueError if not found'
        i = bisect_right(self._keys, k)
        if i != len(self):
            return self._items[i]
        raise ValueError('No item found with key above: %r' % (k,))


# ---------------------------  Simple demo and tests  -------------------------
if __name__ == '__main__':

    def ve2no(f, *args):
        'Convert ValueError result to -1'
        try:
            return f(*args)
        except ValueError:
            return -1

    def slow_index(seq, k):
        'Location of match or -1 if not found'
        for i, item in enumerate(seq):
            if item == k:
                return i
        return -1

    def slow_find(seq, k):
        'First item with a key equal to k. -1 if not found'
        for item in seq:
            if item == k:
                return item
        return -1

    def slow_find_le(seq, k):
        'Last item with a key less-than or equal to k.'
        for item in reversed(seq):
            if item <= k:
                return item
        return -1

    def slow_find_lt(seq, k):
        'Last item with a key less-than k.'
        for item in reversed(seq):
            if item < k:
                return item
        return -1

    def slow_find_ge(seq, k):
        'First item with a key-value greater-than or equal to k.'
        for item in seq:
            if item >= k:
                return item
        return -1

    def slow_find_gt(seq, k):
        'First item with a key-value greater-than or equal to k.'
        for item in seq:
            if item > k:
                return item
        return -1

# This function converts PDF to text using PyMuPDF
def pymu(path):
    try:
        with fitz.open(path) as file:
            string = ""
            for page in file:
                string+= page.getText("text")
            return string

    except:
        string = ""
        with open(path, 'rb') as f:
            pdf = PdfFileReader(f)
            num = pdf.numPages
            for n in range(num):
                page = pdf.getPage(n)
                string += page.extractText()
            # creating a pdf reader object 
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
        for y in x:
            y = y.replace('\n', '\n')
        y = y[0]
        y = str[:str.find("References")]
        return y
    elif str.find("\nREFERENCES"):
        x = str.rpartition('\nREFERENCES')
        for y in x:
            y = y.replace('\n', '\n')
        y = y[0]
        y = str[:str.find("REFERENCES")]
        return y
    else:
        return str
    #x = re.findall('References$', str, flags=re.MULTILINE)
    #x = re.sub('/^(.*?)\\\REFERENCES/', '', str)
    #x = str.split('REFERENCES')
    
# This function checks if the below words are in the string
def isWords(str):
    if re.search('Fe', str) and re.search('protein', str, flags=re.IGNORECASE) and re.search('crystal', str, flags=re.IGNORECASE):
        return True
    else:
        return False

# This function deletes files from within a directory if the keywords within the function 
# above are not found in the article before the references section
def delete_files(dir):
    for filename in os.listdir(dir):        
        filename = dir + '/' + filename
        pdf_string = pyPDF(filename)
        pdf_string_wo_ref = elim_ref(pdf_string)
        #result = isWords(pdf_string)
        result = isWords(pdf_string_wo_ref)
        if result == True:
            continue
        else:
            os.remove(filename)

# This function converts PDF files to text files only containing the text before the references section
def conv2txt_wo_ref(dir):
    for filename in os.listdir(dir):        
        file = dir + '/' + filename
        pdf_string = pymu(file)
        pdf_string_wo_ref = elim_ref(pdf_string)
        with open(dir + '/' + 'NoRef' + '/' + filename +'.txt', 'w') as f:
            for line in pdf_string_wo_ref:
                f.write(line)

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

if __name__ == '__main__':
    #path = 'bioRxiv_Articles/010322v1.full.pdf'
    #path = 'bioRxiv_Articles/003350v1.full.pdf'
    path = 'Fe Articles/870154v3.full.pdf'
    path2 = 'Fe Articles/410019v2.full.pdf'
    #delete_files('bioRxiv_Articles3')
    #conv2txt_wo_ref('Fe Articles')
    
    x = pymu(path)
    print(elim_ref(x))

    