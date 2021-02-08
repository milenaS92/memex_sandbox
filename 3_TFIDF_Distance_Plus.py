# NEW LIBRARIES
import pandas as pd
from sklearn.feature_extraction.text import (CountVectorizer, TfidfTransformer)
from sklearn.metrics.pairwise import cosine_similarity

import os, yaml, json, re, sys

# SCRIPT WITH OUR PREVIOUS FUNCTIONS
import functions

###########################################################
# VARIABLES ###############################################
###########################################################

settings = functions.loadYmlSettings("settings.yml")

###########################################################
# MAIN FUNCTIONS ##########################################
###########################################################

def filterTfidfDictionary(dictionary, threshold, lessOrMore):
    dictionaryFilt = {}
    for item1, citeKeyDist in dictionary.items():
        dictionaryFilt[item1] = {}
        for item2, value in citeKeyDist.items():
            if lessOrMore == "less":
                if value <= threshold:
                    if item1.split("__")[0] != item2.split("__")[0]:
                        dictionaryFilt[item1][item2] = value
            elif lessOrMore == "more":
                if value >= threshold:
                    if item1.split("__")[0] != item2.split("__")[0]:
                        dictionaryFilt[item1][item2] = value
            else:
                sys.exit("`lessOrMore` parameter must be `less` or `more`")

        if dictionaryFilt[item1] == {}:
            dictionaryFilt.pop(item1)

    return(dictionaryFilt)

import math
# a function for grouping pages into clusters of y number of pages
# x = number to round up; y = a multiple of the round-up-to number
def roundUp(x, y):
    result = int(math.ceil(x / y)) * y
    return(result)

clusterSize = 5 # 6 pages per page clusters, with 1 page overlap for smoothness (0-5, 5-10, 10-15, 15-20, etc.)
                # clusters also reduce the number of documents 

def tfidfPublications(pathToMemex, PageOrPubl):
    print("\tProcessing: %s" % PageOrPubl)
    # PART 1: loading OCR files into a corpus
    ocrFiles = functions.dicOfRelevantFiles(pathToMemex, ".json")
    citeKeys = list(ocrFiles.keys())#[:500]

    print("\taggregating texts into documents...")
    corpusDic = {}
    for citeKey in citeKeys:
        docData = json.load(open(ocrFiles[citeKey]))
        for page, text in docData.items():
            # text as a document
            if PageOrPubl == "publications":
                if citeKey not in corpusDic:
                    corpusDic[citeKey] = []
                corpusDic[citeKey].append(text)

            # page cluster as a document
            elif PageOrPubl == "pages":
                pageNum = int(page)
                citeKeyNew = "%s__%05d" % (citeKey, roundUp(pageNum, clusterSize))
                if citeKeyNew not in corpusDic:
                    corpusDic[citeKeyNew] = []
                corpusDic[citeKeyNew].append(text)

                # add the last page of cluster N to cluster N+1
                if pageNum % clusterSize == 0:
                    citeKeyNew = "%s__%05d" % (citeKey, roundUp(pageNum+1, clusterSize))
                    if citeKeyNew not in corpusDic:
                        corpusDic[citeKeyNew] = []
                    corpusDic[citeKeyNew].append(text)
            else:
                sys.exit("`PageOrPubl` parameter must be `publications` or `pages`")

    print("\t%d documents (%s) generated..." % (len(corpusDic), PageOrPubl))
    print("\tpreprocessing the corpus...")

    docList   = []
    docIdList = []

    for docId, docText in corpusDic.items():
        if len(docText) > 2: # cluster of two pages mean that we would drop one last page            
            doc = " ".join(docText)
            # clean doc
            doc = re.sub(r'(\w)-\n(\w)', r'\1\2', doc)
            doc = re.sub('\W+', ' ', doc)
            doc = re.sub('_+', ' ', doc)
            doc = re.sub('\d+', ' ', doc)
            doc = re.sub(' +', ' ', doc)
            # we can also drop documents with a small number of words
            # (for example, when there are many illustrations)
            # let's drop clusters that have less than 1,000 words (average for 6 pages ±2500-3000 words)
            if len(doc.split(" ")) > 1000:
                # update lists
                docList.append(doc)
                docIdList.append(docId)

    # PART 3: calculate tfidf for all loaded publications and distances
    print("\tgenerating tfidf matrix & distances...")
    stopWords = functions.loadMultiLingualStopWords(["eng", "deu", "fre", "spa"])
    vectorizer = CountVectorizer(ngram_range=(1,1), min_df=5, max_df=0.5, stop_words = stopWords)
    countVectorized = vectorizer.fit_transform(docList)
    tfidfTransformer = TfidfTransformer(smooth_idf=True, use_idf=True)
    vectorized = tfidfTransformer.fit_transform(countVectorized) # generates a sparse matrix
    cosineMatrix = cosine_similarity(vectorized)

    # PART 4: saving TFIDF --- only for publications!
    if PageOrPubl == "publications":
        print("\tsaving tfidf data...")
        tfidfTable = pd.DataFrame(vectorized.toarray(), index=docIdList, columns=vectorizer.get_feature_names())
        tfidfTable = tfidfTable.transpose()
        print("\ttfidfTable Shape: ", tfidfTable.shape)
        tfidfTableDic = tfidfTable.to_dict()

        tfidfTableDicFilt = filterTfidfDictionary(tfidfTableDic, 0.05, "more")
        pathToSave = os.path.join(pathToMemex, "results_tfidf_%s.dataJson" % PageOrPubl)
        with open(pathToSave, 'w', encoding='utf8') as f9:
            json.dump(tfidfTableDicFilt, f9, sort_keys=True, indent=4, ensure_ascii=False)

    # PART 4: saving cosine distances --- for both publications and page clusters
    print("\tsaving cosine distances data...")
    cosineTable = pd.DataFrame(cosineMatrix)
    print("\tcosineTable Shape: ", cosineTable.shape)
    cosineTable.columns = docIdList
    cosineTable.index = docIdList
    cosineTableDic = cosineTable.to_dict()

    tfidfTableDicFilt = filterTfidfDictionary(cosineTableDic, 0.25, "more")
    pathToSave = os.path.join(pathToMemex, "results_cosineDist_%s.dataJson" % PageOrPubl)
    with open(pathToSave, 'w', encoding='utf8') as f9:
        json.dump(tfidfTableDicFilt, f9, sort_keys=True, indent=4, ensure_ascii=False)

tfidfPublications(settings["path_to_memex"], "publications")
tfidfPublications(settings["path_to_memex"], "pages")

