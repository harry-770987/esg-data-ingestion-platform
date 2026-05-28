from datetime import datetime, date
import pandas as pd
from .constants import UNIT_CONVERSION_FACTORS, SOURCE_TYPE_METADATA
from .exceptions import NormalizationError

class ValueNormalizer:
    """
    Handles carbon accounting conversions and formatting. Normalizes raw inputs 
    to standard accounting units and formats dates and scopes.
    """

    @staticmethod
    def normalize_unit(quantity, raw_unit, target_unit) -> tuple:
        """
        Converts quantity from raw_unit to target_unit.
        Returns a tuple of (normalized_quantity, normalized_unit).
        If conversion is impossible, returns (None, raw_unit) to flag as suspicious.
        """
        if quantity is None or pd.isna(quantity):
            return None, raw_unit

        try:
            qty_val = float(quantity)
        except (ValueError, TypeError):
            return None, raw_unit

        u_from = str(raw_unit).strip().lower()
        u_to = str(target_unit).strip().lower()

        # Direct identity match
        if u_from == u_to:
            return qty_val, target_unit

        # Check conversion factors
        factor = UNIT_CONVERSION_FACTORS.get((u_from, target_unit))
        if factor is not None:
            return round(qty_val * factor, 4), target_unit

        # If conversion rate is unknown
        return None, raw_unit

    @staticmethod
    def normalize_date(date_val) -> date:
        """
        Attempts to parse date values into a standard datetime.date object.
        Returns None if parsing fails.
        """
        if date_val is None or pd.isna(date_val):
            return None

        if isinstance(date_val, (date, datetime)):
            if isinstance(date_val, datetime):
                return date_val.date()
            return date_val

        date_str = str(date_val).strip()
        
        # Try common date formats
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y', '%b %d, %Y'):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
                
        # Fallback to pandas flexible date parser
        try:
            res = pd.to_datetime(date_str)
            if pd.isna(res):
                return None
            return res.date()
        except Exception:
            return None

    @classmethod
    def normalize_record(cls, row_dict, source_type) -> dict:
        """
        Normalizes a parsed row dictionary according to the source_type.
        Returns a dictionary with standardized keys for model insertion.
        """
        meta = SOURCE_TYPE_METADATA.get(source_type)
        if not meta:
            raise NormalizationError(f"Unsupported source type: {source_type}")

        raw_qty = row_dict.get('quantity')
        raw_unit = row_dict.get('unit', '')
        raw_date = row_dict.get('transaction_date')
        raw_activity = row_dict.get('activity_type')

        # 1. Normalize quantity and unit
        norm_qty, norm_unit = cls.normalize_unit(raw_qty, raw_unit, meta['standard_unit'])

        # 2. Normalize date
        norm_date = cls.normalize_date(raw_date)

        # 3. Determine activity type
        activity_type = str(raw_activity).strip() if raw_activity and not pd.isna(raw_activity) else None
        if not activity_type:
            # Provide standard default name based on source category
            if source_type == 'SAP_FUEL':
                activity_type = 'Fuel'
            elif source_type == 'UTILITY_ELEC':
                activity_type = 'Electricity'
            else:
                activity_type = 'Travel'

        return {
            'category': meta['category'],
            'scope': meta['scope'],
            'activity_type': activity_type,
            'transaction_date': norm_date,
            'quantity': raw_qty,
            'unit': raw_unit,
            'normalized_quantity': norm_qty,
            'normalized_unit': norm_unit,
        }
