# Modeling Changeset Topics

\begin{figure*}
\centering
\includegraphics[width=0.9\textwidth]{figures/changeset-triage.pdf}
\caption{Developer identification using changesets}
\label{fig:changeset-triage}
\end{figure*}

<!--
![Developer identification using changesets\label{fig:changeset-triage}](changeset-triage.pdf)
-->

Our activity-based approach relies on modeling changeset topics
[@Corley-etal_2014], a technique that has shown useful for feature location
[@Corley-etal_2015]. We choose to train the model on changesets, rather than
another source of information, because they also represent what we are
primarily interested in: language being used by committers.  While a snapshot
corpus has documents that represent a program, a changeset corpus has documents
that represent programming.

The changeset approach requires two types of document extraction: one for the
every changeset in the source code history and a developer profile of the words
each individual developer used in those changesets. The left side of Figure
\ref{fig:changeset-triage} illustrates the dual-document extraction approach.

The document extraction process for the developer corpus is straightforward.
Following @Matter-etal_2009, each developer has their own document consisting
of an aggregation of changesets they have committed to the source code
repository. That is, a document representing a developer consists of only words
that developer has changed.

The right side of Figure \ref{fig:changeset-triage} illustrates the retrieval
process. The key intuition to our methodology is that a topic model such as LDA
can infer *any* document's topic proportions regardless of the documents used
to train the model.  In our approach, the documents seen during training are
changesets and the unseen documents are the developer profiles.

Hence, we train a topic model on the changeset corpus and use the model to
index the developer profiles.  Note that we never construct an index of the
changeset documents used for training.  In our approach, we only use the
changesets to continuously update the topic model and only use the developer
profiles for indexing. Also note that since we do not rely on source code at
any point in this approach, it is completely language-agnostic.
