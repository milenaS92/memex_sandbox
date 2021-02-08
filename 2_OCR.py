# NEW LIBRARIES
import pdf2image    # extracts images from PDF
import pytesseract  # interacts with Tesseract, which extracts text from images

import os, yaml, json, random

# SCRIPT WITH OUR PREVIOUS FUNCTIONS
import functions

###########################################################
# VARIABLES ###############################################
###########################################################

settings = functions.loadYmlSettings("settings.yml")

###########################################################
# MAIN FUNCTIONS ##########################################
###########################################################

# function OCR a PDF, saving each page as an image and
# saving OCR results into a JSON file
def ocrPublication(citationKey, language, pageLimit):
    # generate and create necessary paths
    publPath = functions.generatePublPath(settings["path_to_memex"], citationKey)
    pdfFile  = os.path.join(publPath, citationKey + ".pdf")
    jsonFile = os.path.join(publPath, citationKey + ".json") # OCR results will be saved here
    saveToPath = os.path.join(publPath, "pages") # we will save processed images here

    # first we need to check whether this publication has been already processed
    if not os.path.isfile(jsonFile):
        # let's make sure that saveToPath also exists
        if not os.path.exists(saveToPath):
            os.makedirs(saveToPath)

        # start process images and extract text
        print("\t>>> OCR-ing: %s" % citationKey)

        textResults = {}
        images = pdf2image.convert_from_path(pdfFile)
        pageTotal = len(images)
        pageCount = 1
        if pageTotal <= int(pageLimit):
            for image in images:
                text = pytesseract.image_to_string(image, lang=language)
                textResults["%04d" % pageCount] = text

                image = image.convert('1') # binarizes image, reducing its size
                finalPath = os.path.join(saveToPath, "%04d.png" % pageCount)
                image.save(finalPath, optimize=True, quality=10)

                print("\t\t%04d/%04d pages" % (pageCount, pageTotal))
                pageCount += 1

            with open(jsonFile, 'w', encoding='utf8') as f9:
                json.dump(textResults, f9, sort_keys=True, indent=4, ensure_ascii=False)
        else:
            print("\t%d: the length of the publication exceeds current limit (%d)" % (pageTotal, pageLimit))
            print("\tIncrease `page_limit` in settings to process this publication.")

    else: # in case JSON file already exists
        print("\t>>> %s has already been OCR-ed..." % citationKey)

###########################################################
# FUNCTIONS TESTING #######################################
###########################################################

#ocrPublication("AbdurasulovMaking2020", "eng")

###########################################################
# PROCESS ALL RECORDS: APPROACH 1 #########################
###########################################################

# Why this way? Our computers are now quite powerful; they
# often have multiple cores and we can take advantage of this;
# if we process our data in the manner coded below --- we shuffle
# our publications and process them in random order --- we can
# run multiple instances fo the same script and data will
# be produced in parallel. You can run as many instances as
# your machine allows (you need to check how many cores
# your machine has). Even running two scripts will cut
# processing time roughly in half.

# - this approach allows one to prioritize specific publications
#   by maintaining a separate bibliography with a smaller number
#   of neeeded publications.

def processAllRecords(bibDataFile):
    bibData = functions.loadBib(bibDataFile)
    keys = list(bibData.keys())
    random.shuffle(keys)

    for key in keys:
        bibRecord = bibData[key]
        functions.processBibRecord(settings["path_to_memex"], bibRecord)
        language = functions.identifyLanguage(bibRecord["rCite"], "eng")
        ocrPublication(bibRecord["rCite"], language, int(settings["page_limit"]))

    functions.memexStatusUpdates(settings["path_to_memex"], ".pdf")
    functions.memexStatusUpdates(settings["path_to_memex"], ".bib")
    functions.memexStatusUpdates(settings["path_to_memex"], ".png")
    functions.memexStatusUpdates(settings["path_to_memex"], ".json")

#processAllRecords(settings["bib_all"])

###########################################################

#processAllRecords(settings["bib_all"])
#print("Done!")

###########################################################
# PROCESS ALL RECORDS: APPROACH 2 #########################
###########################################################

# we can use yet another way to OCR our files; now that we have
# generated the structure (we copied PDFs and created individual .bib
# files), we do not need to use the main bibliography file.
# Instead, we can just use what we already have in our future
# memex. This approach has additional advantange in a way
# that two different memexes can be merged together and processed
# without relying on the main bibliography file, but rather
# on the existing structure of memex

def processAllRecordsSTR(pathToMemex):
    files = functions.dicOfRelevantFiles(pathToMemex, ".bib")
    citeKeys = list(files.keys())
    random.shuffle(citeKeys)

    for citeKey in citeKeys:
        print(citeKey)
        bibData = functions.loadBib(files[citeKey])
        print("++++++BibData:::",bibData)
        if "pagetotal" in bibData:
            pageTotal = int(bibData["pagetotal"])
            if pageTotal <= int(settings["page_limit"]):
                language = functions.identifyLanguage(bibData[citeKey], "eng")
                ocrPublication(citeKey, language, settings["page_limit"])
        else:
            language = functions.identifyLanguage(bibData[citeKey], "eng")
            ocrPublication(citeKey, language, settings["page_limit"])

    functions.memexStatusUpdates(settings["path_to_memex"], ".pdf")
    functions.memexStatusUpdates(settings["path_to_memex"], ".bib")
    functions.memexStatusUpdates(settings["path_to_memex"], ".png")
    functions.memexStatusUpdates(settings["path_to_memex"], ".json")


processAllRecordsSTR(settings["path_to_memex"])
print("Done!")
