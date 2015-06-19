# Study

In this section we describe the design of a study in which we compare our
activity-based approach with a location-based approach.

## Evaluation

## Subject Systems and Dataset


The 9 subjects of our study vary in size and application domain.
BookKeeper is a distributed logging service\footnote{\url{http://zookeeper.apache.org/bookkeeper/}}.
Derby is a relational database management system\footnote{\url{http://db.apache.org/derby/}}.
Lucene is an information retrieval library\footnote{\url{http://lucene.apache.org/core/}}.
Mahout is a tool for scalable machine learning\footnote{\url{https://mahout.apache.org/}}.
OpenJPA is object/relational mapping tool\footnote{\url{http://openjpa.apache.org/}}.
Pig is a platform for analyzing large datasets\footnote{\url{http://pig.apache.org/}}.
Solr is a search platform\footnote{\url{http://lucene.apache.org/solr/}}.
Tika is a toolkit for extracting metadata and text from various types of files\footnote{\url{http://tika.apache.org/}}.
ZooKeeper is a tool that works as a coordination service to help build distributed applications\footnote{\url{http://zookeeper.apache.org/bookkeeper/}}.
However, the attentive reader will notice that all of the systems are projects
supported by the Apache Software Foundation.
We chose these systems for our preliminary work because developers use
descriptive commit messages that allow for easy traceability linking to issue
reports. Further, Apache provides Git mirrors for all projects using
Subversion.

To build our dataset we mine the Git repository for information about each
commit: the committer, message, and files changed. We use the files changed
information during the location-based approach. Using the message, we extract
the traceability links to issues in JIRA with the regular expression: `%s-\d+`,
where `%s` is the project's name (e.g., BookKeeper). This matches for
JIRA-based issue identifiers, such as `BOOKKEEPER-439` or `TIKA-42`.

From the issue reports, we extract the version the issue marked as fixed in. If
the issue does not list a fixed version, it is ignored. We also extract the
title and description of the issue. We then construct a map between the
developers that committed changes linked to the issue report. We use this map
as our goldset for identifying the developer most apt to handle the issue
report.


## Methodology

For a location-based approach, the process is straightforward, but requires two
separate steps. First, we need to build a topic model for searching over the
source code snapshot. Once we determine the relevant documents, we need to
determine which developer is the *owner* of those documents. To accomplish
this, we turn to the source code history. Following @Bird-etal_2011, we
identify which developer has changed the documents the most. This implies that
the snapshot approach is *dependent* on the performance of the snapshot-based
FLT.

For our proposed activity-based approach, the approach will not necessarily be
dependent on an FLT. First, we train a model of the changeset corpus using
batch training.  Second, we infer an index of topic distributions with the
developer profiles.  Note that we *do not* infer topic distributions with the
changeset corpus used to train the model. Finally, for each query in the
dataset, we infer the query's topic distribution and rank each entity in the
developer profiles index with pairwise comparisons.

## Setting

## Data Collection and Analysis

To evaluate the performance of a topic-modeling-based FLT we cannot use
measures such as precision and recall. This is because the FLT creates the
rankings pairwise, causing every entity to appear in the rankings. Again,
@Poshyvanyk-etal_2007 define an effectiveness measure for topic-modeling-based
FLTs, which is usable for a DIT. The effectiveness measure is the rank
of the first relevant document and represents the number of developers the
triager would have to assign before choosing the right developer. The
effectiveness measure allows evaluating the FLT by using the mean reciprocal
rank (MRR). We can also look at only the top-k recommendations in the list,
giving us the measures of precision@k and recall@k.

To answer our research question, we run the experiment on the snapshot and
changeset corpora as outlined in Section \ref{methodology}. We then calculate
the MRR between the two sets of effectiveness measures. We use the Wilcoxon
signed-rank test with Holm correction to determine the statistical significance
of the difference between the two rankings.

## Results and Discussion


\input{tables/rq1_lda.tex}
