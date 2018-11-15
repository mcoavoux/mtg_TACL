
if [ "$#" -ne 1 ]
then
    echo "Illegal number of parameters"
    echo Usage:
    echo    "sh reparse_dev.sh <multilingual_disco_data/data>"
    exit 1
fi

data=$1

mkdir -p dev_results


t1=ml_gap_lex_with_base_features
t2=ml_gap_lex_with_lex_features
t3=ml_gap_unlex_eager_oracle
t4=ml_gap_unlex_head_oracle
t5=sr_gap_lex_with_base_features
t6=sr_gap_lex_with_lex_features
t7=sr_gap_unlex

for ts in $t1 $t2 $t3 $t4 $t5 $t6 $t7
do
    for corpus in tiger_spmrl negra dptb
    do
        model="pretrained/${ts}/${corpus}"
        input="${data}/${corpus}/dev.raw"
        gold="${data}/${corpus}/dev.discbracket"
        pred=dev_results/${corpus}_${ts}

        ./bin/mtg2_parser -m ${model} -F 1 -b 1 -x ${input} -o ${pred}
        discodop eval ${gold} ${pred} --fmt=discbracket experiments/proper.prm > ${pred}_eval
        discodop eval ${gold} ${pred} --fmt=discbracket experiments/proper.prm --disconly > ${pred}_eval_disconly
    done
done




