"""
Business logic services for finance_manager_core.

Provides:
- CSV/Excel import functionality
- Transaction deduplication
- Data validation and transformation
"""

import csv
import hashlib
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import List, Dict, Tuple, Optional, Any

from django.db import transaction as db_transaction
from django.utils import timezone

from .models import Transaction, Category, TRANSACTION_TYPE_CHOICES
from plugins.finance_manager_accounts.models import Account

logger = logging.getLogger(__name__)


class ImportError(Exception):
    """Custom exception for import errors."""
    pass


class TransactionImportService:
    """
    Service for importing transactions from CSV/Excel files.
    
    Supports:
    - CSV import with configurable column mapping
    - Excel import (via openpyxl)
    - Duplicate detection and deduplication
    - Validation and error reporting
    """

    # Default column mappings (can be overridden)
    DEFAULT_CSV_MAPPING = {
        'date': ['date', 'data', 'competence_date', 'transaction_date'],
        'description': ['description', 'descrizione', 'memo', 'note'],
        'amount': ['amount', 'importo', 'value', 'gross_amount'],
        'type': ['type', 'tipo', 'transaction_type'],
        'category': ['category', 'categoria'],
        'reference': ['reference', 'riferimento', 'external_reference', 'id'],
    }

    def __init__(self, account: Account, default_category: Optional[Category] = None):
        self.account = account
        self.default_category = default_category
        self.errors: List[Dict[str, Any]] = []
        self.imported_count = 0
        self.skipped_count = 0
        self.duplicate_count = 0

    def import_csv(
        self,
        csv_content: str,
        column_mapping: Optional[Dict[str, str]] = None,
        date_format: str = '%Y-%m-%d',
        skip_duplicates: bool = True,
        delimiter: str = ',',
    ) -> Tuple[int, int, List[Dict]]:
        """
        Import transactions from CSV content.
        
        Args:
            csv_content: The CSV file content as string
            column_mapping: Dict mapping our fields to CSV column names
            date_format: Date format string for parsing dates
            skip_duplicates: Whether to skip duplicate transactions
            delimiter: CSV delimiter character
            
        Returns:
            Tuple of (imported_count, skipped_count, errors)
        """
        self.errors = []
        self.imported_count = 0
        self.skipped_count = 0
        self.duplicate_count = 0

        try:
            reader = csv.DictReader(StringIO(csv_content), delimiter=delimiter)
            headers = reader.fieldnames

            if not headers:
                raise ImportError("CSV file has no headers")

            # Resolve column mapping
            mapping = self._resolve_column_mapping(headers, column_mapping)

            rows = list(reader)
            transactions_to_create = []
            seen_hashes = set()

            for row_num, row in enumerate(rows, start=2):  # Start at 2 (1 is header)
                try:
                    tx_data = self._parse_csv_row(row, mapping, date_format)
                    
                    if tx_data is None:
                        self.skipped_count += 1
                        continue

                    # Generate hash for deduplication
                    tx_hash = self._generate_transaction_hash(tx_data)

                    if skip_duplicates:
                        # Check in-file duplicates
                        if tx_hash in seen_hashes:
                            self.duplicate_count += 1
                            continue
                        seen_hashes.add(tx_hash)

                        # Check existing transactions
                        if self._is_duplicate(tx_data, tx_hash):
                            self.duplicate_count += 1
                            continue

                    transactions_to_create.append(tx_data)

                except Exception as e:
                    self.errors.append({
                        'row': row_num,
                        'error': str(e),
                        'data': dict(row)
                    })

            # Bulk create transactions
            if transactions_to_create:
                with db_transaction.atomic():
                    created = Transaction.objects.bulk_create([
                        Transaction(
                            account=self.account,
                            category=tx['category'],
                            description=tx['description'],
                            gross_amount=tx['amount'],
                            competence_date=tx['date'],
                            transaction_type=tx['type'],
                            status='pending',
                            data_source='import_csv',
                            external_reference=tx.get('reference'),
                        )
                        for tx in transactions_to_create
                    ])
                    self.imported_count = len(created)

        except Exception as e:
            logger.exception("CSV import failed")
            self.errors.append({
                'row': 0,
                'error': f"Import failed: {str(e)}",
                'data': None
            })

        return self.imported_count, self.skipped_count + self.duplicate_count, self.errors

    def _resolve_column_mapping(
        self,
        headers: List[str],
        custom_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Resolve column names to actual CSV headers."""
        mapping = {}
        headers_lower = {h.lower().strip(): h for h in headers}

        for field, possible_names in self.DEFAULT_CSV_MAPPING.items():
            if custom_mapping and field in custom_mapping:
                if custom_mapping[field].lower() in headers_lower:
                    mapping[field] = headers_lower[custom_mapping[field].lower()]
                    continue

            for name in possible_names:
                if name.lower() in headers_lower:
                    mapping[field] = headers_lower[name.lower()]
                    break

        return mapping

    def _parse_csv_row(
        self,
        row: Dict[str, str],
        mapping: Dict[str, str],
        date_format: str
    ) -> Optional[Dict[str, Any]]:
        """Parse a single CSV row into transaction data."""
        result = {}

        # Parse date (required)
        date_col = mapping.get('date')
        if not date_col or not row.get(date_col):
            raise ValueError("Missing date field")
        
        try:
            result['date'] = datetime.strptime(row[date_col].strip(), date_format).date()
        except ValueError:
            # Try alternative formats
            for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                try:
                    result['date'] = datetime.strptime(row[date_col].strip(), fmt).date()
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Invalid date format: {row[date_col]}")

        # Parse description (required)
        desc_col = mapping.get('description')
        if not desc_col or not row.get(desc_col):
            raise ValueError("Missing description field")
        result['description'] = row[desc_col].strip()[:500]

        # Parse amount (required)
        amount_col = mapping.get('amount')
        if not amount_col or not row.get(amount_col):
            raise ValueError("Missing amount field")
        
        amount_str = row[amount_col].strip()
        # Handle different number formats
        amount_str = amount_str.replace(',', '.').replace(' ', '')
        amount_str = ''.join(c for c in amount_str if c.isdigit() or c in '.-')
        
        try:
            amount = Decimal(amount_str)
        except InvalidOperation:
            raise ValueError(f"Invalid amount: {row[amount_col]}")

        # Determine transaction type from amount sign or explicit field
        type_col = mapping.get('type')
        if type_col and row.get(type_col):
            type_val = row[type_col].strip().lower()
            if type_val in ['income', 'entrata', 'e', '+']:
                result['type'] = 'income'
            elif type_val in ['expense', 'uscita', 'u', '-']:
                result['type'] = 'expense'
            else:
                result['type'] = 'income' if amount >= 0 else 'expense'
        else:
            result['type'] = 'income' if amount >= 0 else 'expense'

        result['amount'] = abs(amount)

        # Parse category (optional)
        cat_col = mapping.get('category')
        if cat_col and row.get(cat_col):
            cat_name = row[cat_col].strip()
            category = Category.objects.filter(name__iexact=cat_name, is_active=True).first()
            result['category'] = category or self.default_category
        else:
            result['category'] = self.default_category

        if not result['category']:
            raise ValueError("No category specified and no default category set")

        # Parse reference (optional)
        ref_col = mapping.get('reference')
        if ref_col and row.get(ref_col):
            result['reference'] = row[ref_col].strip()[:200]

        return result

    def _generate_transaction_hash(self, tx_data: Dict[str, Any]) -> str:
        """Generate a hash for deduplication based on key transaction data."""
        hash_input = f"{tx_data['date']}|{tx_data['amount']}|{tx_data['description'][:100]}"
        if tx_data.get('reference'):
            hash_input += f"|{tx_data['reference']}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def _is_duplicate(self, tx_data: Dict[str, Any], tx_hash: str) -> bool:
        """Check if a similar transaction already exists."""
        # Check by external reference first (fastest)
        if tx_data.get('reference'):
            if Transaction.objects.filter(
                account=self.account,
                external_reference=tx_data['reference']
            ).exists():
                return True

        # Check by date + amount + description similarity
        similar = Transaction.objects.filter(
            account=self.account,
            competence_date=tx_data['date'],
            gross_amount=tx_data['amount'],
            description__icontains=tx_data['description'][:50]
        )
        return similar.exists()


def import_transactions_from_csv(
    account_id: int,
    csv_content: str,
    category_id: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for CSV import.
    
    Args:
        account_id: ID of the target account
        csv_content: CSV file content
        category_id: Optional default category ID
        **kwargs: Additional arguments passed to import_csv
        
    Returns:
        Dict with import results
    """
    try:
        account = Account.objects.get(pk=account_id)
    except Account.DoesNotExist:
        return {
            'success': False,
            'error': f'Account {account_id} not found',
            'imported': 0,
            'skipped': 0,
            'errors': []
        }

    category = None
    if category_id:
        category = Category.objects.filter(pk=category_id, is_active=True).first()

    service = TransactionImportService(account, category)
    imported, skipped, errors = service.import_csv(csv_content, **kwargs)

    return {
        'success': len(errors) == 0,
        'imported': imported,
        'skipped': skipped,
        'duplicates': service.duplicate_count,
        'errors': errors
    }


def import_transactions_from_excel(
    account_id: int,
    file_path: str,
    sheet_name: str = None,
    category_id: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Import transactions from an Excel file.
    
    Requires openpyxl to be installed.
    """
    try:
        import openpyxl
    except ImportError:
        return {
            'success': False,
            'error': 'openpyxl is required for Excel import. Install with: pip install openpyxl',
            'imported': 0,
            'skipped': 0,
            'errors': []
        }

    try:
        account = Account.objects.get(pk=account_id)
    except Account.DoesNotExist:
        return {
            'success': False,
            'error': f'Account {account_id} not found',
            'imported': 0,
            'skipped': 0,
            'errors': []
        }

    category = None
    if category_id:
        category = Category.objects.filter(pk=category_id, is_active=True).first()

    try:
        wb = openpyxl.load_workbook(file_path, read_only=True)
        ws = wb[sheet_name] if sheet_name else wb.active

        # Convert to CSV-like format
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return {
                'success': False,
                'error': 'Excel file is empty',
                'imported': 0,
                'skipped': 0,
                'errors': []
            }

        headers = [str(h) if h else '' for h in rows[0]]
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        
        for row in rows[1:]:
            writer.writerow([str(cell) if cell is not None else '' for cell in row])

        csv_content = output.getvalue()
        
        service = TransactionImportService(account, category)
        imported, skipped, errors = service.import_csv(csv_content, **kwargs)

        return {
            'success': len(errors) == 0,
            'imported': imported,
            'skipped': skipped,
            'duplicates': service.duplicate_count,
            'errors': errors
        }

    except Exception as e:
        logger.exception("Excel import failed")
        return {
            'success': False,
            'error': str(e),
            'imported': 0,
            'skipped': 0,
            'errors': []
        }
