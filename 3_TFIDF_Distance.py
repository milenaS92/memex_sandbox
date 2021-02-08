# NEW LIBRARIES
import pandas as pd
from sklearn.feature_extraction.text import (CountVectorizer, TfidfTransformer)
from sklearn.metrics.pairwise import cosine_similarity

import os, json, re, sys

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
                    if item1 != item2:
                        dictionaryFilt[item1][item2] = value
            elif lessOrMore == "more":
                if value >= threshold:
                    if item1 != item2:
                        dictionaryFilt[item1][item2] = value
            else:
                sys.exit("`lessOrMore` parameter must be `less` or `more`")

        if dictionaryFilt[item1] == {}:
            dictionaryFilt.pop(item1)
    return(dictionaryFilt)


def tfidfPublications(pathToMemex):
    # PART 1: loading OCR files into a corpus
    ocrFiles = functions.dicOfRelevantFiles(pathToMemex, ".json")
    citeKeys = list(ocrFiles.keys())#[:500]

    print("\taggregating texts into documents...")
    docList   = []
    docIdList = []

    for citeKey in citeKeys:
        docData = json.load(open(ocrFiles[citeKey]))
        # IF YOU ARE ON WINDOWS, THE LINE SHOULD BE:
        # docData = json.load(open(ocrFiles[citeKey], "r", encoding="utf8"))
        
        docId = citeKey
        doc   = " ".join(docData.values())

        # clean doc
        doc = re.sub(r'(\w)-\n(\w)', r'\1\2', doc)
        doc = re.sub('\W+', ' ', doc)
        doc = re.sub('_+', ' ', doc)
        doc = re.sub('\d+', ' ', doc)
        doc = re.sub(' +', ' ', doc)

        # update lists
        docList.append(doc)
        docIdList.append(docId)

    print("\t%d documents generated..." % len(docList))

    # PART 2: calculate tfidf for all loaded publications and distances
    print("\tgenerating tfidf matrix & distances...")
    vectorizer = CountVectorizer(ngram_range=(1,1), min_df=5, max_df=0.5)
    countVectorized = vectorizer.fit_transform(docList)
    tfidfTransformer = TfidfTransformer(smooth_idf=True, use_idf=True)
    vectorized = tfidfTransformer.fit_transform(countVectorized) # generates a sparse matrix
    cosineMatrix = cosine_similarity(vectorized)

    # PART 3: saving TFIDF
    print("\tsaving tfidf data...")
    tfidfTable = pd.DataFrame(vectorized.toarray(), index=docIdList, columns=vectorizer.get_feature_names())
    tfidfTable = tfidfTable.transpose()
    print("\ttfidfTable Shape: ", tfidfTable.shape)
    tfidfTableDic = tfidfTable.to_dict()

    tfidfTableDicFilt = filterTfidfDictionary(tfidfTableDic, 0.05, "more")
    pathToSave = os.path.join(pathToMemex, "results_tfidf.dataJson")
    with open(pathToSave, 'w', encoding='utf8') as f9:
        json.dump(tfidfTableDicFilt, f9, sort_keys=True, indent=4, ensure_ascii=False)

    # PART 3: saving cosine distances
    print("\tsaving cosine distances data...")
    cosineTable = pd.DataFrame(cosineMatrix)
    print("\tcosineTable Shape: ", cosineTable.shape)
    cosineTable.columns = docIdList
    cosineTable.index = docIdList
    cosineTableDic = cosineTable.to_dict()

    tfidfTableDicFilt = filterTfidfDictionary(cosineTableDic, 0.25, "more")
    pathToSave = os.path.join(pathToMemex, "results_cosineDist.dataJson")
    with open(pathToSave, 'w', encoding='utf8') as f9:
        json.dump(tfidfTableDicFilt, f9, sort_keys=True, indent=4, ensure_ascii=False)

tfidfPublications(settings["path_to_memex"])

