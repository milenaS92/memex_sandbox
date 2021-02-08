import os, json
import unicodedata

# SCRIPT WITH OUR PREVIOUS FUNCTIONS
import functions

###########################################################
# VARIABLES ###############################################
###########################################################

settings = functions.loadYmlSettings("settings.yml")

###########################################################
# MINI TEMPLATES ##########################################
###########################################################

generalTemplate = """
<button class="collapsible">@ELEMENTHEADER@</button>
<div class="content">

@ELEMENTCONTENT@

</div>
"""

searchesTemplate = """
<button class="collapsible">SAVED SEARCHES</button>
<div class="content">
<table id="" class="display" width="100%">
<thead>
    <tr>
        <th><i>link</i></th>
        <th>search string</th>
        <th># of publications with matches</th>
        <th>time stamp</th>
    </tr>
</thead>

<tbody>
@TABLECONTENTS@
</tbody>

</table>
</div>
"""

publicationsTemplate = """
<button class="collapsible">PUBLICATIONS INCLUDED INTO MEMEX</button>

<table id="" class="display" width="100%">
<thead>
    <tr>
        <th><i>link</i></th>
        <th>citeKey, author, date, title</th>
    </tr>
</thead>

<tbody>
@TABLECONTENTS@
</tbody>

</table>
"""

###########################################################
# MINI FUNCTIONS ##########################################
###########################################################

# generate search pages and TOC
def formatSearches(pathToMemex):
    with open(settings["template_search"], "r", encoding="utf8") as f1:
        indexTmpl = f1.read()
    dof = functions.dicOfRelevantFiles(pathToMemex, ".searchResults")
    # format individual search pages
    toc = []
    for file, pathToFile in dof.items():
        searchResults = []
        data = json.load(open(pathToFile))
        # collect toc
        template = "<tr> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td></tr>"

        # variables
        linkToSearch = os.path.join("searches", file+".html")
        pathToPage = '<a href="%s"><i>read</i></a>' % linkToSearch
        searchString = '<div class="searchString">%s</div>' % data.pop("searchString")
        timeStamp = data.pop("timestamp")
        tocItem = template % (pathToPage, searchString, len(data), timeStamp)
        toc.append(tocItem)

        # generate the results page
        keys = sorted(data.keys(), reverse=True)
        for k in keys:
            searchResSingle = []
            results = data[k]
            temp = k.split("::::")
            header = "%s (pages with results: %d)" % (temp[1], int(temp[0]))
            #print(header)
            for page, excerpt in results.items():
                #print(excerpt["result"])
                pdfPage = int(page)
                linkToPage = '<a href="../%s"><i>go to the original page...</i></a>' % excerpt["pathToPage"]
                searchResSingle.append("<li><b><hr>(pdfPage: %d)</b><hr> %s <hr> %s </li>" % (pdfPage, excerpt["result"], linkToPage))
            searchResSingle = "<ul>\n%s\n</ul>" % "\n".join(searchResSingle)
            searchResSingle = generalTemplate.replace("@ELEMENTHEADER@", header).replace("@ELEMENTCONTENT@", searchResSingle)
            searchResults.append(searchResSingle)

        searchResults = "<h2>SEARCH RESULTS FOR: <i>%s</i></h2>\n\n" % searchString + "\n\n".join(searchResults)
        with open(pathToFile.replace(".searchResults", ".html"), "w", encoding="utf8") as f9:
            f9.write(indexTmpl.replace("@MAINCONTENT@", searchResults))
        #os.remove(pathToFile)

    #input("\n".join(toc))
    toc = searchesTemplate.replace("@TABLECONTENTS@", "\n".join(toc))
    return(toc)


def formatPublList(pathToMemex):
    ocrFiles = functions.dicOfRelevantFiles(pathToMemex, settings["ocr_results"])
    bibFiles = functions.dicOfRelevantFiles(pathToMemex, ".bib")

    contentsList = []

    for key, value in ocrFiles.items():
        if key in bibFiles:
            bibRecord = functions.loadBib(bibFiles[key])
            bibRecord = bibRecord[key]

            relativePath = functions.generatePublPath(pathToMemex, key).replace(pathToMemex, "")

            authorOrEditor = "[No data]"
            if "editor" in bibRecord:
                authorOrEditor = bibRecord["editor"]
            if "author" in bibRecord:
                authorOrEditor = bibRecord["author"]
            if "date" in bibRecord:
                date = bibRecord["date"][:4]
            else:
                date = 0000
            title = bibRecord["title"]

            # formatting template
            citeKey = '<div class="ID">[%s]</div>' % key
            publication = '%s (%s) <i>%s</i>' % (authorOrEditor, date, title)
            search = unicodedata.normalize('NFKD', publication).encode('ascii','ignore')
            publication += " <div class='hidden'>%s</div>" % search
            link = '<a href="%s/pages/DETAILS.html"><i>read</i></a>' % relativePath

            singleItemTemplate = '<tr><td>%s</td><td>%s %s</td></tr>' % (link, citeKey, publication)
            recordToAdd = singleItemTemplate.replace("{", "").replace("}", "")

            contentsList.append(recordToAdd)

    contents = "\n".join(sorted(contentsList))
    final = publicationsTemplate.replace("@TABLECONTENTS@", contents)
    return(final)

###########################################################
# MAIN FUNCTIONS ##########################################
###########################################################

# generate index pages: index with stats; search results pages
def generateIngexInterface(pathToMemex):
    print("\tgenerating main index page...")
    # generate the main index page with stats
    with open(settings["template_index"], "r", encoding="utf8") as f1:
        indexTmpl = f1.read()
    with open(settings["content_index"], "r", encoding="utf8") as f1:
        indexCont = f1.read()

    # - PREAMBLE
    mainElement   = indexCont + "\n\n"
    # - SEARCHES
    mainElement += formatSearches(pathToMemex)
    # - PUBLICATION LIST
    mainElement += formatPublList(pathToMemex)

    # - FINALIZING INDEX PAGE
    indexPage     = indexTmpl
    indexPage     = indexPage.replace("@MAINCONTENT@", mainElement)

    pathToIndex   = os.path.join(pathToMemex, "index.html")
    with open(pathToIndex, "w", encoding="utf8") as f9:
        f9.write(indexPage)

###########################################################
# FUNCTIONS TESTING #######################################
###########################################################

generateIngexInterface(settings["path_to_memex"])
