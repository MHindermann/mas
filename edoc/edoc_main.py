from __future__ import annotations
from typing import List, Optional, Dict, Union, Tuple
from json import load, dump
from datetime import datetime
from time import sleep
from annif_client import AnnifClient

import os.path


DIR = os.path.dirname(__file__)


class _Utility:
    """ A collection of utility functions. """

    @classmethod
    def load_json(cls, file_path: str) -> list:
        """ Load a JSON object from file.

        :param file_path: complete path to file including filename and extension
        """

        with open(file_path, encoding="utf-8") as file:
            loaded = load(file)

            return loaded

    @classmethod
    def save_json(cls, data: List[Dict], file_path: str) -> None:
        """ Save data as JSON file.

        :param data: the data to be saved
        :param file_path: complete path to file including filename and extension
        """

        with open(file_path, "w") as file:
            dump(data, file)

    @classmethod
    def split_json(cls, file_path: str, save_path: str) -> None:
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
    """ A collection of data functions. """

    @classmethod
    def select_items(cls, data: List[Dict], *fields: str) -> List[Dict]:
        """ Select items based on fields from (raw) edoc data.

        :param data: the input data from edoc
        :param fields: the required fields for an item to be selected
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
    def inspect(cls, data: List[Dict], *fields: str) -> None:
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


def select(file_path: str, *fields: str) -> None:
    """ Select items from file according to fields.

    For example: select(DIR + "/raw/2019.json", "title", "abstract", "keywords", "id_number")

    :param file_path: complete path to file including filename and extension
    :param fields: the required fields for an item to be selected
    """

    data = _Utility.load_json(file_path)
    print(f"{file_path} loaded")
    selected = _Data.select_items(data, *fields)
    print(f"Items selected")
    save_file_path = DIR + "/selected/" + str(datetime.now()).split(".")[0].replace(":", "-").replace(" ", "-")
    _Utility.save_json(selected, save_file_path)


def index(file_path: str,
          save_path: str,
          project_ids: List[str],
          abstract: bool = False,
          fulltext: bool = False,
          limit: int = None,
          threshold: int = None) -> None:
    """ Index items of file with Annif-client.

    Project IDs are yso-en, yso-maui-en, yso-bonsai-en, yso-fasttext-en, tfidf, wikidata-en, fasttext.

    :param file_path: complete path to file including filename and extension
    :param save_path: complete path to save folder including filename without extension
    :param project_ids: Annif-client project IDs to be used
    :param abstract: use abstract for indexing, defaults to False
    :param fulltext: use fulltext for indexing, defaults to False
    :param limit: Annif-client limit, defaults to None
    :param threshold: Annif-client threshold, defaults to None
    """

    data = _Utility.load_json(file_path)
    client = AnnifClient()
    modified_data = []

    for item in data:

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

            # indexing:
            results = client.suggest(project_id=project_id, text=text, threshold=threshold, limit=limit)

            # add results to item:
            modified_item["annif"][name] = results

        # add item to output:
        modified_data.append(modified_item)

    _Utility.save_json(modified_data, save_path)


index(file_path=DIR+"/selected/selected_master.json",
      save_path=f"{DIR}/indexed/indexed_working_{str(datetime.now()).split('.')[0].replace(':', '-').replace(' ', '-')}.json",
      project_ids=["yso-en", "yso-maui-en", "yso-bonsai-en", "yso-fasttext-en", "wikidata-en"],
      abstract=True)

