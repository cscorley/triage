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

The changeset approach requires two types of document extraction: one for the
every changeset in the source code history and a developer profile of the words
each individual developer used in those changesets. The left side of Figure
\ref{fig:changeset-triage} illustrates the dual-document extraction approach.


The document extraction process for the developer corpus is straightforward.
Following @Matter-etal_2009, each developer will have their own document
consisting of an aggregation of changesets they have committed to the source
code repository. That is, a developer document consists of only words they have
changed. There may be weighting schemes to this [@Shokripour-etal_2013], such
as only considering words which they have added or removed, while ignoring
context words.

The right side of Figure \ref{fig:changeset-triage} illustrates the retrieval
process. The key intuition to our methodology is that a topic model such as LDA
or LSI can infer *any* document's topic proportions regardless of the documents
used to train the model.  In our approach, the seen documents are changesets
and the unseen documents are the developer profiles.

Hence, we train a topic model on the changeset corpus and use the model to
index the developer profiles.  Note that we never construct an index of the
changeset documents used for training.  In our approach, we only use the
changesets to continuously update the topic model and only use the developer
profiles for indexing.

