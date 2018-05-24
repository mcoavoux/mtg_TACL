#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import glob
import os
from joblib import Parallel, delayed

def unix(command) :
    print(command)
    subprocess.call([command], shell=True)

def get_beam_it(filename):
    # pred_devb1it3.discbracket
    f = filename.split(".")[0]
    f, i = f.split("it")
    f, b = f.split("b")
    assert(int(i) > 0)
    assert(int(b) == 1)
    return b, i

def evaluate_one(l):
    datadir, expedir, pred_file = l
    
    exp, model_type, corpus, model, p_file = pred_file.split("/")
    
    corpus_type = None
    if "dev" in pred_file:
        corpus_type = "dev"
    else:
        corpus_type = "test"
        assert("test" in pred_file)
    
    gold_corpus = "{}/{}/{}.discbracket".format(datadir, corpus, corpus_type)
    assert(os.path.exists(gold_corpus))
    
    b, it = get_beam_it(p_file)
    
    # disceval_pr_dev_b1_it19
    
    output = "/".join([exp, model_type, corpus, model, "disceval_pr_{}_b{}_it{}".format(corpus_type, b, it)])
    command = "discodop eval {gold} {pred} proper.prm --fmt=discbracket --disconly > {res}".format(gold=gold_corpus, pred=pred_file, res=output)
    unix(command)
    
    output = "/".join([exp, model_type, corpus, model, "eval_pr_{}_b{}_it{}".format(corpus_type, b, it)])
    command = "discodop eval {gold} {pred} proper.prm --fmt=discbracket > {res}".format(gold=gold_corpus, pred=pred_file, res=output)
    unix(command)

def evaluate(datadir, expedir, threads):
    
    expedir = expedir.strip("/")
    
    pred_files = glob.glob("{}/*/*/*/pred*.discbracket".format(expedir))
    
    Parallel(n_jobs=threads)(delayed(evaluate_one)([datadir, expedir, f]) for f in pred_files)


def main():
    
    import argparse
    
    usage = """       """
    parser = argparse.ArgumentParser(description = usage, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("datadir", help="directory with experiments")
    parser.add_argument("expedir", help="directory with experiments")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    
    evaluate(args.datadir, args.expedir, args.threads)




if __name__ == '__main__':

    main()

