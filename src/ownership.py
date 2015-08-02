#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
logger = logging.getLogger('cfl.goldsets')

import codecs
import csv
import os
import os.path

from gensim.utils import to_unicode, smart_open, to_utf8
import dulwich
import dulwich.diff_tree
import dulwich.patch
import re

from blocks import Block, File
from corpora import GitCorpus
import common
import utils

def build_ownership(project, repos):
    if os.path.exists(os.path.join(project.full_path, 'ownership.csv.gz')) and not project.force:
        return read_ownership(project)

    print(project)
    repos = common.load_repos(project)

    # use the gitcorpus cause it'll do all the dulwich setup stuff for us
    # also i am lazy, so...
    for r in repos:
        corpus = GitCorpus(project=project, repo=r, lazy_dict=True)
        repo = corpus.repo

        ownership = dict()

        for commit, parent, change in walk_changes(project, corpus):
            committer = to_unicode(commit.committer.replace(" ", "_"))

            path = change.old.path
            if path is None or path == '/dev/null':
                path = change.new.path

            path = to_unicode(path)

            if path not in ownership:
                ownership[path] = dict()

            if committer not in ownership[path]:
                ownership[path][committer] = 0

            ownership[path][committer] += 1

    with smart_open(os.path.join(project.full_path, 'ownership.csv.gz'), 'w') as f:
        writer = csv.writer(f)

        for path, committers in ownership.items():
            for committer, count in committers.items():
                writer.writerow([to_utf8(path),to_utf8(committer),count])

    return ownership

def read_ownership(project):
    ownership = dict()
    with smart_open(os.path.join(project.full_path, 'ownership.csv.gz')) as f:
        reader = csv.reader(f)
        for path, committer, count in reader:
            committer = to_unicode(committer.replace(" ", "_"))
            path = to_unicode(path)

            if path not in ownership:
                ownership[path] = dict()

            ownership[path][committer] = int(count)

    return ownership

def walk_changes(project, corpus):
    """ Returns one file change at a time, not the entire diff.

    """
    repo = corpus.repo

    for walk_entry in repo.get_walker(include=[corpus.ref_commit_sha]):
        commit = walk_entry.commit

        # initial revision, has no parent
        if len(commit.parents) == 0:
            for change in dulwich.diff_tree.tree_changes(
                    repo.object_store, None, commit.tree
            ):
                yield commit, None, change

        for parent in commit.parents:
            # do I need to know the parent id?

            for change in dulwich.diff_tree.tree_changes(
                repo.object_store, repo[parent].tree, commit.tree
            ):
                yield commit, parent, change
