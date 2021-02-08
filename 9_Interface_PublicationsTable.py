import os, json, unicodedata

# SCRIPT WITH OUR PREVIOUS FUNCTIONS
import functions

###########################################################
# VARIABLES ###############################################
###########################################################

settings = functions.loadYmlSettings("settings.yml")

###########################################################
# MINI TEMPLATES ##########################################
###########################################################

connectionsTemplate = """
<button class="collapsible">Similar Texts (<i>tf-idf</i> + cosine similarity)</button>

  <div class="content">
  <ul>
    <li>
    <b>Sim*</b>: <i>cosine similarity</i>; 1 is a complete match, 0 — nothing similar;
    cosine similarity is calculated using <i>tf-idf</i> values of top keywords.</li>
  </ul>
  </div>


<table id="publications" class="mainList">

<thead>
    <tr>
        <th>link</th>
        <th>Sim*</th>
        <th>Author(s), Year, Title, Pages</th>
    </tr>
</thead>

<tbody>
@CONNECTEDTEXTSTEMP@
</tbody>

</table>

"""

ocrTemplate = """
<button class="collapsible">OCREDTEXT</button>
<div class="content">
  <div class="bib">
  @OCREDCONTENTTEMP@
  </div>
</div>
"""

generalTemplate = """
<button class="collapsible">@ELEMENTHEADER@</button>
<div class="content">
@ELEMENTCONTENT@
</div>
"""

###########################################################
# MINI FUNCTIONS ##########################################
###########################################################

import math
# a function for grouping pages into clusters of y number of pages
# x = number to round up; y = a multiple of the round-up-to number
def roundUp(x, y):
    result = int(math.ceil(x / y)) * y
    return(result)

# formats individual references to publications
def generateDoclLink(bibTexCode, pageVal, distance):
    pathToPubl = functions.generatePublPath(settings["path_to_memex"], bibTexCode)
    bib = functions.loadBib(os.path.join(pathToPubl, "%s.bib" % bibTexCode))
    bib = bib[bibTexCode]

    author = "N.d."
    if "editor" in bib:
        author = bib["editor"]
    if "author" in bib:
        author = bib["author"]

    reference = "%s (%s). <i>%s</i>" % (author, bib["date"][:4], bib["title"])
    search = unicodedata.normalize('NFKD', reference).encode('ascii','ignore')
    search = " <div class='hidden'>%s</div>" % search

    if pageVal == 0: # link to the start of the publication
        htmlLink = os.path.join(pathToPubl.replace(settings["path_to_memex"], "../../../../"), "pages", "DETAILS.html")
        htmlLink = "<a href='%s'><i>read</i></a>" % (htmlLink)
        page = ""
        startPage = 0
    else:
        startPage = pageVal - 5
        endPage   = pageVal
        if startPage == 0:
            startPage += 1
        htmlLink = os.path.join(pathToPubl.replace(settings["path_to_memex"], "../../../../"), "pages", "%04d.html" % startPage)
        htmlLink = "<a href='%s'><i>read</i></a>" % (htmlLink)
        page = ", pdfPp. %d-%d</i></a>" % (startPage, endPage)

    publicationInfo = reference + page + search
    publicationInfo = publicationInfo.replace("{", "").replace("}", "")
    singleItemTemplate = '<tr><td>%s</td><td>%f</td><td data-order="%s%05d">%s</td></tr>' % (htmlLink, distance, bibTexCode, startPage, publicationInfo)

    return(singleItemTemplate)

def generateReferenceSimple(bibTexCode):
    pathToPubl = functions.generatePublPath(settings["path_to_memex"], bibTexCode)
    bib = functions.loadBib(os.path.join(pathToPubl, "%s.bib" % bibTexCode))
    bib = bib[bibTexCode]

    author = "N.d."
    if "editor" in bib:
        author = bib["editor"]
    if "author" in bib:
        author = bib["author"]

    reference = "%s (%s). <i>%s</i>" % (author, bib["date"][:4], bib["title"])
    reference = reference.replace("{", "").replace("}", "")
    return(reference)

# convert json dictionary of connections into HTML format
def formatDistConnections(pathToMemex, distanceFile):
    print("Formatting distances data from `%s`..." % distanceFile)
    distanceFile = os.path.join(pathToMemex, distanceFile)
    distanceDict = json.load(open(distanceFile))

    formattedHTML = {}

    for doc1, doc1Dic in distanceDict.items():
        formattedHTML[doc1] = []
        for doc2, distance in doc1Dic.items():
            doc2 = doc2.split("_")
            if len(doc2) == 1:
                tempVar = generateDoclLink(doc2[0], 0, distance)
            else:
                tempVar = generateDoclLink(doc2[0], int(doc2[1]), distance)

            formattedHTML[doc1].append(tempVar)
            #input(formattedHTML)
    print("\tdone!")
    return(formattedHTML)

###########################################################
# MAIN FUNCTIONS ##########################################
###########################################################

publConnData = formatDistConnections(settings["path_to_memex"], settings["publ_cosDist"])
pageConnData = formatDistConnections(settings["path_to_memex"], settings["page_cosDist"])

# generate interface for the publication and pages
def generatePublicationInterface(citeKey, pathToBibFile):
    print("="*80)
    print(citeKey)

    jsonFile = pathToBibFile.replace(".bib", ".json")
    with open(jsonFile) as jsonData:
        ocred = json.load(jsonData)
        pNums = ocred.keys()
        pageDic = functions.generatePageLinks(pNums)

        # load page template
        with open(settings["template_page"], "r", encoding="utf8") as ft:
            template = ft.read()

        # load individual bib record
        bibFile = pathToBibFile
        bibDic = functions.loadBib(bibFile)
        bibForHTML = functions.prettifyBib(bibDic[citeKey]["complete"])

        orderedPages = list(pageDic.keys())

        for o in range(0, len(orderedPages)):
            #print(o)
            k = orderedPages[o]
            #input(k)
            v = pageDic[orderedPages[o]]

            pageTemp = template
            pageTemp = pageTemp.replace("@PAGELINKS@", v)
            pageTemp = pageTemp.replace("@PATHTOFILE@", "")
            pageTemp = pageTemp.replace("@CITATIONKEY@", citeKey)

            emptyResults = '<tr><td><i>%s</i></td><td><i>%s</i></td><td><i>%s</i></td></tr>'

            if k != "DETAILS":
                mainElement = '<img src="@PAGEFILE@" width="100%" alt="">'.replace("@PAGEFILE@", "%s.png" % k)

                pageKey = citeKey+"_%05d" % roundUp(int(k), 5)
                #print(pageKey)
                if pageKey in pageConnData:
                    formattedResults = "\n".join(pageConnData[pageKey])
                    #input(formattedResults)
                else:
                    formattedResults = emptyResults % ("no data", "no data", "no data")

                mainElement += connectionsTemplate.replace("@CONNECTEDTEXTSTEMP@", formattedResults)
                mainElement += ocrTemplate.replace("@OCREDCONTENTTEMP@", ocred[k].replace("\n", "<br>"))
                pageTemp = pageTemp.replace("@MAINELEMENT@", mainElement)
            else:
                reference = generateReferenceSimple(citeKey)
                mainElement = "<h3>%s</h3>\n\n" % reference

                bibElement = '<div class="bib">%s</div>' % bibForHTML.replace("\n", "<br> ")
                bibElement = generalTemplate.replace("@ELEMENTCONTENT@", bibElement)
                bibElement = bibElement.replace("@ELEMENTHEADER@", "BibTeX Bibliographical Record")
                mainElement += bibElement + "\n\n"

                wordCloud = '\n<img src="../' + citeKey + '_wCloud.jpg" width="100%" alt="wordcloud">'
                wordCloud = generalTemplate.replace("@ELEMENTCONTENT@", wordCloud)
                wordCloud = wordCloud.replace("@ELEMENTHEADER@", "WordCloud of Keywords (<i>tf-idf</i>)")
                mainElement += wordCloud + "\n\n"

                if citeKey in publConnData:
                    formattedResults = "\n".join(publConnData[citeKey])
                    #input(formattedResults)
                else:
                    formattedResults = emptyResults % ("no data", "no data", "no data")

                mainElement += connectionsTemplate.replace("@CONNECTEDTEXTSTEMP@", formattedResults)


                pageTemp = pageTemp.replace("@MAINELEMENT@", mainElement)

            # @NEXTPAGEHTML@ and @PREVIOUSPAGEHTML@
            if k == "DETAILS":
                nextPage = "0001.html"
                prevPage = ""
            elif k == "0001":
                nextPage = "0002.html"
                prevPage = "DETAILS.html"
            elif o == len(orderedPages)-1:
                nextPage = ""
                prevPage = orderedPages[o-1] + ".html"
            else:
                nextPage = orderedPages[o+1] + ".html"
                prevPage = orderedPages[o-1] + ".html"

            pageTemp = pageTemp.replace("@NEXTPAGEHTML@", nextPage)
            pageTemp = pageTemp.replace("@PREVIOUSPAGEHTML@", prevPage)

            pagePath = os.path.join(pathToBibFile.replace(citeKey+".bib", ""), "pages", "%s.html" % k)
            with open(pagePath, "w", encoding="utf8") as f9:
                f9.write(pageTemp)

###########################################################
# FUNCTIONS TESTING #######################################
###########################################################

functions.memexStatusUpdates(settings["path_to_memex"], ".html")
def processAllRecords(pathToMemex):
    files = functions.dicOfRelevantFiles(pathToMemex, ".bib")
    for citeKey, pathToBibFile in files.items():
        if os.path.exists(pathToBibFile.replace(".bib", ".json")):
            generatePublicationInterface(citeKey, pathToBibFile)

processAllRecords(settings["path_to_memex"])
exec(open("9_Interface_IndexPage.py").read())
