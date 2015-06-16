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

The document extraction process for the changesets remains the same as covered
in Section \ref{modeling-changeset-topics}. The document extraction process for the
developer corpus is straightforward. Following @Matter-etal_2009, each
developer will have their own document consisting of each changeset they have
committed to the source code repository. That is, a developer document consists
of only words they have changed. There may be weighting schemes to
this [@Shokripour-etal_2013], such as only considering words which they have
added or removed, while ignoring context words.

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

We can follow the same process used in Section \ref{flt-approach} for a
historical simulation of how a changeset-based DIT would perform in a realistic
scenario.

## Why changesets?

We choose to train the model on changesets, rather than another source of
information, because they also represent what we are primarily interested in:
program features.  A single changeset gives us a view of an addition, removal,
or modification of a single feature.  A developer can to some degree comprehend
what a changeset accomplishes by examining it, much like examining a source
file.

While a snapshot corpus has documents that represent a program, a changeset
corpus has documents that represent programming.  If we consider every
changeset affecting a particular source code entity, then we gain a
sliding-window view of that source code entity over time and the contexts those
changes took place within. Here, the summation of all changes affecting a class
over its lifetime would approximate the same words in its current version.

Changeset topic modeling is akin to summarizing code snippets with machine
learning [@Ying-Robillard_2013], where in our case a changeset gives a
snippet-like view of the code required to complete a task. For example, in
Figure \ref{fig:diff}, we can see the entire method affected by the changeset.

Additionally, @Vasa-etal_2007 observe that code rarely changes as software
evolves. The implication is that the topic modeler will see changesets
containing the same source code entity only a few times, perhaps only once.
Since topic modeling a snapshot only sees an entity once, topic modeling a
changeset can miss no information.

Using changesets also implies that the topic model may gain some noisy
information from these additional documents, especially removals.  However,
@Vasa-etal_2007 also observe that code is less likely to be removed than it is
to be changed. This implies that the noisy information would likely remain in
both snapshot-based models and changeset-based models.

Indeed, it appears desirable to remove changesets from the model that are old
and no longer relevant. There would be no need for this because online LDA
already contains features for increasing the influence newer documents have on
the model, thereby decaying the affect of the older documents on the model.


