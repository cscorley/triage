
from __future__ import print_function, division

import csv
import src
import src.main
import src.utils
import logging
import sys
import scipy.stats
import os.path

def fake(*args, **kwargs):
    print('Fake called with', str(args), str(kwargs))
    sys.exit(1)

# fake out the create_model so we don't accidentally attempt to
# create data
src.common.create_model = fake

def ap(project, t):
    goldsets = src.main.create_goldsets(project)
    ranks = src.main.read_ranks(project, t)
    frms = src.main.get_frms(goldsets, ranks)
    c = project.name+project.version
    new = list()
    for r, i, g in frms:
        new.append((r, c+str(i), g))

    return new


def print_em(desc, a, b, ignore=True, file=None):
    acc = 6
    x, y = src.common.merge_first_rels(b, a, ignore=ignore)
    T, p = scipy.stats.wilcoxon(x, y, correction=True)

    nonzeros = sum(1 for a, b in zip(x, y) if (a - b) != 0)
    S = sum(range(1, nonzeros + 1))


    assert S >= T, "%f %f" % (S, T)

    Td = S - T
    rsp1 = Td / S
    rsp2 = T / S
    r = rsp1 - rsp2
    # From this information alone, the remaining rank sum can be computed, because
    # it is the total sum S minus T, or in this case 45 - 18 = 27. Next, the two
    # rank-sum proportions are 27/45 = 60% and 18/45 = 40%. Finally, the rank
    # correlation is the difference between the two proportions (.60 minus .40),
    # hence r = .20.

    r = "$%.4f$" % r

    assert len(x) == len(y),  "Got different lengths in print_em! Results will be unfair"

    changeset = round(src.utils.calculate_mrr(x), acc)
    snapshot = round(src.utils.calculate_mrr(y), acc)

    if changeset >= snapshot:
        spread = "$+%.4f$" % (changeset - snapshot)
        changeset = "$\\bm{%.4f}$" % changeset
        snapshot = "$%.4f$" % snapshot
    else:
        spread = "$%.4f$" % (changeset - snapshot)
        snapshot = "$\\bm{%.4f}$" % snapshot
        changeset = "$%.4f$" % changeset

    if len(x) < 10:
        star = "^{*}"
    else:
        star = ''

    if p < 0.01:
        p = "$p < 0.01$%s" % star
    else:
        p = "$p = %.4f$%s" % (p, star)


    l = [desc,
         len(x),
         snapshot, changeset,
         spread,
         p,
         r
         ]

    print(' & '.join(map(str, l)), '\\\\', file=file)

HEADER="""\\begin{table}[t]
\\centering"""
INNER_HEADER="""\\caption{%s: MRR, Wilcoxon $p$-values, and effect size}
\\begin{tabular}{l|r|ccr|ll}
\\toprule
Subject & Successful &    & MRR &        & Wilcoxon  & Effect \\\\
System  & Queries    & %s & %s  & Spread & $p$-value & size \\\\
\\midrule"""
INNER_FOOTER= "\\bottomrule\n\\end{tabular}\n\\label{table:%s_%s}"
FOOTER="\\end{table}"

ex = ["derby"]

kwargs = dict(
    model='lda',
    level='file',
    force=False,
    random_seed_value=1,
)

changeset_config = {
    'include_additions': True,
    'include_context': True,
    'include_message': False,
    'include_removals': True,
}

model_config = {
    'num_topics': 500,
    'alpha': 1/500,
    'eta': 1/500,
    'decay': 0.5,
    'offset': 1.0,
    'iterations': 1000,
    'passes': 1,
    'max_bound_iterations': 1000, # special
    'algorithm': 'batch', # special
}

model_config, model_config_string = src.main.get_default_model_config(kwargs)
changeset_config, changeset_config_string = src.main.get_default_changeset_config()

kwargs.update({'changeset_config': changeset_config,
                'changeset_config_string': changeset_config_string})

kwargs.update({'model_config': model_config,
                'model_config_string': model_config_string})

for kind, title in [('triage', 'Deverloper Identification'),
                        ('feature_location', 'Feature Location')]:
    kwargs.update({'experiment': kind,
                   'source': ['release', 'changeset'],
                   'level': 'file'})

    alldict = dict(release=list(), changeset=list())
    with open(os.path.expanduser('~/git/dissertation/tables/%s_rq1.tex' % kind), 'w') as f:
        print(HEADER, file=f)
        projects = src.common.load_projects(kwargs)
        print(INNER_HEADER % (title, 'Snapshot', 'Changesets'), file=f)
        for project in sorted(projects, key=lambda x: x.name):
            if project.name in ex:
                continue
            desc = ' '.join([project.printable_name, project.version])

            results = src.main.run_experiments(project)
            print_em(project.printable_name.capitalize(), results['release'], results['changeset'], file=f)
            alldict['release'].extend([(x, project.name + y, z) for x, y, z in results['release']])
            alldict['changeset'].extend([(x, project.name + y, z) for x, y, z in results['changeset']])

        print('\\midrule', file=f)
        print_em("All", alldict['release'], alldict['changeset'], file=f)
        print(INNER_FOOTER % (kwargs['experiment'], 'rq1'), file=f)

        print(FOOTER, file=f)

    kwargs.update({'experiment': kind,
                   'source': ['temporal', 'changeset'],
                   'level': 'file'})
    alldict = dict(temporal=list(), changeset=list())
    with open(os.path.expanduser('~/git/dissertation/tables/%s_rq2.tex' % kind), 'w') as f:
        print(HEADER, file=f)
        projects = src.common.load_projects(kwargs)
        print(INNER_HEADER % (title, 'Batch', 'Historical Sim.'), file=f)
        for project in sorted(projects, key=lambda x: x.name):
            if project.name in ex:
                continue
            desc = ' '.join([project.printable_name, project.version])

            results = src.main.run_experiments(project)
            print_em(project.printable_name.capitalize().replace("keeper", "Keeper").replace("Openjpa", "OpenJPA"),
                     results['changeset'], results['temporal'], file=f)
            alldict['temporal'].extend([(x, project.name + y, z) for x, y, z in results['temporal']])
            alldict['changeset'].extend([(x, project.name + y, z) for x, y, z in results['changeset']])

        print('\\midrule', file=f)
        print_em("All", alldict['changeset'], alldict['temporal'], file=f)
        print(INNER_FOOTER % (kwargs['experiment'], 'rq2'), file=f)

        print(FOOTER, file=f)

