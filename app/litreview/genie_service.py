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
        self.api_key  = api_key  or os.environ.get('GENIE_API_KEY', '')

        if not self.api_key:
            raise RuntimeError(
                "GENIE_API_KEY is not set. "
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

    def _patch(self, path: str, payload) -> dict:
        """
        Perform a PATCH request to the Genie API.

        Returns the parsed JSON dict on success.
        Raises requests.HTTPError for any non-2xx response (including 404).
        """
        self._configure()
        url = f'{self.base_url}{path}'
        log.debug('Genie PATCH %s payload=%s', url, payload)
        response = requests.patch(url, json=payload, headers=self._headers(), timeout=_TIMEOUT)
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

    def get_omim_ids_bulk(self, ensembl_ids: list) -> dict:
        """
        Fetch OMIM IDs for multiple Ensembl IDs in one API call.

        Args:
            ensembl_ids: List of Ensembl gene IDs.

        Returns:
            Dict mapping ensembl_id -> omim_id string (or None if not found).
        """
        return self._post('/genes/omim-ids', ensembl_ids)

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
              'skipped': list of int PMIDs that already existed (NOT updated)

        Note: The Genie API is add-only for this endpoint.  PMIDs that already
        have a classification will appear in 'skipped' and their category will
        NOT be changed.  Use set_categorization() to update a single existing
        entry via the non-bulk endpoint (which may have upsert semantics).
        """
        payload = [
            {'pmid': int(item['pmid']), 'category': int(item['category'])}
            for item in pmid_category_list
        ]
        return self._post(f'/gene/id:{ensembl_id}/pmids/bulk', payload)

    def update_categorization(self, ensembl_id: str, pmid: int, category: int) -> dict:
        """
        Update the category for an existing PMID via PATCH /gene/id:{ensembl_id}/pmids/{pmid}.

        Args:
            ensembl_id: Ensembl gene ID.
            pmid:       PubMed ID (must already exist for this gene in Genie).
            category:   0–4.

        Returns:
            PMIDEntry dict: {'pmid': int, 'category': int}

        Raises:
            requests.HTTPError: 404 if gene/PMID not found; other status on error.
        """
        return self._patch(
            f'/gene/id:{ensembl_id}/pmids/{int(pmid)}',
            {'category': int(category)},
        )

    def update_categorizations_bulk(
        self,
        ensembl_id: str,
        pmid_category_list: list[dict],
    ) -> list:
        """
        Update multiple PMID/category pairs via PATCH /gene/id:{ensembl_id}/pmids.

        PMIDs not found in Genie are silently skipped (no error).

        Args:
            ensembl_id:        Ensembl gene ID.
            pmid_category_list: List of dicts with 'pmid' (int) and 'category' (0–4).

        Returns:
            List of updated PMIDEntry dicts.

        Raises:
            requests.HTTPError on any non-2xx response.
        """
        payload = [
            {'pmid': int(item['pmid']), 'category': int(item['category'])}
            for item in pmid_category_list
        ]
        return self._patch(f'/gene/id:{ensembl_id}/pmids', payload)

    def register_gene(self, ensembl_id: str) -> dict:
        """
        Register a gene in Genie by Ensembl ID.

        Creates (or ensures the existence of) the gene entry in Genie
        with no PMID categorizations.  Can safely be called more than
        once for the same gene.

        Args:
            ensembl_id: Ensembl gene ID, e.g. 'ENSG00000012048'.

        Returns:
            dict with keys 'added' and 'skipped' (both typically empty lists).
        """
        return self._post(f'/gene/id:{ensembl_id}/pmids/bulk', [])

    def check_genes(self, ensembl_ids: list) -> list:
        """
        Check which Ensembl IDs already exist in Genie.

        Args:
            ensembl_ids: List of Ensembl gene IDs, e.g. ['ENSG00000012048'].

        Returns:
            List of dicts with keys 'ensembl_id' (str) and 'exists' (bool).
        """
        return self._post('/genes/check', ensembl_ids)

    def lookup_genes_bulk(self, symbols: list) -> dict:
        """
        Resolve multiple gene symbols to Ensembl IDs in one API call.

        Args:
            symbols: List of HGNC gene symbols, e.g. ['BRCA1', 'TP53'].

        Returns:
            Dict mapping symbol -> Ensembl ID string for found genes.
            Symbols not found in Genie are absent from the returned dict.
        """
        return self._post('/genes/ensembl-ids', symbols)

    def create_genes_bulk(self, ensembl_ids: list) -> list:
        """
        Create gene records for a list of Ensembl IDs in one API call.

        Already-existing entries are skipped server-side.

        Args:
            ensembl_ids: List of Ensembl gene IDs, e.g. ['ENSG00000012048'].

        Returns:
            List of dicts with keys 'ensembl_id' (str) and 'exists' (bool).
            'exists': True means the gene already existed; False means newly created.
        """
        return self._post('/genes', ensembl_ids)


# Module-level singleton — import and use directly in routes/services
genie_service = GenieService()
