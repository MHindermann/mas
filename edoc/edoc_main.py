from __future__ import annotations
from typing import List, Optional, Dict, Union, Tuple
from json import load, dump
from datetime import datetime
from annif_client import AnnifClient

import os.path


DIR = os.path.realpath(__file__)


class _Utility:
    """ A collection of utility functions. """

    @classmethod
    def load_json(cls, folder: str, filename: str) -> list:
        """ Load a JSON object from file.

        :param folder: the path to the folder
        :param filename: the name of the file
        """

        filename = folder + f"{filename}.json"

        with open(filename, encoding="utf-8") as file:
            loaded = load(file)

            return loaded

    @classmethod
    def save_json(cls, data: List[Dict], folder: str = None, filename: str = None) -> None:
        """ Save data as JSON file.

        :param data: the data to be saved
        :param folder: complete folder path, defaults to None
        :param filename: the name of the file, defaults to None
        """

        if filename is None:
            filename = str(datetime.now()).split(".")[0].replace(":", "-")

        if folder is None:
            full_filename = f"{filename}.json"
        else:
            full_filename = folder + f"{filename}.json"

        with open(full_filename, "w") as file:
            dump(data, file)

    @classmethod
    def split_json(cls, folder: str, filename: str) -> None:
        """ Split a JSON file into pieces not larger than 100MB.

        :param folder: the path to the folder
        :param filename: the name of the file
        """

        pass



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


def select(filename: str, *fields: str) -> None:
    """ Select items with fields from (raw) edoc file.

    :param filename: the name of the raw edoc file
    :param fields: the required fields for an item to be selected
    """

    data = _Utility.load_json("raw/", filename)
    print(f"{filename} loaded")
    selected = _Data.select_items(data, *fields)
    print(f"Items selected")
    folder = DIR + "/selected"
    _Utility.save_json(selected, folder)


# select("1900-2020", "title", "abstract", "keywords", "id_number")


def index(filename: str):
    data = _Utility.load_json("selected/", filename)

    client = AnnifClient()
    for item in data:
        print(client.suggest(project_id="yso-en", text=item.get("title")))
        break

#index("selected_master")