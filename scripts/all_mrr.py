
from __future__ import print_function

import csv
import src.main
import src.utils
import logging
import sys
import scipy.stats

def ap(project, t):
    goldsets = src.main.create_goldsets(project)
    ranks = src.main.read_ranks(project, t)
    frms = src.main.get_frms(goldsets, ranks)
    c = project.name+project.version
    new = list()
    for r, i, g in frms:
        new.append((r, c+str(i), g))

    return new


def print_em(desc, a, b, ignore=False, file=None):
    acc = 6
    x, y = src.main.merge_first_rels(b, a, ignore=ignore)
    T, p = scipy.stats.wilcoxon(x, y, correction=True)


    changeset = round(src.utils.calculate_mrr(x), acc)
    snapshot = round(src.utils.calculate_mrr(y), acc)
    if changeset >= snapshot:
        changeset = "{\\bf %f }" % changeset
        snapshot = "%f" % snapshot
    else:
        snapshot = "{\\bf %f }" % snapshot
        changeset = "%f" % changeset

    if len(x) < 10:
        star = "^{*}"
    else:
        star = ''

    if p < 0.01:
        p = "$p < 0.01%s$" % star
    else:
        p = "$p = %f%s$" % (p, star)


    l = [desc,
        snapshot, changeset,
        p
        ]

    print(' & '.join(map(str, l)), '\\\\', file=file)

HEADER="""\\begin{table}[t]
\\renewcommand{\\arraystretch}{1.3}
\\footnotesize
\\centering"""
INNER_HEADER="""\\caption{{\\bf %s}: MRR and $p$-values}
\\begin{tabular}{l|ll|ll}
\\toprule
Subject System & %s & %s & $p$-value  \\\\
\\midrule"""
INNER_FOOTER= "\\bottomrule\n\\end{tabular}\n\\label{table:%s:%s:%s}"
FOOTER="\\end{table}"

projects = src.main.load_projects({"level": "file", "num_topics": 500})
ex = ["solr", "lucene"]

for kind in ['lda']: # 'lsi']:
    alldict = dict()
    with open('paper/tables/rq1_%s.tex' % kind, 'w') as f:
        print(HEADER, file=f)
        for level in ['class', 'method']:
            rname = 'release_' + kind
            cname = 'changeset_' + kind
            alldict[rname] = list()
            alldict[cname] = list()
            print(INNER_HEADER % ('RQ1', 'Snapshot', 'Changeset'), file=f)
            for project in projects:
                if project.name in ex:
                    continue
                desc = ' '.join([project.printable_name, project.version])

                a = ap(project, rname)
                b = ap(project, cname)

                alldict[rname] += a
                alldict[cname] += b

                print_em(desc, a, b, ignore=False, file=f)

            print('\\midrule', file=f)
            print_em("All", alldict[rname], alldict[cname], ignore=False, file=f)
            print(INNER_FOOTER % ('rq1', level, kind), file=f)

        print(FOOTER, file=f)

