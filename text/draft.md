<!-- 
Markdown Syntax: https://www.markdownguide.org/basic-syntax/
PyCharm and Markdown: https://www.jetbrains.com/help/pycharm/markdown.html 
Convert Markdown to LaTeX or PDF: https://pandoc.org/getting-started.html (PS C:\Users\Max\PycharmProjects\mas\text> 
pandoc .\draft.md -s --number-sections --bibliography biblio.bib --citeproc -o test.pdf)
Write a research paper in Markdown: https://opensource.com/article/18/9/pandoc-research-paper
-->

Machine indexing of institutional repositories: indexing Edoc with Annif and BARTOC FAST as proof of concept

# Introduction

## Outline

## Method

!! Say something to the effect that all data and code are available on GitHub.

## Tools and configuration 

### OpenRefine 

For data refinement I use OpenRefine (https://openrefine.org/). Data manipulation in OpenRefine is tracked: the manipulation history of some data can be exported as JSON file and then reproduced (on the same data on a different machine or on different data) by loading said file. I will supply a corresponding manipulation history whenever appropriate. Note that when using OpenRefine with larger files (and there are many such files in this project), the memory allocation to OpenRefine must be manually increased (see https://docs.openrefine.org/manual/installing/#increasing-memory-allocation for details).

# Prototype

In this chapter, the prototype for a machine indexing of Edoc is presented. The focus is primarily on practical 
implementation although care is taken to spell out design decisions in as much detail as is needed.

## Aim

Let us start by stating the aim of the prototype.  From a functional 
perspective, the prototype takes a subset of the data from Edoc as input and provides index terms for each item in this 
subset as output. In order to fulfill this aim we can distinguish a number of steps that need to be taken:

1. Understand the Edoc data.  
2. Select and construct a sample data set.
3. Use Annif to index the items in the sample data set.
4. Construct a gold standard from the keywords.
5. Assess the quality of the output based on the gold standard.

In the sections below, these steps will be discussed in detail.

## Edoc data

### Edoc

Edoc is the institutional repository of the University of Basel. It was conceived in 2009 as repository for 
electronic dissertations and grew in scope when the University of Basel adapted its first open access policy in 2013.
As per today Edoc contains roughly 68’000 items. 

Edoc runs on the EPrints 3 document management system [https://github.com/eprints/eprints]. 
!! Perhaps add description of how files are added to Edoc, see PDF in `/todo`.

### Data extraction

Even though Edoc is a public server, its database does not have a web-ready API. In addition, since Edoc is a production
server, its underlying database cannot be used directly on pain of disturbing the provided services. The data hence
needs to be extracted from Edoc in order to work with it. This could for example be achieved by cloning the database of
the server and running it on a local machine. However, this route was not available due to the limited resources of the
responsible co-workers. I thus employed a workaround: Edoc has a built-in advanced search tool where the results can be
exported. Even though it is not possible to extract all database items by default, only one of the many available search
fields has to be filled in. The complete database can hence be extracted by only filling in the `Date` field and using a
sufficiently permissive time period such as 1940 to 2020 since the oldest record in the database was published in 1942.
On January 21 2021 this query yielded 68'345 results. These results were then exported as a 326 MB JSON file
called `1942-2020.json`. `1942-2020.json` has two drawbacks. First, the maximum file size on GitHub is 100 MB. And
second, `1942-2020.json` is too big to be handled by standard editors requiring special editors such as Oxygen. For
these reasons `1942-2020.json` was split into smaller files that are easier handled and can be uploaded to GitHub. For
this
`_Utility.split_json` was used yielding 14 files of size 20 MB or less containing 5000 or fewer entries each. These
files are called `raw_master_x-y.json` (where x and y indicate the entries as given by `1942-2020.json`) and saved under
`/edoc/raw`.

### Data description and analysis

!! Text.

## Sample data set

In this section, I will explain how the sample data set is selected and constructed. By "selection" I mean the task of 
specifiying a subset of the Edoc data and by "construction" I mean the task of implementing this selection. 

### Selection

There are a number of constraints for selecting the sample data set pertaining to an items's text, evaluability and 
the data set's
scope.

The first constraint stems from Annif, the 
machine 
indexing framework that will be used. Put simply, machine indexing assigns index terms to a text based on training 
data. The training data consists of a set of texts, a vocabulary, and function from vocabulary to texts. In this 
context we mean by "text" a sequence of words in a natural language and by "vocabulary" a set of words. Intuitively, the training data 
consists of pairs of text and subject terms that meet some standard. The training data and the vocabulary are 
already supplied by Annif, we only need to provide a text for each item that we want to be assigned index terms. 
Therefore, we only select items with text. 

The second constraint is that we must be able to evaluate the quality of the index terms assigned by Annif to any 
item in the 
sample data set. 

The third and final constraint takes into account 
the possibility of having to extend the prototype to the complete Edoc data. On the one hand, the sample data set 
should be small enough to allow for easy handling and rapid iteration. On the other hand, the sample data set should 
not be trivial but reflect the quirks and inadequacies of the complete dataset. In other words, 
we are looking for an abstraction rather than an idealization in the sense of  [@Stokhof.2011]. 

### Construction

The first constraint is that each item in the sample data set needs to have a text. Intuitively, this text could 
consist of a title, an abstract, or even a full text, or any combination of the above. Similar to manual indexing, having 
more 
information (that is, longer texts) usually implies a higher indexing quality in machine indexing. However, this 
assumption needs to be confirmed empirically for the given machine indexing framework and data set. If indeed 
confirmed, it might be advisable only to index items that have a certain minimal text length. Therefore, in order to 
construct the sample data set, we require each item to have a non-empty value in the data fields `title`, `abstract`,
and `id_number` as proxy to retrieve a full text remotely. Note that even more context could be provided by taking 
into account other data fields such as `type`, `publication` or `department`. Especially the latter might be valuable 
when 
disambiguating homonymous or polysemous words. For example, consider item `https://edoc.unibas.ch/id/eprint/76510` 
which is titled "Blacking Out". Without further context, this title could refer (amongst others) to a physiological 
phenomenon, a 
sudden loss of electricity, or a measure taken in wartime. Knowing that the item was published by a 
researcher employed by the 
Faculty of Business and Economics (and not, say, by the Faculty of Medicine) gives us reason to exclude the first 
meaning. However, this idea cannot be implemented with the out 
of the box instance of Annif employed in this chapter (see [subsection "Machine indexing"](#machine-indexing)). 

The second constraint is that the index terms assigned to each item in the sample data set must be assessable. How 
the assessment is conducted in detail is discussed in [section "Assessment"](#assessment). For now, it is 
sufficient 
to say that we require a standard against which we can evaluate the assigned index terms. By "standard" I mean that 
given 
a vocabulary of index terms and our sample data set, for every item in the sample data set, there is an approved 
subset of the 
vocabulary. The production of a standard from scratch is of course is very costly since a person, usually highly 
skilled in a certain academic domain, must assign and/or approve each item's index terms (!!source). For this reason 
we try to avoid having to produce a standard. One way of doing so is by requiring items in the sample data set to 
have non-empty `keywords` data field. The caveats of this approach are discussed in [section "Assessment"](#assessment).

Taking into account the third constraint simply means that we do not employ any further restrictions. We can hence 
construct the sample data set by choosing exactly those items from `/edoc/raw` which have non-empty data fields 
`title`, `abstract`, `id_number`, and `keywords`. We do so by calling `_Data.select_from_file` iteratively for all 
files in `/edoc/raw`. The resulting file is saved in `/edoc/selected` as `selected_master.json`. 

### Analysis

Of the 68'345 items in `/edoc/raw`, all have a title (non-empty `title` data field), most items have an ID (57'153 items with non-empty `id_number` data field), roughly half of the items have an abstract (37'381 items with non-empty `abstract` data field), an less than 10% of the items have keywords (6'660 items with non-empty `keywords` data field). The sample data set as requires all the above data fields to be non-empty; `/edoc/sample/sample_master.json` has 4'111 items and hence constitutes 6% of the raw data. 

!! Now talk about the distribution of the items 

!! Mayhaps give a description of `selected_master.json`, namely 4111 items. Also, perhaps also say how many items in 
`/raw` per data field 
are 
available. 

## Machine indexing

### General overview
!! Give an overview over machine indexing.

### Annif
!! Given an intro to Annif.

### Implementation
!! Explain how to implementation works.

!! Somewhere here we talk about indexing based on title and/or abstract and/or fulltext. Fulltext is not yet
 implemented. Some observations to do so:
 - the link to the fulltext is constructed from the data fields `offical url` and `documebts - main`, e.g., `https
 ://edoc.unibas.ch/79633/` + `1/` + `2020_18_Informed by wet feet_How do floods affect property prices.pdf` to get
  `https://edoc.unibas.ch/79633/1/2020_18_Informed by wet feet_How do floods affect property prices.pdf`

## Gold standard

### Extract keywords

### Clean keywords

### Frequency analysis

### Mapping to controlled vocabularies

## Assessment

### Precision, recall, F1-score
!! Discussion of metrics

### Annif versus gold standard

#### YSO

#### Wikidata

### Annif versus MeSH



### Digression: truth-conditions for indexing
(Correspondence theory of indexing: subject term T fits text X iff text X is about T)
### Targets
!! Find out what I meant here.

### Analysis

## Discussion

# Refinement

# Implementation strategy

# Conclusion

# Bibliography

# Appendix

