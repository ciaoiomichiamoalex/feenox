import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from core import decode_json
from .constants import (PATH_PRJ, URL_DAILY_TOLLS, URL_DOCUMENTS, URL_DOWNLOAD_DOCUMENT,
                        URL_INVOICE_TOLLS, URL_LOGIN, URL_TOLL_GROUPS)


class Feenox:
    """
    The Feenox object allow for downloading tolls detail and invoice documents.
    """
    # _cache: save in cache the token to be reuse quickly during same run without make authentication call
    _cache: dict[str, Any] = {}

    _PATH_CFG: Path = None

    def __init__(self,
                 cfg_in: str | Path,
                 force: bool = False):
        """
        Read from a JSON file the credentials and retrive the token for other API calls.
        The token will be saved on a cache file in the project root for reuse it if still valid.

        :param cfg_in: The path to the JSON file with the login credentials.
        :type cfg_in: str | Path
        :param force: Force the regeneration of the token, even if the previous one is still valid, defaults to False.
        :type force: bool
        """
        if not Feenox._cache or force:
            cache = PATH_PRJ / '.cache'

            # check if the cache file exists and his token is still valid
            if cache.is_file() and not force:
                Feenox._cache = decode_json(cache)
                Feenox._cache['expire'] = datetime.fromisoformat(Feenox._cache['expire'])
                Feenox._check_token_expire(cfg_in)
            else:
                cfg_in = Path(cfg_in).resolve()
                # if input path is a directory search for default config filename
                if cfg_in.is_dir():
                    cfg_in = cfg_in / 'feenox.json'
                Feenox._PATH_CFG = cfg_in
                config = decode_json(cfg_in)

                (response := requests.post(
                    url=URL_LOGIN,
                    data={'grant_type': 'client_credentials'},
                    auth=(config['client_id'], config['client_secret'])
                )).raise_for_status()

                response = response.json()
                Feenox._cache['token'] = f"{response['token_type']} {response['access_token']}"
                Feenox._cache['expire'] = datetime.now() + timedelta(seconds=response['expires_in'])

                with open(cache, 'w', encoding='utf-8') as jou:
                    json.dump(Feenox._cache, jou,
                              default=(lambda obj: obj.isoformat()
                                       if isinstance(obj, datetime)
                                       else TypeError(f'Type {type(obj)} not serializable')))

    @classmethod
    def _check_token_expire(cls,
                            cfg_in: str | Path = None) -> None:
        """
        Check if the current token has already expired or is still valid.

        :param cfg_in: The path to the JSON file with the login credentials, defaults to None.
        :type cfg_in: str | Path
        """
        if not cls._cache['expire'] - datetime.now() > timedelta(seconds=60):
            cls(cfg_in, force=True) if cfg_in else cls(cls._PATH_CFG, force=True)

    @classmethod
    def get_toll_groups(cls) -> list[dict[str, str]]:
        """
        Retrieve the list of all tolling groups to be used for tolls search calls.

        :return: A list of dictionary with all tolling groups, as code and description.
        :rtype: list[dict[str, str]]
        """
        cls._check_token_expire()
        (response := requests.get(
            url=URL_TOLL_GROUPS,
            headers={'x-token': cls._cache['token']}
        )).raise_for_status()
        return response.json()

    @staticmethod
    def _check_tolls_date(tolls_date: tuple[date, date] = None,
                          acquisition_date: tuple[date, date] = None,
                          invoice_date: tuple[date, date] = None) -> tuple[str, date, date]:
        """
        Check if the date parameters for tolls search calls is valid, return values for body request.
        At least one date parameter is mandatory, with maximum 7 days interval between them and not older than 90 days.

        :param tolls_date: Filter on tolling exit gate date, defaults to None.
        :type tolls_date: tuple[date, date]
        :param acquisition_date: Filter on data acquisition date, defaults to None.
        :type acquisition_date: tuple[date, date]
        :param invoice_date: Filter on invoice date, defaults to None.
        :type invoice_date: tuple[date, date]
        :return: A tuple with the date type valorized and the two values.
        :rtype: tuple[str, date, date]
        """
        if sum(bool(arg) for arg in (tolls_date, acquisition_date, invoice_date)) != 1:
            raise ValueError('Only one argument must be specified!')

        date_type, date_from, date_to = next((name,) + arg
                                             for name, arg in (
                                                 ('tolls', tolls_date),
                                                 ('acquisition', acquisition_date),
                                                 ('invoice', invoice_date)
                                             ) if arg)
        if date_from < date.today() - timedelta(days=90):
            raise ValueError(f'The date_from field cannot be older than 90 days!')
        elif abs(date_to - date_from) > timedelta(days=7):
            raise ValueError(f'The interval between the date_from and date_to fields cannot be greater than 7 days!')
        return date_type, date_from, date_to

    @classmethod
    def get_invoice_tolls(cls,
                          toll_groups: list[str] = None,
                          tolls_date: tuple[date, date] = None,
                          acquisition_date: tuple[date, date] = None,
                          invoice_date: tuple[date, date] = None) -> list[dict[str, Any]]:
        """
        Retrieve the list of all invoice tolling detail filtering by tolling groups and dates.
        At least one date parameter is mandatory, with maximum 7 days interval between them and not older than 90 days.

        :param toll_groups: The list of tolling groups to retrieve, defaults to None.
        :type toll_groups: list[str]
        :param tolls_date: Filter on tolling exit gate date, defaults to None.
        :type tolls_date: tuple[date, date]
        :param acquisition_date: Filter on data acquisition date, defaults to None.
        :type acquisition_date: tuple[date, date]
        :param invoice_date: Filter on invoice date, defaults to None.
        :type invoice_date: tuple[date, date]
        :return: A list of dictionary with the tolling details.
        :rtype: dict[str, Any]
        """
        cls._check_token_expire()
        date_type, date_from, date_to = cls._check_tolls_date(tolls_date, acquisition_date, invoice_date)

        (response := requests.post(
            url=URL_INVOICE_TOLLS,
            headers={'x-token': cls._cache['token']},
            json={
                'tollsGroup': (toll_groups if toll_groups else []),
                date_type: {
                    'date_from': date_from.isoformat(),
                    'date_to': date_to.isoformat()
                }
            }
        )).raise_for_status()
        return response.json()

    @classmethod
    def get_daily_tolls(cls,
                        toll_groups: list[str] = None,
                        tolls_date: tuple[date, date] = None,
                        acquisition_date: tuple[date, date] = None,
                        invoice_date: tuple[date, date] = None) -> list[dict[str, Any]]:
        """
        Retrieve the list of all daily tolling detail filtering by tolling groups and dates.
        At least one date parameter is mandatory, with maximum 7 days interval between them and not older than 90 days.

        :param toll_groups: The list of tolling groups to retrieve, defaults to None.
        :type toll_groups: list[str]
        :param tolls_date: Filter on tolling exit gate date, defaults to None.
        :type tolls_date: tuple[date, date]
        :param acquisition_date: Filter on data acquisition date, defaults to None.
        :type acquisition_date: tuple[date, date]
        :param invoice_date: Filter on invoice date, defaults to None.
        :type invoice_date: tuple[date, date]
        :return: A list of dictionary with the tolling details.
        :rtype: dict[str, Any]
        """
        cls._check_token_expire()
        date_type, date_from, date_to = cls._check_tolls_date(tolls_date, acquisition_date, invoice_date)

        (response := requests.post(
            url=URL_DAILY_TOLLS,
            headers={'x-token': cls._cache['token']},
            json={
                'tollsGroup': (toll_groups if toll_groups else []),
                date_type: {
                    'date_from': date_from.isoformat(),
                    'date_to': date_to.isoformat()
                }
            }
        )).raise_for_status()
        return response.json()

    @staticmethod
    def _check_documents_date(document_date: tuple[date, date] = None,
                              publication_date: tuple[date, date] = None) -> tuple[str, date, date] | None:
        """
        Check if the date parameters for documents search calls is valid, return values for body request.

        :param document_date: Filter on document date, defaults to None.
        :type document_date: tuple[date, date]
        :param publication_date: Filter on document publication date, defaults to None.
        :type publication_date: tuple[date, date]
        :return: A tuple with the date type valorized and the two values.
        :rtype: tuple[str, date, date]
        """
        res = sum(bool(arg) for arg in (document_date, publication_date))
        if not res: return None
        elif res > 1: raise ValueError('Only one argument must be specified!')

        date_type, date_from, date_to = next((name,) + arg
                                             for name, arg in (
                                                 ('documentDate', document_date),
                                                 ('documentPublicationDate', publication_date)
                                             ) if arg)
        return date_type, date_from, date_to

    @classmethod
    def get_documents(cls,
                      document_type: str,
                      document_category: str = None,
                      document_date: tuple[date, date] = None,
                      publication_date: tuple[date, date] = None) -> dict[str, list[dict[str, Any]]]:
        """
        Retrieve the list of all documents filtering by type, category and dates.

        :param document_type: The document type to be searched.
        :type document_type: str
        :param document_category: The document category to be searched, defaults to None.
        :type document_category: str
        :param document_date: Filter on document date, defaults to None.
        :type document_date: tuple[date, date]
        :param publication_date: Filter on document publication date, defaults to None.
        :type publication_date: tuple[date, date]
        :return: A list of dictionary with the documents details.
        :rtype: dict[str, list[dict[str, Any]]]
        """
        cls._check_token_expire()
        if res := cls._check_documents_date(document_date, publication_date):
            date_type, date_from, date_to = res

        (response := requests.post(
            url=f"{URL_DOCUMENTS}/{document_type}{(f'/{document_category}' if document_category else '')}",
            headers={'x-token': cls._cache['token']},
            json=({
                date_type: {
                    'date_from': date_from,
                    'date_to': date_to
                }
            } if res else {})
        )).raise_for_status()
        return response.json()

    @classmethod
    def download_document(cls,
                          document_id: str,
                          directory: str | Path) -> Path:
        """
        Download a specific document specified by id.

        :param document_id: The document id retrieve from search documents call.
        :type document_id: str
        :param directory: The path to the folder where to save the downloaded file.
        :type directory: str | Path
        :return: The path to the downloaded file.
        :rtype: Path
        """
        cls._check_token_expire()
        (response := requests.get(
            url=f'{URL_DOWNLOAD_DOCUMENT}/{document_id}',
            headers={'x-token': cls._cache['token']}
        )).raise_for_status()

        directory = Path(directory).resolve()
        # input path must a directory, the filename will be got from response header
        fou = (directory if directory.is_dir() else directory.parent) / response.headers['x-filename']
        with open(fou, 'wb') as res:
            res.write(response.content)
        return fou
