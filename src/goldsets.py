#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import csv
from subprocess import Popen, PIPE
import errno
from StringIO import StringIO
from xml.sax.saxutils import unescape

import whatthepatch as wtp
import dulwich
import dulwich.diff_tree
import dulwich.patch
import re
from lxml import etree
from gensim.utils import to_unicode

import main
from corpora import ChangesetCorpus
from blocks import Block, File

def build_goldset(project):
    repos = main.load_repos(project)
    corpus = ChangesetCorpus(project=project, repo=repos[0], lazy_dict=True)
    repo = corpus.repo

    matcher = re.compile("%s-(\d+)" % project.name, flags=re.IGNORECASE)

    goldsets = dict()
    commits = dict()

    for commit, parent, patch, changes in walk_changes(repo):
        res = matcher.findall(commit.message)

        if res:
            diffs = wtp.parse_patch(patch)
            for removed, added in parse_diff_changes(project, repo, changes, diffs):
                commits[commit.id] = set(res)

                for gid in res:
                    if gid not in goldsets:
                        goldsets[gid] = set()

                    goldsets[gid].update(removed)
                    goldsets[gid].update(added)

    with open(os.path.join(project.full_path, 'ids.txt'), 'w') as f:
        for gid in goldsets:
            f.write(gid + '\n')

    for gid, goldset in goldsets:
        with open(os.path.join(project.full_path, 'goldsets', project.level,
                                gid + '.txt'), 'w') as f:

            for entity in goldset:
                f.write(entity.full_name + '\n')


def parse_diff_changes(project, repo, changes, diffs):
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

        removed_blocks = []
        if diff.header.old_path != "/dev/null":
            removed_blocks = get_blocks(project, repo, changes.old, removed)

        added_blocks = []
        if diff.header.new_path != "/dev/null":
            added_blocks = get_blocks(project, repo, changes.new, added)

        yield removed_blocks, added_blocks



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
                yield commit, None, diff, changes

        for parent in commit.parents:
            # do I need to know the parent id?

            for changes in dulwich.diff_tree.tree_changes(
                repo.object_store, repo[parent].tree, commit.tree
            ):
                diff = get_diff(repo, changes)
                yield commit, parent, diff, changes

def get_diff(repo, changeset):
    patch_file = StringIO()
    dulwich.patch.write_object_diff(patch_file,
                                    repo.object_store,
                                    changeset.old, changeset.new)
    return patch_file.getvalue()

def get_blocks(project, repo, gittree, line_nums):
    cmd = "java -cp ./lib -jar ./lib/srcMLOLOL.jar Java".split()
    ftext = repo[gittree.sha].as_raw_string()
    xml = pipe(ftext, cmd)
    xml = xml[len('<?xml version="1.0" encoding="UTF-8" standalone="no"?>'):]

    # need huge_tree since the depth gets kinda crazy
    p = etree.XMLParser(huge_tree=True)
    tree = etree.fromstring(xml, parser=p)

    package_name = ''
    pkg = list()
    package = tree.find(".//PackageDeclaration")
    if package is not None:
        qn = package.find(".//QualifiedName")
        for child in qn:
            if child.tag == "CommonToken" and child.attrib["name"] == "Identifier":
                pkg.append(child.text)
        package_name = '.'.join(pkg)

    types = ['ClassDeclaration', 'EnumDeclaration', 'InterfaceDeclaration'
             'AnnotationTypeDeclaration']

    # these are the method-like decls that come from the 4 'types' in the grammar
    methodTypes = ["MethodDeclaration", "GenericMethodDeclaration",
                   "ConstructorDeclaration", "GenericConstructorDeclaration",
                   "InterfaceMethodDeclaration", "InterfaceGenericMethodDeclaration",
                   "AnnotationMethodRest"]

    blocks = list()

    if project.level == 'class':
        findtype = types
    elif project.level == 'method':
        findtype = methodTypes

    for t in findtype:
        for elem in tree.iterfind(".//" + t):
            # in all types, there is a keyword marking the type
            # with the identifier following immediately
            params = list()
            elem_name = None
            for child in elem:
                if elem_name is None and child.tag == "CommonToken" and child.attrib["name"] == "Identifier":
                    elem_name = child.text

                if child.tag == "FormalParameters":
                    for param in child.findall(".//Type"):
                        params.append(''.join(ct.text for ct in param.findall(".//CommonToken")))

            if elem_name is None:
                elem_name = "$" + t + "$"

            start_line = int(elem.attrib["start_line"])
            end_line = int(elem.attrib["end_line"])

            # TODO, find the body, get actual start_line
            body_line = start_line

            supers = list()
            parent = elem.getparent()
            while parent != None:
                if parent.tag == 'classCreatorRest':
                    # anonymous class time!
                    supers.append("$classCreatorRest$")
                else:
                    for child in parent:
                        if child.tag == "CommonToken" and child.attrib["name"] == "Identifier":
                            supers.append(child.text)
                            break
                parent = parent.getparent()

            if package_name:
                supers.append(package_name)

            if project.level == 'method':
                elem_name += '(' + ','.join(params) + ')'

            elem_name = unescape(elem_name)
            supers = [unescape(s) for s in supers]

            block = Block(t, elem_name, start_line, body_line, end_line,
                          super_block_name=u'.'.join(reversed(supers)))

            blocks.append(block)

    # figure out which methods changed
    changed = list()
    for method in blocks:
        keep = False
        for line_num in line_nums:
            if line_num in method.line_range:
                keep = True
        if keep:
            changed.append(method)

    # for c in changed:
    #    print(c.full_name)

    # shits the bed on unicode, but above works lol
    # print(changed)

    return changed


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
    return p.stdout.read().decode('UTF-8')
