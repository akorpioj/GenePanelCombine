"""
Genie API service for gene identity lookup and PMID categorization storage.

Genie API endpoints used:
  GET  /gene/{gene_symbol}                   -> list of Ensembl IDs
  GET  /gene/id:{ensembl_id}                 -> gene detail (display name, chromosome, description)
  GET  /gene/id:{ensembl_id}/omim            -> OMIM ID
  GET  /gene/id:{ensembl_id}/pmids           -> stored PMID/category list
  POST /gene/id:{ensembl_id}/pmids/bulk      -> store PMID/category list in bulk

Category integer mapping (matches Genie API):
  0 = Uncategorized (default)
  1 = Not useful
  2 = Probably not useful
  3 = Possibly useful
  4 = Useful
"""

import os
import logging
from typing import Optional

import requests
from flask import current_app

log = logging.getLogger(__name__)

# Timeout for all Genie API calls (seconds)
_TIMEOUT = 10


class GenieService:
    """Service for interacting with the Genie gene-information API."""

    def __init__(self):
        self._configured = False
        self.base_url: str = ''
        self.api_key: str = ''

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _configure(self) -> None:
        """Read config lazily so the object can be created at import time."""
        if self._configured:
            return

        try:
            base_url = current_app.config.get('GENIE_API_URL')
            api_key  = current_app.config.get('GENIE_API_KEY')
        except RuntimeError:
            base_url = None
            api_key  = None

        self.base_url = (base_url or os.environ.get('GENIE_API_URL', 'http://127.0.0.1:8000')).rstrip('/')
        self.api_key  = api_key  or os.environ.get('GENIE_SECRET_API_KEY', '')

        if not self.api_key:
            raise RuntimeError(
                "GENIE_SECRET_API_KEY is not set. "
                "Add it to your .env file or environment variables."
            )

        self._configured = True

    def _headers(self) -> dict:
        return {'X-API-Key': self.api_key}

    def _get(self, path: str) -> Optional[dict]:
        """
        Perform a GET request to the Genie API.

        Returns the parsed JSON dict on success, None on 404.
        Raises requests.HTTPError for any other non-2xx response.
        """
        self._configure()
        url = f'{self.base_url}{path}'
        log.debug('Genie GET %s', url)
        response = requests.get(url, headers=self._headers(), timeout=_TIMEOUT)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, payload) -> dict:
        """
        Perform a POST request to the Genie API.

        Returns the parsed JSON dict on success.
        Raises requests.HTTPError for any non-2xx response.
        """
        self._configure()
        url = f'{self.base_url}{path}'
        log.debug('Genie POST %s payload=%s', url, payload)
        response = requests.post(url, json=payload, headers=self._headers(), timeout=_TIMEOUT)
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def lookup_gene(self, gene_symbol: str) -> list[str]:
        """
        Look up Ensembl IDs for a gene symbol.

        Args:
            gene_symbol: HGNC gene symbol, e.g. 'BRCA1'.

        Returns:
            List of Ensembl IDs (may be empty if not found).
        """
        data = self._get(f'/gene/{gene_symbol}')
        if data is None:
            return []
        return data.get('ensembl_id', [])

    def get_gene_detail(self, ensembl_id: str) -> Optional[dict]:
        """
        Fetch full gene annotation for an Ensembl ID.

        Args:
            ensembl_id: Ensembl gene ID, e.g. 'ENSG00000012048'.

        Returns:
            dict with keys: display_name, seq_region_name (chromosome),
            description, biotype, assembly_name, start, end, strand.
            Returns None if not found.
        """
        data = self._get(f'/gene/id:{ensembl_id}')
        if data is None:
            return None
        # The API wraps the Ensembl payload under 'gene_info'
        return data.get('gene_info')

    def get_omim_id(self, ensembl_id: str) -> Optional[str]:
        """
        Fetch the OMIM ID for a given Ensembl ID.

        Args:
            ensembl_id: Ensembl gene ID.

        Returns:
            OMIM ID string (e.g. '113705'), or None if not available.
        """
        data = self._get(f'/gene/id:{ensembl_id}/omim')
        if data is None:
            return None
        return str(data.get('omim_id')) if data.get('omim_id') else None

    def get_categorizations(self, ensembl_id: str) -> list[dict]:
        """
        Fetch stored PMID/category pairs for an Ensembl ID.

        Args:
            ensembl_id: Ensembl gene ID.

        Returns:
            List of dicts: [{"pmid": int, "category": int}, ...]
            Returns [] if no record exists yet for this gene.
        """
        data = self._get(f'/gene/id:{ensembl_id}/pmids')
        if data is None:
            return []
        return data.get('pmids', [])

    def save_categorizations_bulk(
        self,
        ensembl_id: str,
        pmid_category_list: list[dict],
    ) -> dict:
        """
        Store a list of PMID/category pairs for an Ensembl ID in bulk.

        Args:
            ensembl_id: Ensembl gene ID.
            pmid_category_list: List of dicts, each with:
                - 'pmid' (int): PubMed ID
                - 'category' (int): 0–4

        Returns:
            dict with keys:
              'added':   list of PMIDEntry dicts that were newly created
              'skipped': list of int PMIDs that already existed
        """
        payload = [
            {'pmid': int(item['pmid']), 'category': int(item['category'])}
            for item in pmid_category_list
        ]
        return self._post(f'/gene/id:{ensembl_id}/pmids/bulk', payload)


# Module-level singleton — import and use directly in routes/services
genie_service = GenieService()
