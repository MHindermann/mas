from __future__ import annotations
from typing import List, Optional, Dict, Union, Tuple
from json import load, dump
import csv
from datetime import datetime
from annif_client import AnnifClient
import os.path
import urllib3
import xmltodict
import ast
import scipy.stats
from sklearn.metrics import f1_score, recall_score, precision_score


DIR = os.path.dirname(__file__)


class _Utility:
    """ A collection of utility functions. """

    @classmethod
    def load_json(cls,
                  file_path: str) -> list:
        """ Load a JSON object from file.

        :param file_path: complete path to file including filename and extension
        """

        with open(file_path, encoding="utf-8") as file:
            loaded = load(file)

            return loaded

    @classmethod
    def save_json(cls,
                  data: Union[List, Dict],
                  file_path: str) -> None:
        """ Save data as JSON file.

        :param data: the data to be saved
        :param file_path: complete path to file including filename and extension
        """

        with open(file_path, "w") as file:
            dump(data, file)

    @classmethod
    def split_json(cls,
                   file_path: str,
                   save_path: str) -> None:
        """ Split a JSON file into files not larger than 100MB.

        :param file_path: complete path to file including filename and extension
        :param save_path: complete path to save folder including filename without extension
        """

        size = int(os.path.getsize(file_path)/(1024*1024))
        print(f"{file_path} is {size} MB")

        if size > 99:
            data = cls.load_json(file_path)
            maximum = len(data)
            position = 0
            while position < maximum:
                json_slice = data[position:position + 5000]
                cls.save_json(json_slice, DIR + f"{save_path}_{position}-{position + 5000}.json")
                position = position + 5000


class _Data:
    """ A collection of edoc data functions. """

    @classmethod
    def select_from_data(cls,
                         data: List[Dict],
                         *fields: str) -> List[Dict]:
        """ Select items from data based on non-empty fields.

        Only items where all required fields are non-empty are sample.

        :param data: the input data
        :param fields: the required fields for an item to be sample
        """

        selected = []
        for item in data:
            keep_item = True
            for field in fields:
                if field not in item:
                    keep_item = False
                    break
            if keep_item is True:
                selected.append(item)

        return selected

    @classmethod
    def select_from_file(cls,
                         file_path: str,
                         *fields: str) -> None:
        """ Select items from file according to fields.

        For example: select_from_file(DIR + "/raw/2019.json", "title", "abstract", "keywords", "id_number")

        :param file_path: complete path to file including filename and extension
        :param fields: the required fields for an item to be sample
        """

        data = _Utility.load_json(file_path)
        print(f"{file_path} loaded")
        selected = _Data.select_from_data(data, *fields)
        print(f"Items sample")
        save_file_path = DIR + "/sample/" + str(datetime.now()).split(".")[0].replace(":", "-").replace(" ", "-")
        _Utility.save_json(selected, save_file_path)

    @classmethod
    def inspect(cls,
                data: List[Dict],
                *fields: str) -> None:
        """ Print fields of items in data.

        :param data: data to be inspected
        :param fields: fields to focus on
        """

        item_nr = 1
        for item in data:
            print(f"Item #{item_nr}")
            for field in fields:
                if field in item:
                    print(f"{str(field)}: {item.get(field)}")
            item_nr = item_nr + 1
            print("**********")

        print(f"Items in data: {len(data)}")

    @classmethod
    def enrich_author_keywords(cls,
                               file_path: str,
                               save_path: str) -> None:
        """ Enrich author keywords.

        For each edoc item: the string of author keywords is cut into single keywords and each keyword is cleaned. Each
        keyword is then enriched with Qid, MeSH and YSO ID if available.

        :param file_path: complete path to file including filename and extension
        :param save_path: complete path to save folder including filename without extension
        """

        data = _Utility.load_json(file_path)
        modified_data = []

        for item in data:

            # make deep copy of item:
            modified_item = dict(item)

            # clean keywords
            keywords = modified_item.get("keywords")
            keywords_clean = _Keywords.clean_keywords([keywords])

            # enrich keywords
            enriched_keywords = []
            for keyword in keywords_clean:
                enriched_keywords.append(cls.map2reference(keyword))

            modified_item["keywords enriched"] = enriched_keywords

            # add modified item to output:
            modified_data.append(modified_item)

        _Utility.save_json(modified_data, save_path + ".json")

    @classmethod
    def map2reference(cls,
                      keyword: str) -> Dict:
        """ Map a keyword to its reference keyword.

        Keyword must first be cleaned by corresponding _Keyword method.

        :param keyword: the keyword
        """

        # load reference keywords:
        keywords_reference = _Utility.load_json(DIR + "/keywords/keywords_reference_master.json")

        # enrich keywords
        for entry in keywords_reference:
            if entry["keyword clean"] == keyword:
                return entry

        print(f"No reference found for {keyword}!")

    @classmethod
    def enrich_with_mesh(cls,
                         file_path: str,
                         save_path: str) -> None:
        """ Enrich edoc data per item with MeSH keywords from PubMed if available.

        :param file_path: complete path to file including filename and extension
        :param save_path: complete path to save folder including filename without extension
        """

        data = _Utility.load_json(file_path)
        modified_data = []

        for item in data:

            # sanity check:
            print(item.get("title"))

            # make deep copy of item:
            modified_item = dict(item)

            # find PubMed ID if available
            identifiers = modified_item.get("id_number") # identifiers is list of dict
            for identifier in identifiers:
                if identifier.get("type") == "pmid":
                    pmid_id = identifier.get("id")

                    # add MeSH based on PubMed ID:
                    mesh = cls.fetch_mesh(pmid_id)
                    modified_item["mesh"] = mesh

            # add modified item to output:
            modified_data.append(modified_item)

        _Utility.save_json(modified_data, save_path + ".json")

    @classmethod
    def fetch_mesh(cls,
                   pubmed_id: str) -> List[Dict]:
        """ Fetch MeSH keywords for article based on PubMed ID.

        :param pubmed_id: article PubMed ID
        """

        mesh = []

        http = urllib3.PoolManager()
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pubmed_id}&retmode=xml"
        response = http.request('GET', url)
        article = xmltodict.parse(response.data)
        try:
            for item in article["PubmedArticleSet"]["PubmedArticle"]["MedlineCitation"]["MeshHeadingList"]["MeshHeading"]:
                mesh.append({"MeSH descriptor ID": item["DescriptorName"]["@UI"], "MeSH label": item["DescriptorName"]["#text"]})
        except (TypeError, KeyError):
            pass

        return mesh

    @classmethod
    def enrich_with_annif(cls,
                          file_path: str,
                          save_path: str,
                          project_ids: List[str],
                          abstract: bool = False,
                          fulltext: bool = False,
                          limit: int = None,
                          threshold: int = None) -> None:
        """ Enrich items from file with automatic keywords using Annif-client.

        Available Annif-client project IDs are yso-en, yso-maui-en, yso-bonsai-en, yso-fasttext-en, wikidata-en.

        :param file_path: complete path to file including filename and extension
        :param save_path: complete path to save folder including filename without extension
        :param project_ids: Annif-client project IDs to be used
        :param abstract: toggle use abstract for indexing, defaults to False
        :param fulltext: toggle use fulltext for indexing, defaults to False
        :param limit: Annif-client limit, defaults to None
        :param threshold: Annif-client threshold, defaults to None
        """

        data = _Utility.load_json(file_path)
        client = AnnifClient()
        modified_data = []

        for item in data:

            # sanity check:
            print(item.get("title"))

            # make deep copy of item:
            modified_item = dict(item)

            # make text to be indexed:
            text = modified_item.get("title")
            if abstract is True:
                text = text + " " + modified_item.get("abstract")
            if fulltext is True:
                pass
                # TODO: add fulltext support

            for project_id in project_ids:

                # make name for indexing:
                name = f"{project_id}-{str(abstract)}-{str(fulltext)}-{str(threshold)}-{str(limit)}"

                # check if item has annif-component:
                if "annif" in modified_item:
                    if name in modified_item.get("annif"):
                        print(f"WARNING: {name} is already available and is currently being overridden!")
                else:
                    modified_item["annif"] = dict()

                # actual indexing via Annif-client:
                results = client.suggest(project_id=project_id, text=text, threshold=threshold, limit=limit)

                # add results to item:
                modified_item["annif"][name] = results

            # add modified item to output:
            modified_data.append(modified_item)

        _Utility.save_json(modified_data, save_path)

    @classmethod
    def super_enrich_with_annif(cls,
                                abstract: bool) -> None:
        """ Enrich items with automatic keywords using all Annif-client projects.

        :param abstract: toggle use abstract for indexing
        """

        file_path = DIR + "/indexed/indexed_master.json"
        save_path = f"{DIR}/indexed/indexed_working_{str(datetime.now()).split('.')[0].replace(':', '-').replace(' ', '-')}.json"
        project_ids = ["yso-en", "yso-maui-en", "yso-bonsai-en", "yso-fasttext-en", "wikidata-en"]

        _Data.enrich_with_annif(file_path=file_path, save_path=save_path, project_ids=project_ids, abstract=abstract)


class _Keywords:
    """ A collection of functions for manipulating edoc author keywords. """

    @classmethod
    def extract_keywords(cls,
                         file_path: str) -> List[str]:
        """ Extract keywords per item from file.

        :param file_path: complete path to file including filename and extension
        """
        data = _Utility.load_json(file_path)
        keywords = []
        for item in data:
            keywords.append(item.get("keywords"))

        return keywords

    @classmethod
    def clean_keywords(cls,
                       keywords_per_item: List[str]) -> List[str]:
        """ Turn a string of keywords per item into a list of cleaned (=normalized) keywords.

        :param keywords_per_item: the keywords
        """

        assert(isinstance(keywords_per_item, list))

        clean = []
        for keywords in keywords_per_item:
            try:
                # generate distinct keywords from string:
                if ";" in keywords:
                    keywords = keywords.split(";")
                elif "–" in keywords:
                    keywords = keywords.split("-")
                else:
                    keywords = keywords.split(",")
                # clean keywords:
                for keyword in keywords:
                    clean = clean + cls.clean_keyword(keyword)
            except TypeError:
                print(f"TypeError with {keywords}")
        return clean

    @classmethod
    def clean_keyword(cls,
                      keyword: str) -> List[str]:
        """ Clean a keyword.

        :param keyword: the keyword
        """

        clean = []
        # make lower case:
        keyword = keyword.lower()
        # remove *:
        keyword = keyword.replace("*", "")
        # remove whitespace:
        keyword = keyword.strip()

        new_keywords = []
        if "," in keyword:
            new_keywords = keyword.split(",")
        elif "/" in keyword:
            new_keywords = keyword.split("/")
        elif ":" in keyword:
            new_keywords = keyword.split(":")
        # untested but required
        # elif "&" in keyword:
        #    new_keywords = keyword.split("&")

        if len(new_keywords) > 0:
            for new_keyword in new_keywords:
                clean = clean + cls.clean_keyword(new_keyword)
            return clean
        else:
            clean.append(keyword)
            return clean

    @classmethod
    def make_histogram(cls,
                       keywords: List[str]) -> List[Dict]:
        """ Make a histogram for keywords.

        :param keywords: the keywords
        """
        histogram = dict()
        for keyword in keywords:
            if keyword in histogram:
                histogram[keyword] = histogram[keyword] + 1
            else:
                histogram[keyword] = 1

        openrefine_histogram = []
        for entry in histogram:
            openrefine_histogram.append({"keyword": entry, "occurrences": histogram.get(entry)})

        return openrefine_histogram

    @classmethod
    def enrich_with_yso(cls,
                        file_path: str,
                        save_path: str):
        """ Blah.

        :param file_path: complete path to file including filename and extension
        :param save_path: complete path to save folder including filename without extension
        """

        data = _Utility.load_json(file_path)
        modified_data = []

        for item in data:
            # make deep copy of item:
            modified_item = dict(item)

            # if YSO ID is missing, fetch it if available; but discard entries without clean keywords:
            if modified_item.get("yso id") == "":
                if modified_item.get("keyword clean") == "":
                    continue
                else:
                    yso = cls.fetch_yso(modified_item.get("keyword clean"))
                    modified_item["yso id"] = yso
                    print(yso)

            modified_data.append(modified_item)

        _Utility.save_json(modified_data, save_path)

    @classmethod
    def fetch_yso(cls,
                  keyword: str) -> Union[str, None]:
        """ Fetch the YSO ID for a keyword if any.

        :param keyword: the keyword
        """

        http = urllib3.PoolManager()
        url = f"https://api.finto.fi/rest/v1/yso/search?query={keyword}&lang=en"
        response = http.request('GET', url)

        try:
            results = ast.literal_eval(response.data.decode("UTF-8")).get("results")
            return results[0].get("localname")[1:]
        except (IndexError, SyntaxError):
            return None

    @classmethod
    def make_count(cls,
                   file_path: str,
                   save_path: str) -> None:
        """ Count all keywords and their respective IDs per item in file.

        :param file_path: complete path to file including filename and extension
        :param save_path: complete path to save folder including filename and extension
        """

        data = _Utility.load_json(file_path)
        output = []

        for item in data:
            gold_standard = item.get("keywords enriched")
            qid = 0
            mesh = 0
            yso = 0
            try:
                for keyword in gold_standard:
                    if keyword.get("qid") != "":
                        qid = qid + 1
                    if keyword.get("mesh id") != "":
                        mesh = mesh + 1
                    if keyword.get("yso id") != "":
                        yso = yso + 1
                output.append({"gold standard": len(gold_standard), "qid": qid, "mesh id": mesh, "yso id": yso})
            except AttributeError:
                continue

        _Utility.save_json(output, save_path)


class _Analysis:
    """ A collection of data analysis functions. """

    @classmethod
    def print_chi_square_fit(cls,
                             file_path: str) -> None:

        """ Print chi square goodness of fit.

        File must be CSV with first line title; three columns with first column categories, second column expected and
        third column observed values.

        :param file_path: complete path to file including filename and extension
        """

        with open(file_path, mode='r') as file:
            reader = csv.reader(file)

            expected = []
            observed = []

            line_count = 0
            for line in reader:
                if line_count == 0:
                    name = line
                    line_count = line_count + 1
                    continue
                expected.append(int(line[1].split(".")[0]))
                observed.append(int(line[2].split(".")[0]))

        print(f"Results for {name}")
        print(scipy.stats.chisquare(f_obs=observed, f_exp=expected))

    @classmethod
    def make_random_sample(cls,
                           file_path: str,
                           save_path: str,
                           size: int) -> None:
        """ Save a random sample from the population in the file.

        :param file_path: complete path to file including filename and extension
        :param save_path: complete path to save folder including filename and extension
        :param size: the sample size
        """

        population = _Utility.load_json(file_path)
        import random

        sample = random.sample(population=population, k=size)
        _Utility.save_json(sample, save_path)

    @classmethod
    def super_make_metrics(cls,
                           file_path: str):
        """ Make metrics for all combinations of Annif projects and parameters in enriched Edoc file.

        Output files are saved in /metrics.

        :param file_path: complete path to file including filename and extension
        """

        project_ids = ["yso-en", "yso-maui-en", "yso-bonsai-en", "yso-fasttext-en", "wikidata-en"]

        n = 1
        while n < 11:
            for project_id in project_ids:
                print(f"Working on {project_id}...")
                # title:
                cls.make_metrics(file_path=file_path,
                                 project_id=project_id)
                # title + abstract:
                cls.make_metrics(file_path=file_path,
                                 project_id=project_id,
                                 abstract=True)
                # title + limit:
                cls.make_metrics(file_path=file_path,
                                 project_id=project_id,
                                 n=n)
                # title + limit:
                cls.make_metrics(file_path=file_path,
                                 project_id=project_id,
                                 abstract=True,
                                 n=n)
            n = n + 1

    @classmethod
    def make_metrics(cls,
                     file_path: str,
                     project_id: str,
                     abstract: bool = False,
                     fulltext: bool = False,
                     limit: int = None,
                     threshold: int = None,
                     n: int = 10) -> None:

        """ Make Sklearn metrics F1, recall, precision for file.

        The output is saved as /metrics/metrics_{marker}.json.

        Available Annif-client project IDs are yso-en, yso-maui-en, yso-bonsai-en, yso-fasttext-en, wikidata-en.

        https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html
        https://scikit-learn.org/stable/modules/generated/sklearn.metrics.recall_score.html
        https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_score.html

        :param file_path: complete path to file including filename and extension
        :param project_id: Annif-client project ID
        :param abstract: toggle use abstract for indexing, defaults to False
        :param fulltext: toggle use fulltext for indexing, defaults to False
        :param limit: Annif-client limit, defaults to None
        :param threshold: Annif-client threshold, defaults to None
        :param n: number of top IDs (by score) to be extracted per item, defaults to 10
        """

        data = _Utility.load_json(file_path)

        # construct y_true (=standard) and y_pred (=suggestions) from data:
        standard = []
        suggestions = []
        for item in data:
            sklearn_array = cls.get_sklearn_array(item=item,
                                                  project_id=project_id,
                                                  abstract=abstract,
                                                  fulltext=fulltext,
                                                  limit=limit,
                                                  threshold=threshold,
                                                  n=n)
            if sklearn_array is None:
                continue
            standard = standard + sklearn_array.get("y_true")
            suggestions = suggestions + sklearn_array.get("y_pred")

        # construct the correct annif marker:
        marker = f"{project_id}-{abstract}-{fulltext}-{n}-{threshold}"

        # compute the metrics:
        metrics = {
            "F1-macro": f1_score(standard, suggestions, average='macro'),
            "Precision-macro": precision_score(standard, suggestions, average='macro', zero_division=0),
            "Recall-macro": recall_score(standard, suggestions, average='macro', zero_division=0),

            "F1-micro": f1_score(standard, suggestions, average='micro'),
            "Precision-micro": precision_score(standard, suggestions, average='micro', zero_division=0),
            "Recall-micro": recall_score(standard, suggestions, average='micro', zero_division=0),

            "F1-weighted": f1_score(standard, suggestions, average='weighted'),
            "Precision-weighted": precision_score(standard, suggestions, average='weighted', zero_division=0),
            "Recall-weighted": recall_score(standard, suggestions, average='weighted', zero_division=0)
        }

        _Utility.save_json(metrics, DIR + f"/metrics/metrics_{marker}.json")

    @classmethod
    def get_sklearn_array(cls,
                          item: dict,
                          project_id: str,
                          abstract: bool = False,
                          fulltext: bool = False,
                          limit: int = None,
                          threshold: int = None,
                          n: int = 10) -> Union[dict, None]:

        """ Get Sklearn y_true and y_pred for an item.

        Available Annif-client project IDs are yso-en, yso-maui-en, yso-bonsai-en, yso-fasttext-en, wikidata-en.

        :param item: sample data set item
        :param project_id: Annif-client project ID
        :param abstract: toggle use abstract for indexing, defaults to False
        :param fulltext: toggle use fulltext for indexing, defaults to False
        :param limit: Annif-client limit, defaults to None
        :param threshold: Annif-client threshold, defaults to None
        :param n: number of top IDs (by score) to be extracted, defaults to 10
        """

        # construct the correct annif marker:
        marker = f"{project_id}-{abstract}-{fulltext}-{limit}-{threshold}"

        # extract suggestion IDs:
        suggestions_ids = cls.extract_suggestions(item=item, marker=marker, n=n)

        # extract gold standard IDs:
        gold_standard_ids = cls.extract_standard(item=item, marker=marker)

        # make y_true, y_pred:
        if gold_standard_ids is None:
            return None

        # count the true positives:
        true_positive = 0
        for suggestion in suggestions_ids:
            try:
                if suggestion in gold_standard_ids:
                    true_positive = true_positive + 1
            except TypeError:
                return None

        # construct y_true:
        y_true = []
        for k in range(0, len(gold_standard_ids)):
            y_true.append(1)
        for k in range(0, len(suggestions_ids) - len(gold_standard_ids)):
            y_true.append(0)

        # construct y_pred:
        y_pred = []
        for k in range(0, true_positive):
            y_pred.append(1)
        for k in range(0, len(suggestions_ids) - true_positive):
            y_pred.append(1)
        for k in range(0, len(y_true) - len(y_pred)):
            y_pred.append(0)

        return {"y_true": y_true, "y_pred": y_pred}

    @classmethod
    def get_id_type(cls, marker: str) -> str:
        """ Get the ID type from the project ID.

        :param marker: project_id-abstract-fulltext-limit-threshold
        """

        if marker.split("-")[0] == "wikidata":
            return "qid"
        else:
            return "yso id"

    @classmethod
    def extract_suggestions(cls,
                            item: dict,
                            marker: str,
                            n: int = 10):

        """ Extract top n Annif suggestion IDs from item.

        :param item: the Edoc item
        :param marker: project_id-abstract-fulltext-limit-threshold
        :param n: number of top IDs (by score) to be extracted, defaults to 10
        """

        suggestions = item.get("annif").get(marker)

        suggestions_ids = []
        for suggestion in suggestions[:n]:
            uri = suggestion.get("uri")
            if cls.get_id_type(marker) == "qid":
                suggestions_ids.append(uri.split("http://www.wikidata.org/entity/")[1])
            elif cls.get_id_type(marker) == "yso id":
                suggestions_ids.append(int(uri.split("http://www.yso.fi/onto/yso/p")[1]))

        return suggestions_ids

    @classmethod
    def extract_standard(cls,
                         item: dict,
                         marker: str) -> Union[list, None]:
        """ Extract gold standard IDs from item.

        :param item: the Edoc item
        :param marker: the type of ID
        """

        id_type = cls.get_id_type(marker)
        gold_standard = item.get("keywords enriched")

        try:
            gold_standard_ids = []
            for keyword in gold_standard:
                if keyword.get(id_type) == "":
                    continue
                else:
                    gold_standard_ids.append(keyword.get(id_type))
        except AttributeError:
            return None

        if len(gold_standard_ids) == 0:
            return None
        else:
            return gold_standard_ids

    @classmethod
    def super_make_stats(cls) -> None:
        """ Make metrics for files in /metrics.

        Output is saved as /analysis/metrics_stats.json.
        """

        stats = []

        files = os.listdir(DIR + "/metrics")
        for file in files:

            metrics = _Utility.load_json(DIR + f"/metrics/{file}")
            metrics["file"] = file.split("/")[len(file.split("/"))-1]

            stats.append({"stat": metrics})

        _Utility.save_json(stats, DIR + "/analysis/metrics_stats.json")

_Analysis.super_make_stats()

exit()

_Analysis.super_make_metrics(file_path=DIR + "/indexed/indexed_master_mesh_enriched.json")

exit()

_Analysis.make_metrics(file_path=DIR + "/indexed/indexed_master_mesh_enriched.json",
                       project_id="yso-en",
                       abstract=True,
                       fulltext=False,
                       limit=None,
                       threshold=None,
                       n=10)



"""
Here I describe _Utility and _Data in relation to the files in the edoc folder. 

OK 1. We start by extracting all data from edoc. We do this by conducting an advanced search with the date-field set to
1900-2020. On the results page, we export the results as JSON. We use the data extracted pm 20201210 We have 68345 
entries and the file has a size of about 326 MB (which is why it won't fit on GitHub). We call this file 1900-2020.json.

OK 2. We split 1900-2020.json into smaller files that are easier handled and can be uploaded to GitHub. For this we use 
_Utility.split_json and we end up with files of size 20 MB or less containing 5000 or less entries each. These files are
called raw_master_x-y.json where x and y indicate the entries as given by 1900-2020.json. These files are saved under
eodc/raw

OK 3. We select a subset of the entries downloaded from edoc. We use _Data.select_from_file to do so (for convencience on 
1900-2020.json, but it could also be iteratively employed on the files in edoc/raw). The fields chosen are "title", 
"abstract", "keywords" and "id_number". The rationale for choosing these fields is given elsewhere (in short: we need 
items from which to construct a gold standard). The resulting 4111 items are saved as sample_master.json in 
edoc/sample.

ok 4. We extract the keywords (per entry) from the sample entries with _Keywords.extract_keywords like so:
keywords = _Keywords.extract_keywords(DIR + "/sample/sample_master.json")
We the save the resulting list under edoc/keywords as keywords_raw.json like so:
_Utility.save_json(keywords, DIR + "/keywords/keywords_extracted.json")

ok 5. We clean the extracted keywords with _Keywords.clean_keywords. How and why this is done is explained elsewhere. This 
is done as follows:
keywords_extracted = _Utility.load_json(DIR + "/keywords/keywords_extracted.json")
keywords_clean = _Keywords.clean_keywords(keywords_extracted)
We the save the resulting list under edoc/keywords as keywords_clean.json like so:
_Utility.save_json(clean, DIR + "keywords/keywords_clean.json")

ok 6. We build a histogram of the cleaned keywords used in the sample data with _Keyword.make_histogram:
keywords_clean = _Utility.load_json(DIR + "/keywords/keywords_clean.json")
histogram = _Keyword.make_histogram(keywords)
We the save the resulting histogram under edoc/keywords as keywords_clean_histogram.json like so:
_Utility.save_json(histogram, "/keywords/keywords_clean_histogram.json")

ok 7a. We create a list of reference keywords from the author keywords. To do this we use OpenRefine to match keywords from 
keywords_clean_histogram.json to Wikidata and other ontologies. This is explained elsewhere: draft-document OpenRefine 
methods up to 20210121. The resulting file is exported as keywords_clean_histogram_enriched.csv and then transformed to 
keywords_reference.json. Problem with exports here: multiple IDs are lost  (e.g., keyword clean ethnology has two mesh 
ids Q000208 and D005007 but the second is on different line and exported as standing alone...). 

ok 7b. We try to enrich the reference keywords with YSO ids wherever they are missing. Increases YSO coverage from 1759 to
3185. To do this:
_Keywords.enrich_with_yso(DIR + "/keywords/keywords_reference.json", DIR + "/keywords/keywords_reference-test.json")

8. We index the sample items with _Data.super_enrich_with_annif. How this works exactly is explained elsewhere. The 
resulting file is indexed_master.json saved in edoc/index. 

9. We enrich the sample items with MeSH keywords from PubMed if available (item needs a PubMed ID and items needs to
be indexed with MeSH on PubMed, 1653 items match this requirement); the resulting file is indexed_master_mesh.json. Like 
so: 
_Data.enrich_with_mesh(DIR + "/indexed/indexed_master.json", DIR + "/indexed/indexed_master_mesh")

OK 10. We enrich the sample items with cleaned author keywords (including, if available, Qid, MeSH ID, YSO ID) based on 
the reference keywords; the resulting file is indexed_master_mesh_enriched.json. To do so:
_Data.enrich_author_keywords(DIR + "/indexed/indexed_master_mesh.json", DIR + "/indexed/indexed_master_mesh_enriched")
NOTE: rerun this whenever we amend the reference keywords! WE MUST DO THIS NOW
"""

#TODO:
"""
A. For each set of keywords and article in sample_master.json, map each keyword to its corresponding keyword in 
keywords_clean_histogram.json. This is required so that we can compute precision and recall. To dos so, we require both 
the concept and its URI.

"""



exit()

# see https://medium.com/better-programming/how-to-convert-pdfs-into-searchable-key-words-with-python-85aab86c544f for some ideas

from tika import parser
rawText = parser.from_file(DIR + "/fulltexts/2020_18_Informed by wet feet_How do floods affect property prices.pdf")
rawList = rawText['content'].splitlines()
print(" ".join(rawList))
exit()

#this does not work:
#import PyPDF2
#filename = DIR + "/fulltexts/2020_18_Informed by wet feet_How do floods affect property prices.pdf"
#file = open(filename,'rb')
#pdf_reader = PyPDF2.PdfFileReader(file)

#num_pages = pdf_reader.numPages
#count = 0
#text = ""
#while count < num_pages:
#    page = pdf_reader.getPage(count)
#    count +=1
#    text += page.extractText()

#print(text)

