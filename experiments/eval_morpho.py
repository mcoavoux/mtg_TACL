import argparse
from collections import defaultdict


ID, TOKEN, LEMMA, CPOS, FPOS, MORPH, HEAD, DEP, PHEAD, PDEP = range(10)

def conll_corpus_reader(filename):
    lines = open(filename, "r", encoding="utf8").read()
    sentences = [ [ line.split("\t") for line in sent.split("\n") ] for sent in lines.split("\n\n") if sent.strip() ]
    return sentences

def get_mdict(s) :
    if s == "_" :
        return {}
    return dict([ w.split("=", 1) for w in s.split("|") ])


def evaluate(gold, pred) :
    assert ( len(gold) == len(pred) )
    
    
    n_sentences = len(gold)
    n_tokens = 0
    
    ctags = 0
    ftags = 0
    deps = 0
    
    complete_match = 0
    
    morph = defaultdict(lambda:[0,0,0,0])
    TP, TN, FP, FN = range(4)
    
    
    gmorph_ats = set()
    pmorph_ats = set()
    for i in range(n_sentences) :
        gsent = gold[i]
        psent = pred[i]
        assert( len(gsent) == len(psent) )
        for j in range(len(gsent)) :
            gmorph_ats |= set(get_mdict(gsent[j][MORPH]).keys())
            pmorph_ats |= set(get_mdict(psent[j][MORPH]).keys())
    
    gmorph_ats = pmorph_ats
    
    for i in range(n_sentences) :
        gsent = gold[i]
        psent = pred[i]
        
        n_tokens += len(gsent)
        
        for j in range(len(gsent)) :
            
            assert( gsent[j][:2] == psent[j][:2] )
            
            if gsent[j][CPOS] == psent[j][CPOS] :
                ctags += 1
            if gsent[j][FPOS] == psent[j][FPOS] :
                ftags += 1
            if gsent[j][DEP] == psent[j][DEP] :
                deps += 1
            
            gmorph = get_mdict(gsent[j][MORPH])
            pmorph = get_mdict(psent[j][MORPH])
            
            for attribute in gmorph_ats :
                if attribute in gmorph :
                    if attribute in pmorph :
                        if gmorph[attribute] == pmorph[attribute] :
                            morph[attribute][TP] += 1
                        else :
                            morph[attribute][FP] += 1
                    else :
                        morph[attribute][FN] += 1
                else :
                    if attribute in pmorph :
                        morph[attribute][FP] += 1
                    else :
                        morph[attribute][TN] += 1
            
            filtered_gmorph = {k : v for k,v in gmorph.items() if k in gmorph_ats}
            if gsent[j][FPOS] == psent[j][FPOS] and filtered_gmorph == pmorph :
                complete_match += 1
    
    
    result = {"sentences" : n_sentences,
              "tokens" : n_tokens,
              "cpos" : ctags / n_tokens,
              "fpos" : ftags / n_tokens,
              "deps" : deps / n_tokens,
              "complete_match" : complete_match / n_tokens,
              "list":[]}
    
    for attribute in gmorph_ats :
        l = morph[attribute]
        result["morph {} accuracy".format(attribute)]  = (l[TP] + l[TN]) / n_tokens
        result["morph {} coverage".format(attribute)]  = (l[TP] + l[FN]) / n_tokens
        
        
        if 0 in l :
            prec = reca = fmea = 0
        else :
            prec = l[TP] / (l[TP] + l[FP])
            reca = l[TP] / (l[TP] + l[FN])
            fmea = 2 * prec * reca / (prec + reca)
        
        result["morph {} f-measure".format(attribute)] = fmea
        result["morph {} precision".format(attribute)] = prec
        result["morph {} recall".format(attribute)]    = reca
        result["list"].append(attribute)
    
    return result
    


def main(goldfile, predfile) :
    goldcorpus = conll_corpus_reader(goldfile)
    predcorpus = conll_corpus_reader(predfile)

    return evaluate(goldcorpus, predcorpus)
    


if __name__ == "__main__" :
    
    usage="""
        Evaluation script for morphology and dependency label
    """
    
    parser = argparse.ArgumentParser(description = usage, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("gold", type = str, help="gold conll file")
    parser.add_argument("pred", type = str, help="pred conll file")
    
    
    args = parser.parse_args()
    
    result = main(args.gold, args.pred)
    
    for k,v in sorted(result.items()) :
        print(k, "\t", v)
    
    