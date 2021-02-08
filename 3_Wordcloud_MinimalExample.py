###########################################################
# MAIN FUNCTIONS ##########################################
###########################################################

from wordcloud import WordCloud
import matplotlib.pyplot as plt

AndrewsTree2013 = {
        "academic": 0.05813626462255791, "acyclic": 0.06250123247317078,
        "andrews": 0.12638860902474044,
        "artificial": 0.07179606130684399,
        "coincidental": 0.107968929904822,
        "collatex": 0.05992322690922588,
        "collation": 0.06303029408091644,
        "computational": 0.05722784996783764,
        "computing": 0.10647437138201694,
        "conflation": 0.06207493202469115,
        "copied": 0.11909333470623461,
        "deletion": 0.1139260485820703,
        "deum": 0.08733065096290674,
        "dsh": 0.12062758085160386,
        "empirical": 0.06256016440693514,
        "exemplar": 0.06413026390502427,
        "february": 0.06598308140156786,
        "fig": 0.06658631708313895,
        "figure": 0.057484475246214396,
        "finnish": 0.06718916017623287,
        "genealogical": 0.14922848147612744,
        "grammatical": 0.06639003369358097,
        "graph": 0.3064885690820798,
        "heikkila": 0.06250123247317078,
        "howe": 0.0502983742283863,
        "lachmannian": 0.05357248497700353,
        "legend": 0.05576734763473662,
        "lexical": 0.07504108167413616,
        "library": 0.052654345617120235,
        "linguistic": 0.08295373338961148,
        "literary": 0.05453901405048022,
        "macé": 0.09416507085735495,
        "manuscript": 0.056407679242811995,
        "medieval": 0.0722276960100237,
        "methods": 0.06617794961055612,
        "model": 0.06712481163842804,
        "oup": 0.11328056728336285,
        "phylogenetic": 0.0771729868291211,
        "quae": 0.06207493202469115,
        "readings": 0.14004936139939653,
        "relationships": 0.05294605101492676,
        "reverted": 0.08384604576952619,
        "roos": 0.057864729221843304,
        "root": 0.050044699046501814,
        "sermo": 0.05136276592219361,
        "spelling": 0.10943421974916011,
        "spencer": 0.058047262455825824,
        "stemma": 0.42250289612460745,
        "stemmata": 0.0813887983497219,
        "stemmatic": 0.09093028877718234,
        "stemmatology": 0.11984645381845176,
        "table": 0.0650730361130049,
        "traditions": 0.06135920913100084,
        "transmission": 0.07196157976331963,
        "transposition": 0.09182278547380966,
        "tree": 0.06790095059625004,
        "user": 0.08246083727188196,
        "variant": 0.2562367460915465,
        "variants": 0.1432698250058143,
        "variation": 0.2935924450487041,
        "vb": 0.11035543471056206,
        "vertices": 0.050436368099886865,
        "vienna": 0.07506704856975273,
        "witness": 0.11471933221048437,
        "witnesses": 0.09101116903971758
    }

savePath = "AndrewsTree2013"

def createWordCloud(savePath, tfIdfDic):
    wc = WordCloud(width=1000, height=600, background_color="white", random_state=2, relative_scaling=0.5, colormap="gray") 

    wc.generate_from_frequencies(tfIdfDic)
    # plotting
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    #plt.show() # this line will show the plot
    plt.savefig(savePath, dpi=200, bbox_inches='tight')

createWordCloud(savePath, AndrewsTree2013)