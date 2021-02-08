import os, re, shutil, sys

from datetime import datetime

import json         # load and save json
import PyPDF2       # cleans PDFs
from scipy.spatial import distance # to calculate different distances

###########################################################
# FUNCTIONS ###############################################
###########################################################

# load settings from our YML-like file
# - the format of our YML is more relaxed than that of the original YML (YML does not support comments)
def loadYmlSettings(ymlFile):
    with open(ymlFile, "r", encoding="utf8") as f1:
        data = f1.read()
        data = re.sub(r"#.*", "", data) # remove comments
        data = re.sub(r"\n+", "\n", data) # remove extra linebreaks used for readability
        data = re.split(r"\n(?=\w)", data) # splitting
        dic = {}
        for d in data:
            if ":" in d:
                d = re.sub(r"\s+", " ", d.strip())
                d = re.split(r"^([^:]+) *:", d)[1:]
                key = d[0].strip()
                value = d[1].strip()
                if key == "prioritized_publ":
                    value = d[1].strip()
                    value = re.sub("\s+", "", value).split(",")
                dic[key] = value
    #input(dic)
    return(dic)

# load bibTex Data into a dictionary
def loadBib(bibTexFile):

    bibDic = {}
    recordsNeedFixing = []

    with open(bibTexFile, "r", encoding="utf8") as f1:
        records = f1.read()
        records = re.sub("\n@preamble[^\n]+", "", records)
        records = records.split("\n@") #separate records
        #for all records
        for record in records[1:]:
            completeRecord = "\n@" + record #restore complete record
            #delete line with file direction
            completeRecord = re.sub("\n\s+file = [^\n]+", "", completeRecord)
            #print("----COMPLETERECORD:")
            record = record.strip().split("\n")[:-1]

            rType = record[0].split("{")[0].strip() #rType = kind of file
            #rCiteRaw = citation name
            rCiteRaw = record[0].split("{")[1].strip().replace(",", "")
            print("------RCITERAW:      ",rCiteRaw)
            rCite = rCiteRaw.replace("", "") #delete -
            print("------RCITE:      ",rCite)
            # only valid characters in citeKey:
            if re.search("^[A-Za-z0-9_-]+$", rCite):
                bibDic[rCite] = {}
                bibDic[rCite]["rCite"] = rCite
                bibDic[rCite]["rType"] = rType
                bibDic[rCite]["complete"] = completeRecord


                for r in record[1:]:
                    key = r.split("=")[0].strip()
                    val = r.split("=")[1].strip()
                    val = re.sub("^\{|\},?", "", val)
                    #print("VALUES: ",val)

                    bibDic[rCite][key] = val

                    # fix the path to PDF
                    if key == "file":
                        if ";" in val:
                            #print(val)
                            temp = val.split(";")

                            for t in temp:
                                if ".pdf" in t:
                                    val = t

                            bibDic[rCite][key] = val
            else:
                print(rCiteRaw)
                print(rCite)
                print(completeRecord)
                sys.exit("\n\tPROCESSING STOPPED: INVALID KEY")

        # filter bibDic: remove records that do not have informatin on authr/editor and date
        bibDicFiltered = {}
        #print("------BIBDICITEMS:",bibDic.items())
        for k,v in bibDic.items():
            if "author" in k or "editor" not in k:
                if "date" in k or "year" not in k:
                    bibDicFiltered[k] = v
                else:
                    print(v["complete"])
                    input(k)
            else:
                print(v["complete"])
                input(k)

    if len(bibDicFiltered) > 1:
        print("="*80)
        print("NUMBER OF RECORDS IN BIBLIOGRAPHY         : %d" % len(bibDic))
        print("NUMBER OF RECORDS IN FILTERED BIBLIOGRAPHY: %d" % len(bibDicFiltered))
        print("="*80)
    #print("* * * bibDicFiltered:", bibDicFiltered)
    return(bibDicFiltered)

# generate path from bibtex citation key; for example, if the key is `SavantMuslims2017`,
# the path will be pathToMemex+`/s/sa/SavantMuslims2017/`
def generatePublPath(pathToMemex, bibTexCode):
    temp = bibTexCode.lower()
    directory = os.path.join(pathToMemex, temp[0], temp[:2], bibTexCode)
    return(directory)

# creates a clean copy of PDF; the original will still be in Zotero
# the clean PDF will allow to reduce the sie of the memex folder
def createCleanPDF(pdfFileSRC, pdfFileDST):
    with open(pdfFileSRC, 'rb') as pdf_obj:
        pdf = PyPDF2.PdfFileReader(pdf_obj)
        out = PyPDF2.PdfFileWriter()
        for page in pdf.pages:
            out.addPage(page)
            out.removeLinks()
        with open(pdfFileDST, 'wb') as f:
            out.write(f)

# process a single bibliographical record: 1) create its unique path; 2) save a bib file; 3) save PDF file
def processBibRecord(pathToMemex, bibRecDict):
    tempPath = generatePublPath(pathToMemex, bibRecDict["rCite"])

    print("="*80)
    print("%s :: %s" % (bibRecDict["rCite"], tempPath))
    print("="*80)

    if not os.path.exists(tempPath):
        os.makedirs(tempPath)

    bibFilePath = os.path.join(tempPath, "%s.bib" % bibRecDict["rCite"])
    with open(bibFilePath, "w", encoding="utf8") as f9:
        f9.write(bibRecDict["complete"])

    if "file" in bibRecDict:
        pdfFileSRC = bibRecDict["file"]
        pdfFileDST = os.path.join(tempPath, "%s.pdf" % bibRecDict["rCite"])
        if not os.path.isfile(pdfFileDST): # this is to avoid copying that had been already copied.
            os.rename(pdfFileSRC, pdfFileDST) # simply copying PDFs: 1.5 sec; 1,19 GB
            #createCleanPDF(pdfFileSRC, pdfFileDST) # copying clean PDFs: 27 sec; 1,09 GB
    else:
        print("\trecord has no PDF!")


###########################################################
# OCR-RELATED FUNCTIONS ###################################
###########################################################

# cleans OCRed text
def postprocessOcredPage(ocrText):
    ocrText = re.sub(r"(\w)-\n(\w)", r"\1\2", ocrText)
    ocrText = re.sub(r"(\w)'(\w)", r"\1\2", ocrText)
    #ocrText = re.sub("-", "_", ocrText)
    ocrText = ocrText.lower()
    ocrText = re.split("\W+", ocrText)
    return(ocrText)

# cleans OCRed text for SEARCH
def postprocessOcredPageForSearch(ocrText):
    ocrText = re.sub(r"(\w)-\n(\w)", r"\1\2", ocrText)
    #ocrText = re.sub(r"\s+", "_", ocrText)
    #ocrText = re.sub(r"(\w)\W(\w)", r"\1\2", ocrText)
    ocrText = re.sub(r"\s+", " ", ocrText)
    #ocrText = ocrText.lower()
    #input(ocrText)
    return(ocrText)

# tries to identify language for Tesseract
def identifyLanguage(bibRecDict, fallBackLanguage):
    if "langid" in bibRecDict:
        try:
            language = langKeys[bibRecDict["langid"]]
            message = "\t>> Language has been successfuly identified: %s" % language
        except:
            message = "\t>> Language ID `%s` cannot be understood by Tesseract; fix it and retry\n" % bibRecDict["langid"]
            message += "\t>> For now, trying `%s`..." % fallBackLanguage
            language = fallBackLanguage
    else:
        message = "\t>> No data on the language of the publication"
        message += "\t>> For now, trying `%s`..." % fallBackLanguage
        language = fallBackLanguage
    print(message)
    return(language)

###########################################################
# MAINTRENANCE FUNCTIONS ##################################
###########################################################

# creates a dictionary of citationKey:Path pairs for a relevant type of files
def dicOfRelevantFiles(pathToMemex, extension):
    dic = {}
    for subdir, dirs, files in os.walk(pathToMemex):
        for file in files:
            # process publication tf data
            if file.endswith(extension):
                key = file.replace(extension, "")
                value = os.path.join(subdir, file)
                dic[key] = value
    return(dic)

# creates a list of paths to files of a relevant type
def listOfRelevantFiles(pathToMemex, extension):
    listOfPaths = []
    for subdir, dirs, files in os.walk(pathToMemex):
        for file in files:
            # process publication tf data
            if file.endswith(extension):
                path = os.path.join(subdir, file)
                listOfPaths.append(listOfPaths)
    return(listOfPaths)

def memexStatusUpdates(pathToMemex, fileType):
    # collect stats
    NumberOfPublications = len(listOfRelevantFiles(pathToMemex, ".pdf")) # PDF is the main measuring stick
    NumberOfCountedItems = len(listOfRelevantFiles(pathToMemex, fileType))

    currentTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # check if dictionary exists
    dicFile = os.path.join(pathToMemex, "memex.status")
    if os.path.isfile(dicFile):
        dic = json.load(open(dicFile))
    else:
        dic = {}

    dic[fileType] = {}
    dic[fileType]["files"] = NumberOfCountedItems
    dic[fileType]["pdfs"] = NumberOfPublications
    dic[fileType]["time"] = currentTime

    # save dic
    with open(dicFile, 'w', encoding='utf8') as f9:
        json.dump(dic, f9, sort_keys=True, indent=4, ensure_ascii=False)

    print("="*40)
    print("Memex Stats have been updated for: %s" % fileType)
    print("="*40)

# the function will quickly remove all files with a certain
# extension --- useful when messing around and need to delete
# lots of temporary files

def removeFilesOfType(pathToMemex, fileExtension, silent):
    if fileExtension in [".pdf", ".bib"]:
        sys.exit("files with extension %s must not be deleted in batch!!! Exiting..." % fileExtension)
    else:
        for subdir, dirs, files in os.walk(pathToMemex):
            for file in files:
                # process publication tf data
                if file.endswith(fileExtension):
                    pathToFile = os.path.join(subdir, file)
                    if silent != "silent":
                        print("\tDeleting: %s" % pathToFile)
                    os.remove(pathToFile)

###########################################################
# INTERFACE-RELATED FUNCTIONS #############################
###########################################################

# HTML: generates TOCs for each page; the current page is highlighted with red
def generatePageLinks(pNumList):
    listMod = ["DETAILS"]
    listMod.extend(pNumList)

    toc = []
    for l in listMod:
        toc.append('<a href="%s.html">%s</a>' % (l, l))
    toc = " ".join(toc)

    pageDic = {}
    for l in listMod:
        pageDic[l] = toc.replace('>%s<' % l, ' style="color: red;">%s<' % l)

    return(pageDic)

# HTML: makes BIB more HTML friendly
def prettifyBib(bibText):
    bibText = bibText.replace("{{", "").replace("}}", "")
    bibText = re.sub(r"\n\s+file = [^\n]+", "", bibText)
    bibText = re.sub(r"\n\s+abstract = [^\n]+", "", bibText)
    return(bibText)


###########################################################
# KEYWORD ANALYSIS FUNCTIONS ##############################
###########################################################

def loadMultiLingualStopWords(listOfLanguageCodes):
    print(">> Loading stopwords...")
    stopwords = []
    pathToFiles = settings["stopwords"]
    codes = json.load(open(os.path.join(pathToFiles, "languages.json")))

    for l in listOfLanguageCodes:
        with open(os.path.join(pathToFiles, codes[l]+".txt"), "r", encoding="utf8") as f1:
            lang = f1.read().strip().split("\n")
            stopwords.extend(lang)

    stopwords = list(set(stopwords))
    print("\tStopwords for: ", listOfLanguageCodes)
    print("\tNumber of stopwords: %d" % len(stopwords))
    #print(stopwords)
    return(stopwords)

###########################################################
# VARIABLES ###############################################
###########################################################

settings = loadYmlSettings("settings.yml")
langKeys = loadYmlSettings(settings["language_keys"])
