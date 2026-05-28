from datetime import date
import numpy as np
import pandas as pd

class RowValidator:
    """
    Validates normalized rows, flags data anomalies, and performs statistical 
    outlier detection (> 3 standard deviations from batch mean).
    """

    @classmethod
    def validate_batch(cls, records: list) -> list:
        """
        Processes a list of normalized records, detects anomalies, and flags suspicious rows.
        Appends `suspicious` (bool) and `suspicious_reasons` (list of strings) to each record dictionary.
        """
        # 1. Extract valid quantities for statistical outlier detection
        valid_quantities = []
        for r in records:
            nq = r.get('normalized_quantity')
            if nq is not None and not pd.isna(nq):
                try:
                    valid_quantities.append(float(nq))
                except (ValueError, TypeError):
                    pass

        # 2. Calculate median and Median Absolute Deviation (MAD) if we have enough sample points
        # MAD is robust to outliers, preventing a single large outlier from masking itself.
        outlier_detection_active = len(valid_quantities) >= 3
        if outlier_detection_active:
            median_val = np.median(valid_quantities)
            mad_val = np.median([abs(x - median_val) for x in valid_quantities])
            # Avoid division by zero if all values are identical
            mad_val = max(mad_val, 1e-4)

        today = date.today()

        # 3. Perform row-by-row checks
        for r in records:
            reasons = []
            
            # Extract fields
            raw_qty = r.get('quantity')
            raw_unit = r.get('unit')
            norm_qty = r.get('normalized_quantity')
            norm_unit = r.get('normalized_unit')
            trans_date = r.get('transaction_date')

            # --- Structural / Content Checks ---
            
            # Check quantity issues
            if raw_qty is None or pd.isna(raw_qty) or str(raw_qty).strip() == '':
                reasons.append("Missing raw quantity")
            else:
                try:
                    val = float(raw_qty)
                    if val <= 0:
                        reasons.append("Quantity must be greater than zero")
                except (ValueError, TypeError):
                    reasons.append("Quantity is not a valid number")

            # Check unit issues
            if not raw_unit or pd.isna(raw_unit) or str(raw_unit).strip() == '':
                reasons.append("Missing raw unit")
            elif norm_qty is None:
                reasons.append(f"Unit conversion failed for unit: '{raw_unit}'")

            # Check date issues
            if trans_date is None or pd.isna(trans_date):
                reasons.append("Missing or invalid transaction date")
            elif trans_date > today:
                reasons.append(f"Transaction date '{trans_date}' is in the future")

            # --- Statistical Outlier Checks ---
            if outlier_detection_active and norm_qty is not None:
                try:
                    val = float(norm_qty)
                    # MAD outlier detection: check if value is > 4.5 MADs away from median
                    if abs(val - median_val) / mad_val > 4.5:
                        reasons.append(
                            f"Quantity is a statistical outlier. Value ({val}) is an extreme outlier "
                            f"relative to the batch median (median: {round(median_val, 2)}, MAD: {round(mad_val, 2)})"
                        )
                except (ValueError, TypeError):
                    pass

            # Mark state
            r['suspicious'] = len(reasons) > 0
            r['suspicious_reasons'] = reasons

        return records
