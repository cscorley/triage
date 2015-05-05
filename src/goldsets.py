#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import csv
from subprocess import Popen, PIPE
import errno
from StringIO import StringIO

import whatthepatch as wtp
import dulwich
import dulwich.diff_tree
import dulwich.patch
from lxml import etree
from gensim.utils import to_unicode

import main
from corpora import ChangesetCorpus
from blocks import Block, File

def build_goldset(project):
    repos = main.load_repos(project)
    corpus = ChangesetCorpus(project=project, repo=repos[0], lazy_dict=True)
    repo = corpus.repo

    for commit, parent, patch, changes in walk_changes(repo):
        diffs = wtp.parse_patch(patch)
        for diff in diffs:
            removed = list()
            added = list()
            if not (diff.header.old_path.endswith(".java") or
                    diff.header.new_path.endswith(".java")):
                continue

            for r, a, text in diff.changes:
                if r:
                    removed.append(r)
                if a:
                    added.append(a)
            print(diff)
            print(removed)
            print(added)

            if diff.header.old_path != "/dev/null":
                get_blocks(repo, changes.old, removed)

            if diff.header.new_path != "/dev/null":
                get_blocks(repo, changes.new, added)

            return



def walk_changes(repo):
    """ Returns one file change at a time, not the entire diff.

    """

    for walk_entry in repo.get_walker():
        commit = walk_entry.commit

        # initial revision, has no parent
        if len(commit.parents) == 0:
            for changes in dulwich.diff_tree.tree_changes(
                    repo.object_store, None, commit.tree
            ):
                diff = get_diff(repo, changes)
                yield commit.id, None, diff, changes

        for parent in commit.parents:
            # do I need to know the parent id?

            for changes in dulwich.diff_tree.tree_changes(
                repo.object_store, repo[parent].tree, commit.tree
            ):
                print(changes)
                diff = get_diff(repo, changes)
                yield commit.id, parent, diff, changes

def get_diff(repo, changeset):
    patch_file = StringIO()
    dulwich.patch.write_object_diff(patch_file,
                                    repo.object_store,
                                    changeset.old, changeset.new)
    return patch_file.getvalue()

def get_blocks(repo, tree, line_nums):
    print(tree.sha, line_nums)
    cmd = "java -cp ./lib -jar ./lib/srcMLOLOL.jar Java".split()
    print("parsing java")
    xml = pipe(str(repo[tree.sha]), cmd)
    xml = xml[len('<?xml version="1.0" encoding="UTF-8" standalone="no"?>'):]
    print(xml)
    print("parsing xml")

    tree = etree.fromstring(xml)
    for method in tree.iterfind(".//MethodDeclaration"):
        print(method.getparent())


def pipe(text, cmd):
    p = Popen(cmd, stdin=PIPE, stdout=PIPE)
    try:
        p.stdin.write(text)
    except IOError as e:
        if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
            # Stop loop on "Invalid pipe" or "Invalid argument".
            # No sense in continuing with broken pipe.
            pass
        else:
            # Raise any other error.
            raise

    p.stdin.close()
    return p.stdout.read().decode()
