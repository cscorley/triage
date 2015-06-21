# Preliminary Study

In this section we describe the design and results of a preliminary study in
which we compare our activity-based approach with a location-based approach.

## Subject Systems and Dataset

The 7 subjects of our study vary in size and application domain.
BookKeeper is a distributed logging service\footnote{\url{http://zookeeper.apache.org/bookkeeper/}}.
Derby is a relational database management system\footnote{\url{http://db.apache.org/derby/}}.
<!--Lucene is an information retrieval
library\footnote{\url{http://lucene.apache.org/core/}}.-->
Mahout is a tool for scalable machine learning\footnote{\url{https://mahout.apache.org/}}.
OpenJPA is object/relational mapping tool\footnote{\url{http://openjpa.apache.org/}}.
Pig is a platform for analyzing large datasets\footnote{\url{http://pig.apache.org/}}.
<!--Solr is a search
platform\footnote{\url{http://lucene.apache.org/solr/}}.-->
Tika is a toolkit for extracting metadata and text from various types of files\footnote{\url{http://tika.apache.org/}}.
ZooKeeper is a tool that works as a coordination service to help build distributed applications\footnote{\url{http://zookeeper.apache.org/bookkeeper/}}.
Table \ref{table:subjects} summarizes the sizes of each system's corpora and
dataset.

\begin{table}
\centering
\caption{Subject system corpora and dataset sizes}
\label{table:subjects}
\input{tables/subjects}
\end{table}

We chose these systems for our preliminary work because developers use
descriptive commit messages that allow for easy traceability linking to issue
reports. Further, all projects use JIRA as an issue tracker, which has been
found to encourage more accurate linking [@Bissyande-etal_2013].

To build our dataset we mine the Git repository for information about each
commit: the committer, message, and files changed. We use the files changed
information during the location-based approach. Using the message, we extract
the traceability links to issues in JIRA with the regular expression: `%s-\d+`,
where `%s` is the project's name (e.g., BookKeeper). This matches for
JIRA-based issue identifiers, such as `BOOKKEEPER-439` or `TIKA-42`.

From the issue reports, we extract the version the issue marked as fixed in. We
ignore issues that are not marked with a fixed version. We also extract the
title and description of the issue. We then construct a map between the
developers that committed changes linked to the issue report. We use this map
as our goldset for identifying the developer most apt to handle the issue
report.

## Methodology

For a location-based approach, the process is straightforward, but requires two
separate steps. First, we build a topic model for searching over the source
code snapshot and query the model for files related to the issue report. Once
we determine the relevant documents, we need to determine which developer is
the *owner* of those documents. To accomplish this, we turn to the source code
history. Following @Bird-etal_2011, we identify which developer has changed the
documents the most. This implies that the location-based approach is
*dependent* on the performance of the FLT.

For our proposed activity-based approach, the approach will not necessarily be
dependent on an FLT. First, we train a model of the changeset corpus using
batch training.  Second, we infer an index of topic distributions with the
developer profiles.  Note that we *do not* infer topic distributions with the
changeset corpus used to train the model. Finally, for each query in the
dataset, we infer the query's topic distribution and rank each entity in the
developer profiles index with pairwise comparisons.

## Setting

The left side of Figure \ref{fig:changeset-triage} shows our document
extraction process. We implemented our document extractor in Python v2.7 using
the Dulwich library^[<http://www.samba.org/~jelmer/dulwich/>] for interacting
with the source code repository. We extract documents from both a snapshot of
the repository at a tagged snapshot and each commit reachable from that tag's
commit. We use the same preprocessing steps on all extracted documents.

For our document extraction from a snapshot, we simply use each text file in
the source code repository as documents. To extract text from the changesets,
we use `git diff` between two commits. In our changeset text extractor, we
extract all text related to the change, e.g., context, removed, and added
lines; we ignore metadata lines. Note that we do not consider where the text
originates from, only that it is text changed by the commit.

After extracting tokens, we split the tokens based on camel case, underscores,
and non-letters. We only keep the split tokens; we discard original tokens.
We normalize to lower case before filtering non-letters, English stop
words [@Fox_1992], Java keywords, and words shorter than three characters
long. We do not stem words.

We implemented our modeling using the Python library Gensim
[@Rehurek-Sojk_2010], version 0.11.1. We use the same configurations on each
subject system.  We do not try to adjust parameters between the different
systems to attempt to find a better, or best, solution; rather, we leave them
the same to reduce confounding variables.  We do realize that this may lead to
topic models that may not be best-suited for feature location on a particular
subject system. However, this constraint gives us confidence that the
measurements collected are fair and that the results are not influenced by
selective parameter tweaking. Again, our goal is to show the performance of the
activity-based DIT against location-based DIT under the same conditions.

Gensim's LDA implementation originates from the online LDA by @Hoffman-etal_2010 and
uses variational inference instead of a collapsed Gibbs sampler.  Unlike Gibbs
sampling, to ensure that the model converges for each document, we
allow LDA to see each mini-batch $5$ times by setting Gensim's initialization
parameter `passes` to this value and allowing the inference step $1000$
iterations over a document.  We set the following LDA parameters for all
systems: $500$ topics ($K$), a symmetric $\alpha=1/K$, and a symmetric
$\eta=1/K$.  These are default values for $\alpha$ and $\eta$ in Gensim.

## Data Collection and Analysis

To evaluate the performance of a topic-modeling-based DIT or FLT we cannot use
measures such as precision and recall. This is because the techniques create
rankings pairwise, causing every document to appear in the rankings.
@Poshyvanyk-etal_2007 define an effectiveness measure for topic-modeling-based
FLTs, which is usable for a DIT. Here, the effectiveness measure is the rank of
the first relevant document and represents the number of developers the triager
would have to assign before choosing the right developer. The effectiveness
measure allows evaluating the DIT by using the mean reciprocal rank (MRR)
[@Voorhees_1999]: $MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{e_i}$
where $Q$ is the set of queries and $e_i$ is the effectiveness measure for some
query $Q_i$.

We run the experiment on the for the activity- and location-based approaches as
outlined in Section \ref{methodology}. We then calculate the MRR between the
two sets of effectiveness measures. We use the Wilcoxon signed-rank test with
Holm correction to determine the statistical significance of the difference
between the two rankings.

## Results

\input{tables/rq1_lda.tex}

Table \ref{table:rq1:file:lda} shows the MRR and Wilcoxon signed-rank $p$-value
for each subject system. We can see that for all systems with the exception of
Pig, that the activity-based approach outperforms the location-based approach.
Of those 6 systems in favor of the activity-based approach, 5 are statistically
significant with $p < 0.01$. Overall, the activity-based approach performs
slightly better with statistical significance.


<!--
The results of Pig deserve some qualitative discussion. It could be possible
that the quality of the queries differs from other systems. However, the
average issue report in Pig contains 79 words in total. Systems like Tika and
ZooKeeper share that characteristic, respectively with 72 and 79 words on
average. It could be that the developers of Pig have stronger ownership over
files and share a common vocabulary than other systems. However, we cannot
confirm this hypothesis without further experimentation.
-->
