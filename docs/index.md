<!-- mas documentation master file, created by
sphinx-quickstart on Sun Mar  7 20:23:58 2021. -->
# Documentation of classes and functions in /mas/files


### class files.Utility()
A collection of utility functions.


#### classmethod load_json(file_path)
Load a JSON object from file.


* **Parameters**

    **file_path** (`str`) – complete path to file including filename and extension



* **Return type**

    `list`



#### classmethod save_json(data, file_path)
Save data as JSON file.


* **Parameters**

    
    * **data** (`Union`[`List`, `Dict`]) – the data to be saved


    * **file_path** (`str`) – complete path to file including filename and extension



* **Return type**

    `None`



#### classmethod split_json(file_path, save_path)
Split a JSON file into files not larger than 100MB.


* **Parameters**

    
    * **file_path** (`str`) – complete path to file including filename and extension


    * **save_path** (`str`) – complete path to save folder including filename without extension



* **Return type**

    `None`



### class files.Data()
A collection of Edoc data functions.


#### classmethod enrich_author_keywords(file_path, save_path)
Enrich author keywords.

For each Edoc item: the string of author keywords is cut into single keywords and each keyword is cleaned. Each
keyword is then enriched with Qid, MeSH and YSO ID if available.


* **Parameters**

    
    * **file_path** (`str`) – complete path to file including filename and extension


    * **save_path** (`str`) – complete path to save folder including filename without extension



* **Return type**

    `None`



#### classmethod enrich_with_annif(file_path, save_path, project_ids, abstract=False, fulltext=False, limit=None, threshold=None)
Enrich items from file with automatic keywords using Annif-client.

Available Annif-client project IDs are yso-en, yso-maui-en, yso-bonsai-en, yso-fasttext-en, wikidata-en.


* **Parameters**

    
    * **file_path** (`str`) – complete path to file including filename and extension


    * **save_path** (`str`) – complete path to save folder including filename without extension


    * **project_ids** (`List`[`str`]) – Annif-client project IDs to be used


    * **abstract** (`bool`) – toggle use abstract for indexing, defaults to False


    * **fulltext** (`bool`) – toggle use fulltext for indexing, defaults to False


    * **limit** (`Optional`[`int`]) – Annif-client limit, defaults to None


    * **threshold** (`Optional`[`int`]) – Annif-client threshold, defaults to None



* **Return type**

    `None`



#### classmethod enrich_with_mesh(file_path, save_path)
Enrich Edoc data per item with MeSH keywords from PubMed if available.


* **Parameters**

    
    * **file_path** (`str`) – complete path to file including filename and extension


    * **save_path** (`str`) – complete path to save folder including filename without extension



* **Return type**

    `None`



#### classmethod fetch_mesh(pubmed_id)
Fetch MeSH keywords for article based on PubMed ID.


* **Parameters**

    **pubmed_id** (`str`) – article PubMed ID



* **Return type**

    `List`[`Dict`]



#### classmethod get_departments()
Get all Edoc departments.


* **Return type**

    `List`[`str`]



#### classmethod inspect(data, \*fields)
Print fields of items in data.


* **Parameters**

    
    * **data** (`List`[`Dict`]) – data to be inspected


    * **fields** (`str`) – fields to focus on



* **Return type**

    `None`



#### classmethod map2reference(keyword)
Map a keyword to its reference keyword.

Keyword must first be cleaned by corresponding _Keyword method.


* **Parameters**

    **keyword** (`str`) – the keyword



* **Return type**

    `Dict`



#### classmethod select_from_data(data, \*fields)
Select items from data based on non-empty fields.

Only items where all required fields are non-empty are sample.


* **Parameters**

    
    * **data** (`List`[`Dict`]) – the input data


    * **fields** (`str`) – the required fields for an item to be sample



* **Return type**

    `List`[`Dict`]



#### classmethod select_from_file(file_path, \*fields)
Select items from file according to fields.

For example: select_from_file(DIR + “/raw/2019.json”, “title”, “abstract”, “keywords”, “id_number”)


* **Parameters**

    
    * **file_path** (`str`) – complete path to file including filename and extension


    * **fields** (`str`) – the required fields for an item to be sample



* **Return type**

    `None`



#### classmethod super_enrich_with_annif(abstract)
Enrich items with automatic keywords using all Annif-client projects.


* **Parameters**

    **abstract** (`bool`) – toggle use abstract for indexing



* **Return type**

    `None`



### class files.Keywords()
A collection of functions for manipulating Edoc author keywords.


#### classmethod clean_keyword(keyword)
Clean a keyword.


* **Parameters**

    **keyword** (`str`) – the keyword



* **Return type**

    `List`[`str`]



#### classmethod clean_keywords(keywords_per_item)
Turn a string of keywords per item into a list of cleaned (=normalized) keywords.


* **Parameters**

    **keywords_per_item** (`List`[`str`]) – the keywords



* **Return type**

    `List`[`str`]



#### classmethod enrich_with_yso(file_path, save_path)
Enrich items in file with YSO IDs if available.


* **Parameters**

    
    * **file_path** (`str`) – complete path to file including filename and extension


    * **save_path** (`str`) – complete path to save folder including filename without extension



#### classmethod extract_keywords(file_path)
Extract keywords per item from file.


* **Parameters**

    **file_path** (`str`) – complete path to file including filename and extension



* **Return type**

    `List`[`str`]



#### classmethod fetch_yso(keyword)
Fetch the YSO ID for a keyword if any.


* **Parameters**

    **keyword** (`str`) – the keyword



* **Return type**

    `Optional`[`str`]



#### classmethod make_count(file_path, save_path)
Count all keywords and their respective IDs per item in file.


* **Parameters**

    
    * **file_path** (`str`) – complete path to file including filename and extension


    * **save_path** (`str`) – complete path to save folder including filename and extension



* **Return type**

    `None`



#### classmethod make_histogram(keywords)
Make a histogram for keywords.


* **Parameters**

    **keywords** (`List`[`str`]) – the keywords



* **Return type**

    `List`[`Dict`]



### class files.Analysis()
A collection of data analysis functions.


#### classmethod count_confusion(standard, suggestions)
Count the values in the confusion matrix for standard and suggestions.


* **Parameters**

    
    * **standard** (`list`) – the standard


    * **suggestions** (`list`) – the suggestions



#### classmethod extract_standard(item, marker)
Extract gold standard IDs from item.


* **Parameters**

    
    * **item** (`dict`) – the Edoc item


    * **marker** (`str`) – the type of ID



* **Return type**

    `Optional`[`list`]



#### classmethod extract_suggestions(item, marker, n=10)
Extract top n Annif suggestion IDs from item.


* **Parameters**

    
    * **item** (`dict`) – the Edoc item


    * **marker** (`str`) – project_id-abstract-fulltext-limit-threshold


    * **n** (`int`) – number of top IDs (by score) to be extracted, defaults to 10



#### classmethod get_id_type(marker)
Get the ID type from the project ID.


* **Parameters**

    **marker** (`str`) – project_id-abstract-fulltext-limit-threshold



* **Return type**

    `str`



#### classmethod get_sklearn_array(item, project_id, abstract=False, fulltext=False, limit=None, threshold=None, n=10)
Get Sklearn y_true and y_pred for an item.

Available Annif-client project IDs are yso-en, yso-maui-en, yso-bonsai-en, yso-fasttext-en, wikidata-en.


* **Parameters**

    
    * **item** (`dict`) – sample data set item


    * **project_id** (`str`) – Annif-client project ID


    * **abstract** (`bool`) – toggle use abstract for indexing, defaults to False


    * **fulltext** (`bool`) – toggle use fulltext for indexing, defaults to False


    * **limit** (`Optional`[`int`]) – Annif-client limit, defaults to None


    * **threshold** (`Optional`[`int`]) – Annif-client threshold, defaults to None


    * **n** (`int`) – number of top IDs (by score) to be extracted, defaults to 10



* **Return type**

    `Optional`[`dict`]



#### classmethod make_metrics(file_path, project_id, abstract=False, fulltext=False, limit=None, threshold=None, n=10, department=None)
Make Sklearn metrics F1, recall, precision for file.

The output is saved as /metrics/metrics_{marker}.json.

Available Annif-client project IDs are yso-en, yso-maui-en, yso-bonsai-en, yso-fasttext-en, wikidata-en.


* **Parameters**

    
    * **file_path** (`str`) – complete path to file including filename and extension


    * **project_id** (`str`) – Annif-client project ID


    * **abstract** (`bool`) – toggle use abstract for indexing, defaults to False


    * **fulltext** (`bool`) – toggle use fulltext for indexing, defaults to False


    * **limit** (`Optional`[`int`]) – Annif-client limit, defaults to None


    * **threshold** (`Optional`[`int`]) – Annif-client threshold, defaults to None


    * **n** (`int`) – number of top IDs (by score) to be extracted per item, defaults to 10


    * **department** (`Optional`[`str`]) – restrict to items from department



* **Return type**

    `None`



#### classmethod make_random_sample(file_path, save_path, size)
Save a random sample from the population in the file.


* **Parameters**

    
    * **file_path** (`str`) – complete path to file including filename and extension


    * **save_path** (`str`) – complete path to save folder including filename and extension


    * **size** (`int`) – the sample size



* **Return type**

    `None`



#### classmethod print_chi_square_fit(file_path)
Print chi square goodness of fit.

File must be CSV with first line title; three columns with first column categories, second column expected and
third column observed values.


* **Parameters**

    **file_path** (`str`) – complete path to file including filename and extension



* **Return type**

    `None`



#### classmethod super_make_metrics(file_path, department=None)
Make metrics for all combinations of Annif projects and parameters in enriched Edoc file.

Output files are saved in /metrics/. Joint results are saved in /analysis/metrics.json.


* **Parameters**

    
    * **file_path** (`str`) – complete path to file including filename and extension


    * **department** (`Optional`[`str`]) – restrict to items from department



#### classmethod super_make_stats()
Make metrics for files in /metrics.

Output is saved as /analysis/metrics.json.


* **Return type**

    `None`


# Indices and tables


* Index


* Module Index


* Search Page
