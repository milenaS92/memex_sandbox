###############################################################################
# YAML LIBRARY WORKAROUND #####################################################
############################################################################### 

"""
In some cases it might be difficult to install the `yaml` library that helps
processing yaml files. Luckily, yaml files are quite easy to parse and we can
use the following function to do that. Important: this function is very simple
and will work only with yaml files in which key-value pairs occupy single lines
"""

def loadYaml(file):
    dic = {}
    with open(file, "r", encoding="utf8") as f1:
        data = f1.read().split("\n")

        for d in data:
            d = d.split(":")
            dic[d[0].strip()] = d[1].strip()

    return(dic)

