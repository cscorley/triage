#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
logger = logging.getLogger('common')

import csv
import os
import os.path
from collections import namedtuple

import dulwich.repo
import scipy.stats
import numpy
from gensim.corpora import MalletCorpus, Dictionary
from gensim.models import LdaModel, LsiModel, HdpModel
from gensim.matutils import sparse2full
from gensim.utils import smart_open, to_unicode, to_utf8

import utils
from corpora import (ChangesetCorpus, SnapshotCorpus, ReleaseCorpus,
                     TaserSnapshotCorpus, TaserReleaseCorpus,
                     CorpusCombiner, GeneralCorpus)
from errors import TaserError
from ownership import build_ownership

def check_ranks(project, kind, experiment):
    if project.force:
        return None

    if kind == 'changeset':
        rank_name = '-'.join([kind, experiment, project.model, project.changeset_config_string, project.model_config_string]).lower()
    elif kind == 'temporal':
        rank_name = '-'.join([kind, experiment, project.model, project.changeset_config_string]).lower()
    else:
        rank_name = '-'.join([kind, experiment, project.model, project.model_config_string]).lower()

    try:
        return read_ranks(project, rank_name), rank_name
    except IOError:
        return None, rank_name

def run_basic(project, corpus, other_corpus, queries, goldsets, eval_name, rank_name):
    """
    This function runs the experiment in one-shot. It does not evaluate the
    changesets over time.
    """
    logger.info("Running basic evaluation on the %s", eval_name)

    train_perplexity = None
    infer_perpleixty = None

    if project.model == "lda":
        model, _ = create_model(project, corpus, corpus.id2word, LdaModel, eval_name)
        train_perplexity = get_perplexity(model, corpus)
        other_perplexity = get_perplexity(model, other_corpus)
    elif project.model == "hdp":
        model, _ = create_model(project, corpus, corpus.id2word, HdpModel, eval_name)
    elif project.model == "lsi":
        model, _ = create_model(project, corpus, corpus.id2word, LsiModel, eval_name)


    query_topic = get_topics(model, queries)
    doc_topic = get_topics(model, other_corpus)

    ranks = get_rank(query_topic, doc_topic, goldsets)
    write_ranks(project, rank_name, ranks)

    return get_frms(ranks, goldsets), train_perplexity, other_perplexity

def get_perplexity(model, corpus):
    old_id2word = corpus.id2word
    corpus.id2word = model.id2word
    perplexity = numpy.exp2(-model.log_perplexity(corpus))
    corpus.id2word = old_id2word

    return perplexity

def collect_info(project, repos, queries, goldsets, changeset_corpus, release_corpus):
    logger.info("Collecting corpus metadata info")
    changeset_corpus.metadata = True
    release_corpus.metadata = True
    queries.metadata = True
    ids = load_ids(project)
    try:
        issue2git, git2issue = load_issue2git(project, ids)
    except:
        return

    path = os.path.join(project.full_path, "general-info.csv")
    if not os.path.exists(path):
        with smart_open(path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(["changesets_before_first"])
            row = list()

            for i, docmeta in enumerate(changeset_corpus):
                doc, meta = docmeta
                if meta[0] in git2issue:
                    row.append(i)
                    break

            writer.writerow(row)

    path = os.path.join(project.full_path, 'goldset-info.csv')
    if not os.path.exists(path):
        with smart_open(path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(["metadata", "total_entities"])

            for gid, goldset in goldsets.items():
                row = list()
                row.append(gid)
                row.append(len(goldset))
                writer.writerow(row)

    collect_helper(project, changeset_corpus, 'changeset')
    collect_helper(project, release_corpus, 'release' + project.level)
    collect_helper(project, queries, 'queries')

    changeset_corpus.metadata = False
    release_corpus.metadata = False
    queries.metadata = False

def collect_helper(project, corpus, name):
    logger.info("Helper corpus metadata info of " + name)
    path = os.path.join(project.full_path, '-'.join([name, 'info.csv']))

    if os.path.exists(path):
        return

    with smart_open(path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["metadata", "unique_words", "total_words"])

        for doc, meta in corpus:
            row = list()
            row.append(meta[0])
            row.append(len(doc))
            row.append(sum(freq for word, freq in doc))
            writer.writerow(row)

def write_ranks(project, prefix, ranks):
    path = os.path.join(project.full_path, '-'.join([prefix, project.level, 'ranks.csv.gz']))
    logger.info("Attempting to write %d ranks to: %s", len(ranks), path)
    with smart_open(path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'rank', 'distance', 'item'])

        for gid, rank in ranks.items():
            for idx, dist, d_name in rank:
                writer.writerow([gid, idx, dist, to_utf8(d_name)])

def read_ranks(project, prefix):
    path = os.path.join(project.full_path, '-'.join([prefix, project.level, 'ranks.csv.gz']))
    logger.info("Attempting to read ranks from: %s", path)
    ranks = dict()
    with smart_open(path) as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for g_id, idx, dist, d_name in reader:
            if g_id not in ranks:
                ranks[g_id] = list()

            ranks[g_id].append((int(idx), float(dist), to_unicode(d_name)))

    logger.info("Read %d ranks", len(ranks))

    return ranks


def run_temporal(project, repos, corpus, create_other_corpus, queries, goldsets, rank_name):
    logger.info("Running temporal evaluation")

    force = project.force
    try:
        ranks = read_ranks(project, rank_name)

        logger.info("Sucessfully read previously written Temporal ranks")
    except IOError:
        force = True

    if force:
        ranks = run_temporal_helper_chunks(project, repos, corpus, create_other_corpus, queries, goldsets)
        #ranks = run_temporal_helper(project, repos, corpus, create_other_corpus, queries, goldsets)
        write_ranks(project, rank_name, ranks)

    return get_frms(ranks, goldsets)


def run_temporal_helper(project, repos, corpus, create_other_corpus, queries, goldsets):
    """
    This function runs the experiment in over time. That is, it stops whenever
    it reaches a commit linked with an issue/query. Will not work on all
    projects.
    """
    ids = load_ids(project)
    issue2git, git2issue = load_issue2git(project, ids, filter_ids=True)

    logger.info("Stopping at %d commits for %d issues", len(git2issue), len(issue2git))

    if project.model == "lda":
        model, model_fname = create_model(project, None, corpus.id2word, LdaModel, 'temporal', force=True)
    elif project.model == "hdp":
        model, model_fname = create_model(project, None, corpus.id2word, HdpModel, 'temporal', force=True)
    elif project.model == "lsi":
        model, model_fname = create_model(project, None, corpus.id2word, LsiModel, 'temporal', force=True)

    indices = list()
    ranks = dict()
    docs = list()
    corpus.metadata = True
    prev = 0

    logger.info("Partitioning corpus")

    # let's partition the corpus first
    for idx, docmeta in enumerate(corpus):
        doc, meta = docmeta
        sha, _ = meta
        if sha in git2issue:
            indices.append((prev, idx+1, sha))
            prev = idx

    logger.info('Created %d partitions of the corpus', len(indices))
    corpus.metadata = False


    for counter, index  in enumerate(indices):
        logger.info('At %d of %d partitions', counter, len(indices))
        start, end, sha = index

        sha_model_fname = model_fname % sha
        if os.path.exists(sha_model_fname):
            # need to be super careful that the way this one was built matches what we expect
            # e.g., didn't come from a different run with a different update pattern
            model = model.load(sha_model_fname)
        else:
            #docs = list()
            #for i in xrange(start, end):
                #docs.append(corpus[i])
            if project.model == "lda":
                for i in xrange(start, end):
                    model.update([corpus[i]])
            if project.model == "lsi":
                model.add_documents(docs)

            if project.save_models:
                model.save(sha_model_fname) # thanks, gensim!


        for qid in set(git2issue[sha]):
            logger.info('Getting ranks for query id %s', qid)
            try:
                other_corpus = create_other_corpus(project, repos, changesets=corpus, ref=sha)
            except TaserError:
                continue

            query_topic = get_topics(model, queries, by_ids=[qid])
            doc_topic = get_topics(model, other_corpus)
            subranks = get_rank(query_topic, doc_topic, goldsets)
            if qid in subranks:
                if qid not in ranks:
                    ranks[qid] = list()

                rank = subranks[qid]
                ranks[qid].extend(rank)
            else:
                logger.info('Couldnt find qid %s', qid)

    return ranks

def run_temporal_helper_chunks(project, repos, corpus, create_other_corpus, queries, goldsets):
    """
    This function runs the experiment in over time. That is, it stops whenever
    it reaches a commit linked with an issue/query. Will not work on all
    projects.
    """
    ids = load_ids(project)
    issue2git, git2issue = load_issue2git(project, ids, filter_ids=True)

    logger.info("Stopping at %d commits for %d issues", len(git2issue), len(issue2git))

    if project.model == "lda":
        model, model_fname = create_model(project, None, corpus.id2word, LdaModel, 'temporal', force=True)
    elif project.model == "hdp":
        model, model_fname = create_model(project, None, corpus.id2word, HdpModel, 'temporal', force=True)
    elif project.model == "lsi":
        model, model_fname = create_model(project, None, corpus.id2word, LsiModel, 'temporal', force=True)

    indices = list()
    ranks = dict()
    docs = list()
    corpus.metadata = True
    prev = 0

    logger.info("Partitioning corpus")

    # let's partition the corpus first
    for idx, docmeta in enumerate(corpus):
        doc, meta = docmeta
        sha, _ = meta
        if sha in git2issue:
            indices.append((prev, idx+1, sha))
            prev = idx

    logger.info('Created %d partitions of the corpus', len(indices))
    corpus.metadata = False


    for counter, index  in enumerate(indices):
        logger.info('At %d of %d partitions', counter, len(indices))
        start, end, sha = index

        sha_model_fname = model_fname % sha
        if os.path.exists(sha_model_fname):
            # need to be super careful that the way this one was built matches what we expect
            # e.g., didn't come from a different run with a different update pattern
            model = model.load(sha_model_fname)
        else:
            docs = corpus[start:end]
            if project.model == "lda":
                model.update(docs, chunksize=len(docs))
            if project.model == "lsi":
                model.add_documents(docs)

            if project.save_models:
                model.save(sha_model_fname) # thanks, gensim!


        for qid in set(git2issue[sha]):
            logger.info('Getting ranks for query id %s', qid)
            try:
                other_corpus = create_other_corpus(project, repos, changesets=corpus, ref=sha)
            except TaserError:
                continue

            query_topic = get_topics(model, queries, by_ids=[qid])
            doc_topic = get_topics(model, other_corpus)
            subranks = get_rank(query_topic, doc_topic, goldsets)
            if qid in subranks:
                if qid not in ranks:
                    ranks[qid] = list()

                rank = subranks[qid]
                ranks[qid].extend(rank)
            else:
                logger.info('Couldnt find qid %s', qid)

    return ranks

def run_temporal_helper_full_1(project, repos, corpus, create_other_corpus, queries, goldsets):
    """
    This function runs the experiment in over time. That is, it stops whenever
    it reaches a commit linked with an issue/query. Will not work on all
    projects.
    """
    ids = load_ids(project)
    issue2git, git2issue = load_issue2git(project, ids, filter_ids=True)

    logger.info("Stopping at %d commits for %d issues", len(git2issue), len(issue2git))

    if project.model == "lda":
        model, model_fname = create_model(project, None, corpus.id2word, LdaModel, 'temporal', force=True)
    elif project.model == "hdp":
        model, model_fname = create_model(project, None, corpus.id2word, HdpModel, 'temporal', force=True)
    elif project.model == "lsi":
        model, model_fname = create_model(project, None, corpus.id2word, LsiModel, 'temporal', force=True)

    ranks = dict()
    corpus.metadata = True

    for idx, docmeta in enumerate(corpus):
        doc, meta = docmeta
        sha, _ = meta

        sha_model_fname = model_fname % sha
        if os.path.exists(sha_model_fname):
            # need to be super careful that the way this one was built matches what we expect
            # e.g., didn't come from a different run with a different update pattern
            model = model.load(sha_model_fname)
        else:
            #docs = list()
            #for i in xrange(start, end):
                #docs.append(corpus[i])
            if project.model == "lda":
                model.update([doc])
            if project.model == "lsi":
                model.add_documents(docs)

            if project.save_models:
                model.save(sha_model_fname) # thanks, gensim!


        if sha in git2issue:
            for qid in set(git2issue[sha]):
                logger.info('Getting ranks for query id %s', qid)
                try:
                    other_corpus = create_other_corpus(project, repos, changesets=corpus, ref=sha)
                except TaserError:
                    continue

                query_topic = get_topics(model, queries, by_ids=[qid])
                doc_topic = get_topics(model, other_corpus)
                subranks = get_rank(query_topic, doc_topic, goldsets)
                if qid in subranks:
                    if qid not in ranks:
                        ranks[qid] = list()

                    rank = subranks[qid]
                    ranks[qid].extend(rank)
                else:
                    logger.info('Couldnt find qid %s', qid)

    return ranks


def merge_first_rels(a, b, ignore=False, penalty=None):
    logger.info('merging %d rels with %d rels, ignore=%s, penalty=%s', len(a), len(b), str(ignore), str(penalty))
    first_rels = dict()

    for num, query_id, doc_meta in a:
        #qid = int(query_id)
        qid = query_id
        if qid not in first_rels:
            first_rels[qid] = [num]
        else:
            logger.info('duplicate qid found: %s', query_id)

    for num, query_id, doc_meta in b:
        #qid = int(query_id)
        qid = query_id
        if qid not in first_rels and not ignore:
            logger.info('added a penalty: %s', qid)
            first_rels[qid] = [penalty]

        if qid in first_rels:
            first_rels[qid].append(num)

    removals = list()
    for key, v in first_rels.items():
        if len(v) == 1:
            logger.info('added b penalty: %s', key)
            v.append(penalty)

        if ignore and (v[0] == penalty or v[1] == penalty):
            logger.info('removal added: %s', key)
            removals.append(key)

    x = [v[0] for k, v in first_rels.items() if k not in removals]
    y = [v[1] for k, v in first_rels.items() if k not in removals]
    #assert any([i == 0 for i in x])
    #assert any([i == 0 for i in y])
    return x, y


def get_frms(ranks, goldsets):
    logger.info('Getting FRMS for %d ranks', len(ranks))
    frms = list()

    for r_id, rank in ranks.items():
        if r_id not in goldsets:
            logger.info('Skipping %s, not in goldset', str(r_id))
            continue

        added = False
        for idx, dist, name in rank:
            if name in goldsets[r_id]:
                added = True
                frms.append((idx, r_id, name))
                break # take only the first one

        if not added:
            logger.info('Found no FRM for %s goldset \n\t %s', str(r_id), str(goldsets[r_id]))

    logger.info('Returning %d FRMS', len(frms))
    return frms

def get_rels(ranks, goldset=None):
    rels = list()

    if goldset:
        dists = list()
        for name in goldset:
            if name in ranks:
                dists.append((ranks[name], name))

        for dist, name in dists:
            idx = len([1 for x in ranks.values() if x < dist])
            rels.append((idx+1, dist, name))

    else:
        # without the goldset, we have to sort and enumerate all items :(
        sorted_ranks = sorted(ranks.items(), key=lambda x: x[1])
        for idx, rank in enumerate(sorted_ranks):
            d_name, dist = rank
            rels.append((idx+1, dist, d_name))

    rels.sort()

    return rels


def get_rank(query_topic, doc_topic, goldsets=None, distance_measure=utils.hellinger_distance):
    logger.info('Getting ranks between %d query topics and %d doc topics',
                len(query_topic), len(doc_topic))
    ranks = dict()
    for q_meta, query in query_topic:
        qid, _ = q_meta
        q_dist = dict()

        for d_meta, doc in doc_topic:
            d_name, _ = d_meta
            q_dist[d_name] = distance_measure(query, doc)

        if goldsets and qid in goldsets:
            goldset = goldsets[qid]
        else:
            goldset = None

        ranks[qid] = get_rels(q_dist, goldset)

    logger.info('Returning %d ranks', len(ranks))
    return ranks


def get_topics(model, corpus, by_ids=None, full=True):
    logger.info('Getting doc topic for corpus with length %d, by ids %s', len(corpus), str(by_ids))
    doc_topic = list()
    corpus.metadata = True
    old_id2word = corpus.id2word
    corpus.id2word = model.id2word

    if by_ids:
        by_ids = set(by_ids)
        by_ids.update([str(x) for x in by_ids])
    logger.debug("BYIDS:%s", by_ids)

    for doc, metadata in corpus:
        logger.debug("METADATA:%s", str(metadata))
        if by_ids is None or metadata[0] in by_ids:
            # get a vector where low topic values are zeroed out.
            topics = model[doc]
            if full:
                topics = sparse2full(topics, model.num_topics)

            # this gets the "full" vector that includes low topic values
            # topics = model.__getitem__(doc, eps=0)
            # topics = [val for id, val in topics]

            doc_topic.append((metadata, topics))

    corpus.metadata = False
    corpus.id2word = old_id2word
    logger.info('Returning doc topic of length %d', len(doc_topic))

    return doc_topic




def load_ids(project):
    with open(os.path.join(project.full_path, 'ids.txt')) as f:
        ids = [x.strip() for x in f.readlines()]

    return ids



def load_issue2git(project, ids, filter_ids=False):
    logger.info("Loading issue2git.csv")
    dest_fn = os.path.join(project.data_path, 'issue2git.csv')
    if os.path.exists(dest_fn):
        write_out = False
        i2g = dict()
        with open(dest_fn) as f:
            r = csv.reader(f)
            for issue, repo, sha in r:
                if issue not in i2g:
                    i2g[issue] = list()
                i2g[issue].append(sha)

    else:
        write_out = True

        i2s = dict()
        fn = os.path.join(project.full_path, 'IssuesToSVNCommitsMapping.txt')
        with open(fn) as f:
            lines = [line.strip().split('\t') for line in f]
            for line in lines:
                issue = line[0]
                links = line[1]
                svns = line[2:]

                i2s[issue] = svns

        s2g = dict()
        fn = os.path.join(project.data_path, 'svn2git.csv')
        with open(fn) as f:
            reader = csv.reader(f)
            for svn,git in reader:
                if svn in s2g and s2g[svn] != git:
                    logger.info('Different gits sha for SVN revision number %s', svn)
                else:
                    s2g[svn] = git

        i2g = dict()
        for issue, svns in i2s.items():
            for svn in svns:
                if svn in s2g:
                    # make sure we don't have issues that are empty
                    if issue not in i2g:
                        i2g[issue] = list()
                    i2g[issue].append(s2g[svn])
                else:
                    logger.info('Could not find git sha for SVN revision number %s', svn)

    logger.info("Loaded issue2git with %d entries", len(i2g))

    # Make sure we have a commit for all issues
    keys = set(i2g.keys())
    ignore = set(ids) - keys
    if len(ignore):
        logger.info("Ignoring evaluation for the following issues:\n\t%s",
                    '\n\t'.join(ignore))

    # clean up by ids if needed:
    if filter_ids:
        for issue in i2g.keys():
            if issue not in ids:
                del i2g[issue]


    # build reverse mapping
    g2i = dict()
    for issue, gits in i2g.items():
        for git in gits:
            if git not in g2i:
                g2i[git] = list()
            g2i[git].append(issue)

    if write_out:
        with open(dest_fn, 'w') as f:
            w = csv.writer(f)
            for issue, gits in i2g.items():
                w.writerow([issue] + gits)

    logger.info("Returning issue2git with len %d and git2issue with len %d", len(i2g), len(g2i))

    return i2g, g2i


def load_projects(config, path='data'):
    projects = list()
    refpaths = list()
    for dirpath, dirname, filenames in os.walk(path):
        for filename in filenames:
            if filename == 'ref':
                refpaths.append(os.path.join(dirpath, filename))

    for refpath in refpaths:
        with open(refpath) as f:
            ref = f.read().strip()

        # extract project info based on path, weeee
        full_path, _ = os.path.split(refpath)
        data_path, project_version = os.path.split(full_path)
        _, project_name = os.path.split(data_path)
        src_path = os.path.join(full_path, 'src')

        Project = namedtuple('Project',  ' '.join(['name', 'printable_name', 'version', 'ref', 'data_path', 'full_path', 'src_path']
                                                  + config.keys()))
        # figure out which column index contains the project name

        # find the project in the csv, adding it's info to config
        # do the os.path.join to force a trailing slash
        row = [project_name, make_title(project_name) + ' ' + project_version, project_version, ref,
               os.path.join(data_path, ''),
               os.path.join(full_path, ''),
               os.path.join(src_path, '')]
        row += config.values()

        projects.append(Project(*row))

    return projects

def make_title(name):
    return name.title().replace("keeper", "Keeper").replace("jpa", "JPA")


def load_repos(project):
    # reading in repos
    with open(os.path.join('data', project.name, 'repos.txt')) as f:
        repo_urls = [line.strip() for line in f]

    repos_base = 'gits'
    if not os.path.exists(repos_base):
        utils.mkdir(repos_base)

    repos = list()

    for url in repo_urls:
        repo_name = url.split('/')[-1]
        target = os.path.join(repos_base, repo_name)
        try:
            repo = utils.clone(url, target, bare=True)
        except OSError:
            repo = dulwich.repo.Repo(target)

        repos.append(repo)

    return repos


def create_queries(project):
    corpus_fname_base = project.full_path + 'Queries'
    corpus_fname = corpus_fname_base + '.mallet.gz'
    dict_fname = corpus_fname_base + '.dict.gz'

    if not os.path.exists(corpus_fname):
        pp = GeneralCorpus(lazy_dict=True)
        id2word = Dictionary()

        ids = load_ids(project)

        queries = list()
        for id in ids:
            with open(os.path.join(project.data_path, 'queries',
                                    'short', '%s.txt' % id)) as f:
                short = f.read()

            with open(os.path.join(project.data_path, 'queries',
                                    'long', '%s.txt' % id)) as f:
                long = f.read()

            text = ' '.join([short, long])
            text = pp.preprocess(text)

            # this step will remove any words not found in the dictionary
            bow = id2word.doc2bow(text, allow_update=True)

            queries.append((bow, (id, 'query')))

        # write the corpus and dictionary to disk. this will take awhile.
        MalletCorpus.serialize(corpus_fname, queries, id2word=id2word,
                               metadata=True)

    # re-open the compressed versions of the dictionary and corpus
    id2word = None
    if os.path.exists(dict_fname):
        id2word = Dictionary.load(dict_fname)

    corpus = MalletCorpus(corpus_fname, id2word=id2word)

    return corpus

def create_model(project, corpus, id2word, Kind, name, force=False):
    numpy.random.seed(project.random_seed_value)

    if Kind is LdaModel and corpus is None:
        project.model_config.update({
            'algorithm': 'online', # special
            'alpha': None,
            'eta': None,
            'chunksize': 1,
            'passes': 10,
            'eval_every': 0,
            'decay': 2.0,
            'offset': 1,
        })
        if 'max_bound_iterations' in project.model_config:
            del project.model_config['max_bound_iterations']

        p = project._replace(model_config_string='-'.join(["%s"] + [unicode(v) for k, v in sorted(project.model_config.items())]))
    else:
        p = project

    model_fname = p.full_path + name.lower() + '-' + p.model_config_string
    model_fname += '.' + p.model + '.gz'

    if not os.path.exists(model_fname) or p.force or force:
        params = dict(p.model_config) # make copy of config
        params['corpus'] = corpus
        params['id2word'] = id2word

        model = Kind(**params)

        if corpus and project.save_models:
            model.save(model_fname)
    else:
        model = Kind.load(model_fname)

    return model, model_fname


def create_mallet_model(project, corpus, name, use_level=True):
    model_fname = project.full_path + name + str(project.num_topics)
    if use_level:
        model_fname += project.level

    model_fname += '.malletlda.gz'

    if not os.path.exists(model_fname):
        model = LdaMallet('./lib/mallet-2.0.7/bin/mallet',
                          corpus=corpus,
                          id2word=corpus.id2word,
                          optimize_interval=10,
                          num_topics=project.num_topics)

        if project.save_models:
            model.save(model_fname)
    else:
        model = LdaMallet.load(model_fname)

    return model


def create_corpus(project, repos, Kind, use_level=True, forced_ref=None):
    names = [Kind.__name__]
    args = {
        'project': project,
        'lazy_dict': True,
    }

    if use_level:
        names.append(project.level)

    if Kind is ChangesetCorpus:
        names.append(project.changeset_config_string)
        args.update(project.changeset_config)

    if forced_ref:
        names.append(forced_ref[:8])

    corpus_fname_base = project.full_path + '-'.join(names)

    corpus_fname = corpus_fname_base + '.mallet.gz'
    dict_fname = corpus_fname_base + '.dict.gz'
    made_one = False

    if not os.path.exists(corpus_fname):
        combiner = CorpusCombiner()

        for repo in repos:
            try:
                if repo or forced_ref:
                    args.update({
                        'repo': repo,
                        'ref': forced_ref,
                    })
                corpus = Kind(**args)

            except KeyError:
                continue
            except TaserError as e:
                if repo == repos[-1] and not made_one:
                    raise e
                    # basically, if we are at the last repo and we STILL
                    # haven't sucessfully extracted a corpus, ring some bells
                else:
                    # otherwise, keep trying. winners never quit.
                    continue

            combiner.add(corpus)
            made_one = True

        # write the corpus and dictionary to disk. this will take awhile.
        combiner.metadata = True
        MalletCorpus.serialize(corpus_fname, combiner, id2word=combiner.id2word,
                               metadata=True)
        combiner.metadata = False

        # write out the dictionary
        combiner.id2word.save(dict_fname)

    # re-open the compressed versions of the dictionary and corpus
    id2word = None
    if os.path.exists(dict_fname):
        id2word = Dictionary.load(dict_fname)

    corpus = MalletCorpus(corpus_fname, id2word=id2word)

    return corpus


def create_release_corpus(project, repos, changesets=None, ref=None):
    if project.level == 'file':
        RC = ReleaseCorpus
        SC = SnapshotCorpus
    else:
        RC = TaserReleaseCorpus
        SC = TaserSnapshotCorpus

    return create_corpus(project, repos, SC, forced_ref=ref)

    # not using this just yet
    if forced_ref:
        return create_corpus(project, repos, SC, forced_ref=ref)
    else:
        try:
            return create_corpus(project, [None], RC)
        except TaserError:
            return create_corpus(project, repos, SC, forced_ref=ref)

def append_perplexity(project, perplexity, kind):
    path = os.path.join(project.data_path, kind + '-' + project.level + ".csv")
    logger.info("writing perplexity: %s", ",".join([unicode(k) for k, v in sorted(project.model_config.items())] + ["random_seed_value", "perplexity"] + [unicode(k) for k, v in sorted(project.changeset_config.items())]))

    if not os.path.exists(path):
        with open(path, "wt") as f:
            writer = csv.writer(f)
            writer.writerow([unicode(k) for k, v in sorted(project.model_config.items())] + ["random_seed_value", "perplexity"] + [unicode(k) for k, v in sorted(project.changeset_config.items())])

    with open(path, "at") as f:
        writer = csv.writer(f)
        writer.writerow([unicode(v) for k, v in sorted(project.model_config.items())] + [project.random_seed_value, unicode(perplexity)] + [unicode(v) for k, v in sorted(project.changeset_config.items())])
