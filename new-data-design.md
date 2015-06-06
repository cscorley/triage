- <project-name>/
    - issues.xml.gz: compressed xml downloaded from issue tracker
    - git.tar.xz: compressed .git/ of the repository used
    - git2issue.csv: contains a (sha,ref,issue) mapping for the entire history

                sha: commit sha
                tag: closest tag or head from which the commit is reachable.
                     this is meant to represent which version the commit 
                     belongs to.
                issue: issue id extracted from the commit message

    - queries/
        - short/
            - <id>.txt: UTF-8 of issue summary/title as extracted from the XML
        - long/
            - <id>.txt: UTF-8 of issue description as extracted from the XML
    - changes-<level>.log: contains changed source code entities in the format
      of `git log --name-status --pretty=raw`. When `<level>=file`, the output
      should be the same as actually running the command. When `<level>=class`
      or `<level>=method`, then the output will have the parsed entity names
      instead of file paths.
    - <version>/
        - <generated>: files generated. models, corpora, and results.
