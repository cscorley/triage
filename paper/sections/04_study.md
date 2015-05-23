# Study

## Evaluation

In this section we describe the design of a case study in which we
compare topic models trained on changesets to those trained on snapshots.
For this work, we pose the following research questions:

RQ1
:   Is a changeset-based DIT as accurate as a snapshot-based DIT?

RQ2
:   Does the accuracy of a changeset-based DIT fluctuate as a project evolves?

## Methodology

For snapshots, the process is straightforward, but requires two separate steps.
First, we need to build a topic model for searching over the source code
snapshot (i.e., just like in the FLT evaluation). Once we determine the
relevant documents, we need to determine which developer is the *owner* of
those documents. To accomplish this, we turn to the source code history.
Following @Bird-etal_2011, we identify which developer has changed the
documents the most. This implies that the snapshot approach is *dependent* on
the performance of the snapshot-based FLT.

For changesets, the approach will not necessarily be dependent on an FLT. We
can utilize the same approach as we did for the FLT evaluation. First, we train
a model of the changeset corpus using batch training.  Second, we infer an
index of topic distributions with the developer profiles.  Note that we *do
not* infer topic distributions with the changeset corpus used to train the
model.  Finally, for each query in the dataset, we infer the query's topic
distribution and rank each entity in the developer profiles index with pairwise
comparisons.

For the historical simulation, we take a slightly different approach.  We first
determine which commits relate to each query (or issue) and partition
mini-batches out of the changesets.  We then proceed by initializing a model
for online training.  Using each mini-batch, or partition, we update the model.
Then, we infer an index of topic distributions with the developer profiles at
the commit the partition ends on.  We also obtain a topic distribution for each
query related to the commit.  For each query, we infer the query's topic
distribution and rank each entity in the developer index with pairwise
comparisons. Finally, we continue by updating the model with the next
mini-batch.

## Subject Systems

There are two publicly-available and recently published datasets usable for
this study. Between these two datasets are over 415 defects and features from 5
open source Java projects. Choosing a publicly-available dataset allows us to
set this work in context of work completed by other researchers.

Table \ref{table:dit-datasets} summarizes the subject systems from the
datasets. The first is a dataset of 5 software systems by @Kagdi-etal_2012. The
second is a dataset of 3 software systems by @Linares-Vasquez-etal_2012. Both
datasets were automatically extracted from changesets that relate to the
queries (issue reports).


\input{tables/subjects.tex}


ArgoUML is a UML diagramming tool^[<http://argouml.tigris.org/>].
Eclipse is a general purpose IDE^[<https://www.eclipse.org/>].
jEdit is a text editor^[<http://www.jedit.org/>].
KOffice is a office productivity suite^[<http://www.kde.org/applications/office>].
muCommander is a cross-platform file manager^[<http://www.mucommander.com/>].

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

To answer RQ1, we run the experiment on the snapshot and changeset corpora as
outlined in Section \ref{flt-methodology}. We then calculate the MRR between
the two sets of effectiveness measures. We use the Wilcoxon signed-rank test
with Holm correction to determine the statistical significance of the
difference between the two rankings. To answer RQ2, we run the historical
simulation as outlined in Section \ref{flt-methodology} and compare it to the
results of batch changesets from RQ1. Again, we calculate the MRR and use the
Wilcoxon signed-rank test.

