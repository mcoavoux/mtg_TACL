import subprocess
import argparse
from collections import defaultdict
import os
import eval_morpho
import sys


def unix(command) :
    return  subprocess.check_output([command], shell=True)

def dirlist(folder) :
    for d in os.listdir(folder) :
        path = os.path.join(folder, d)
        if os.path.isdir(path) :
            yield path

def filelist(folder) :
    for d in os.listdir(folder) :
        path = os.path.join(folder, d)
        if os.path.isfile(path) :
            yield path

def get_discodop_eval_info(filename) :
    
    lines = open(filename).readlines()[-12:]
    if len(lines) > 0 :
        assert("_________ Summary _________" in lines[0])
        res = {}
        for line in lines[1:] :
            key = line.split(":")[0]
            val = line.split(":")[1].split()[-1]
            res[key] = float(val)
        return res
    return {"labeled f-measure" : 0}

def get_evalpl_info(filename) :
    lines = open(filename, "r", encoding="utf8").readlines()[:3]
    nums = [ line.split()[-2] for line in lines ]
    return {"LAS" : nums[0], "UAS" : nums[1], "label" : nums[2]}

def do_model(datadir, best):
    dic = [defaultdict(lambda: defaultdict(float)), defaultdict(lambda: defaultdict(float)), defaultdict(str)]
    
    if best == None :
        return dic
    
    folder, model_type, language, model, iteration = best.split("/")
    iteration = iteration.split("_")[-1]
    
    ## need to get
    ## for dev / test :
    ##      const eval  /  disc const eval
    ##      dep eval
    ##      morph eval tagging + morphology features
    
    evalpunct = language == "ftb"
    if evalpunct:
        cevalkey = "eval_sp"
        devalkey = "depeval"
    else :
        cevalkey = "eval_pr"
        devalkey = "depeval_nopunct"
    
    
    
    prefix = os.path.join(folder, model_type, language, model)
    
    for i,corpus in enumerate(["dev", "test"]) :
        dic[i]["const"] = get_discodop_eval_info(os.path.join(prefix, "{}_{}_b1_{}".format(cevalkey, corpus, iteration)))
        dic[i]["discontinuous const"] = get_discodop_eval_info(os.path.join(prefix, "disc{}_{}_b1_{}".format(cevalkey, corpus, iteration)))
        dic[i]["morph"] = eval_morpho.main(os.path.join(datadir, language, "{}.conll".format(corpus)),
                                           os.path.join(prefix, "pred_{}b1{}.discbracket.conll".format(corpus, iteration)))
        dic[i]["dep"] = get_evalpl_info(os.path.join(prefix, "{}_{}_b1_{}".format(devalkey, corpus, iteration)))
    
    dic[2]["model ID"] = model+"_"+iteration
    dic[2]["model type"] = model_type
    dic[2]["lang"] = language
    
    return dic
    
    
    



def do_models(datadir, lang) :
    
    best = None
    bestf = 0
    
    language = lang.split("/")[-1]
    #print("language =", language)
    evalpunct = True if language == "ftb" else False
    
    if evalpunct:
        cevalkey = "eval_sp_dev"
    else :
        cevalkey = "eval_pr_dev"
    
    ## Find best model
    
    #print()
    #print(lang)
    #print(list(dirlist(lang)))
    #print()
    
    for model in dirlist(lang) :
        filenames = []
        for filename in sorted(os.listdir(model)) :
            path = os.path.join(model, filename)
            if filename.startswith(cevalkey) :
                filenames.append(path)
        
        for path in sorted(filenames, key = lambda x : int(x.split("it")[-1])) :
            evalinfo = get_discodop_eval_info(path)
            fscore = evalinfo["labeled f-measure"]
            
            if fscore > bestf :
                bestf = fscore
                best = path
    
    print(bestf, best)
    
    return do_model(datadir, best)




def get_all_results(datadir, expedir) :
    
    results = {}
    
    for model_type in dirlist(expedir) :
        #print(model_type)
        for lang in dirlist(model_type) :
            #print(lang)
            results[lang] = do_models(datadir, lang)
    return results

def generate_const_results(results, mapping, write=sys.stderr.write) :
    
    d = defaultdict(lambda:defaultdict(lambda:[0,0]))
    
    for TYPE, TYPENAME in enumerate(["DEV", "TEST"]):
    
        for lang in results :
            
            const_dev_results = results[lang][TYPE]["const"]
            dconst_dev_results = results[lang][TYPE]["discontinuous const"]
            
            model_type = results[lang][2]["model type"]
            language = results[lang][2]["lang"]
            
            d[model_type][language] = const_dev_results["labeled f-measure"],  dconst_dev_results["labeled f-measure"]
        
        write("---------------{}----------------------\n".format(TYPENAME))
        write("                                          \n")
        #write("\\begin{tabular}{ll cc cc cc cc}\n")
        write("\\begin{tabular}{lll cc cc cc}\n")
        write("    \\toprule\n")
        #write("    &&\\multicolumn{2}{c}{English} & \\multicolumn{2}{c}{German (Tiger)} & \\multicolumn{2}{c}{German (Negra)} & \\multicolumn{2}{c}{French} \\\\\n")
        write("    &&&\\multicolumn{2}{c}{English} & \\multicolumn{2}{c}{German (Tiger)} & \\multicolumn{2}{c}{German (Negra)} \\\\\n")
        #write("    Transition System & Features  & F & Disc. F & F & Disc. F & F & Disc. F & F & Disc. F \\\\\n")
        write("    Transition System & Features & Oracle  & F & Disc. F & F & Disc. F & F & Disc. F \\\\\n")
        write("    \\midrule\n")
        
        list_models = ["gap_unlex_uncat",
                       "gap_unlex",
                       "gap_lex_uncat",
                       "gap_lex",
                       "usr6_unlex_uncat",
                       "usr6_unlex",
                       "merge0_unlex_uncat",
                       "merge0_unlex",
                       "merge4_unlex_uncat",
                       "merge4_unlex",
                       "merge2_unlex_uncat",
                       "merge2_unlex",
                       "merge2_lex_uncat",
                       "merge2_lex"]
            
        for model_type in list_models:
        #for model_type in ["gap_lex", "gap_unlex", "merge0_unlex", "merge1_unlex", "merge2_lex", "merge2_unlex", "merge3_lex", "merge3_unlex"] :
            mod = mapping[model_type]
            res_by_lang = []
            #for language in ["dptb", "tiger_spmrl", "negra", "ftb"] :
            for language in ["dptb", "tiger_spmrl", "negra"] :
                res_by_lang.extend(list(d[model_type][language]))
            #print(res_by_lang)
            #print(" & ".join([str(round(x, 2)) for x in res_by_lang]))
            write("    {} & {} \\\\\n".format(mod, " & ".join([str(round(x, 1)) for x in res_by_lang])))
        
        write("    \\bottomrule\n")
        write("\\end{tabular}\n")


def generate_morph_results(results, mapping, write=sys.stderr.write) :
    
    d = defaultdict(lambda:defaultdict(str))
    
    for lang in results :
        
        model_type = results[lang][2]["model type"]
        
        if model_type == "merge0_unlex" :
            language = results[lang][2]["lang"]
            
            morph_results = results[lang][0]["morph"]
            
            d[language] = morph_results
    
    write("---------------DEV----------------------\n")
    
    write("\\begin{tabular}{cccc}\n")
    write("    \\toprule\n")
    write("    Attribute & Acc. & F1 & Cov. \\\\\n")
    
    at_map = {"s": "subcat", "t":"tense", "n":"number", "m":"mood", "component": "mwe", "mwehead":"mwe-head", "p":"person", "g": "gender"}
    
    for language in sorted(d) :
        pos = round(d[language]["fpos"] * 100, 2)
        c_match = round(d[language]["complete_match"] * 100, 2)
        write("    \\midrule\n")
        write("    \\multicolumn{4}{c}{"+mapping[language]+"}\\\\ \n")
        write("    \\midrule\n")
        write("    POS            & {} & {} & {} \\\\\n".format(pos, "-", 100))
        if language not in {"dptb", "negra"} :
            write("    Complete match & {} & {} & {} \\\\\n".format(c_match, "-", 100))
            for attribute in sorted(d[language]["list"], key = lambda x : ("component" in x or "mwe" in x, x)) :
                full_at = at_map[attribute] if attribute in at_map else attribute
                acc = round(d[language]["morph {} accuracy".format(attribute)] * 100, 2)
                f1  = round(d[language]["morph {} f-measure".format(attribute)] * 100, 2)
                cov = round(d[language]["morph {} coverage".format(attribute)] * 100, 2)
                write("    {} & {} & {} & {} \\\\\n".format(full_at, acc, f1, cov))
        
        
    write("    \\bottomrule\n")
    write("\\end{tabular}\n")





if __name__ == "__main__" :
    
    usage="""
        Aggregates a bunch of evaluation metrics and output them in an
        easily readable format.
    """
    
    parser = argparse.ArgumentParser(description = usage, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("datadir", type = str, help="root of data dir")
    parser.add_argument("expedir", type = str, help="root of expe dir")
    
    args = parser.parse_args()
    
    oracles = ["head-driven", "eager"]

    features = ["{base}", "{+lex}", "{+nt}", "{+nt+lex}"]
    
    mapping={"dptb" : "English", "ftb" : "French", "tiger_spmrl" : "German (Tiger)", "negra" : "German (Negra)",
            "gap_unlex_uncat"    : "\\textsc{sr-gap}          & \\textsc" + features[0] + " & {} ".format(oracles[0]),
            "gap_lex_uncat"      : "\\textsc{sr-gap}          & \\textsc" + features[1] + " & {} ".format(oracles[0]),
            "gap_unlex"          : "\\textsc{sr-gap}          & \\textsc" + features[2] + " & {} ".format(oracles[0]),
            "gap_lex"            : "\\textsc{sr-gap}          & \\textsc" + features[3] + " & {} ".format(oracles[0]),
        
            "merge0_unlex_uncat" : "\\textsc{ml-gap}          & \\textsc" + features[0] + " & {} ".format(oracles[1]),
            "merge0_unlex"       : "\\textsc{ml-gap}          & \\textsc" + features[2] + " & {} ".format(oracles[1]),

            "merge4_unlex_uncat" : "\\textsc{ml-gap} & \\textsc" + features[0] + " & {} ".format(oracles[0]),
            "merge4_unlex"       : "\\textsc{ml-gap} & \\textsc" + features[2] + " & {} ".format(oracles[0]),

            "usr6_unlex_uncat" : "\\textsc{sr-gap-unlex} & \\textsc" + features[0] + " & {} ".format(oracles[1]),
            "usr6_unlex"       : "\\textsc{sr-gap-unlex} & \\textsc" + features[2] + " & {} ".format(oracles[1]),

            "merge2_unlex_uncat" : "\\textsc{ml-gap-lex}      & \\textsc" + features[0] + " & {} ".format(oracles[1]),
            "merge2_lex_uncat"   : "\\textsc{ml-gap-lex}      & \\textsc" + features[1] + " & {} ".format(oracles[1]),
            "merge2_unlex"       : "\\textsc{ml-gap-lex}      & \\textsc" + features[2] + " & {} ".format(oracles[1]),
            "merge2_lex"         : "\\textsc{ml-gap-lex}      & \\textsc" + features[3] + " & {} ".format(oracles[1])}

    
    results = get_all_results(args.datadir, args.expedir)
    
    generate_const_results(results, mapping)
    
    generate_morph_results(results, mapping)
