import csv
from collections import defaultdict, namedtuple


def get_project_name(filename):
    return filename.lower().split('/')[1]


FullHistory = namedtuple('FullHistory', 'filename project_name sha_paths')


def get_full_history(filename):
    """Reads a 'changes-file-full.csv' and returns a FullHistory object."""
    project_name = get_project_name(filename)
    sha_paths = defaultdict(set)
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            sha = row[0]
            path = row[2]
            sha_paths[sha].add(path)
    return FullHistory(filename, project_name, sha_paths)


Goldset = namedtuple('Goldset', 'filename project_name issue_paths')


def get_goldset(filename):
    """Reads a 'changes-file-goldset.csv' and returns a Goldset object."""
    project_name = get_project_name(filename)
    issue_paths = defaultdict(set)
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            path = row[3]
            if path.endswith('.java'):
                for issue in row[1].split(';'):
                    issue_paths[issue].add(path)
    return Goldset(filename, project_name, issue_paths)


def get_goldset_issues(goldset):
    return set(goldset.issue_paths.keys())


def get_goldset_paths(goldset):
    goldset_paths = set()
    for paths in goldset.issue_paths.values():
        for path in paths:
            goldset_paths.add(path)
    return goldset_paths


def get_internal_change_proneness(full_history):
    """Returns a dict that maps a Java file path to its internal change proneness.

    See doi>10.1145/3084226.3084239 for discussion of internal vs. external.
    """
    path_change_counts = defaultdict(int)
    for paths in full_history.sha_paths.values():
        for path in paths:
            if path.endswith('.java'):
                path_change_counts[path] += 1
    sha_count = len(full_history.sha_paths)
    return {path : path_change_count / sha_count for path, path_change_count in path_change_counts.items()}


def get_goldset_internal_change_proneness(path_icp, goldset):
    """Returns a list of internal change proneness values for the goldset Java file paths."""
    goldset_paths = get_goldset_paths(goldset)
    goldset_icp = list()
    for path, icp in path_icp.items():
        if path in goldset_paths:
            goldset_icp.append(icp)
    return goldset_icp

