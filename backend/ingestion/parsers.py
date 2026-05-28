import pandas as pd
import io
from .constants import COLUMN_ALIASES
from .exceptions import ParserError, ValidationError

class CSVParser:
    """
    Pandas-backed CSV parser that reads uploaded files, resolves varying column headers 
    using a predefined alias map, and outputs clean intermediate records.
    """
    
    @staticmethod
    def parse(file_source, source_type=None) -> pd.DataFrame:
        """
        Parses a CSV file from a file path, string, or file-like stream.
        Standardizes column headers and returns a cleaned Pandas DataFrame.
        """
        try:
            # 1. Read CSV into Pandas DataFrame
            if isinstance(file_source, str):
                # Check if it's raw CSV content or a file path
                if '\n' in file_source or ',' in file_source:
                    df = pd.read_csv(io.StringIO(file_source))
                else:
                    df = pd.read_csv(file_source)
            elif hasattr(file_source, 'read'):
                # It's a file-like object (Django UploadedFile or io.BytesIO)
                # Read content as text
                content = file_source.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                df = pd.read_csv(io.StringIO(content))
            else:
                raise ParserError("Invalid file source type provided.")
        except Exception as e:
            raise ParserError(f"Failed to parse physical CSV: {str(e)}")

        if df.empty:
            raise ParserError("Uploaded CSV file is empty.")

        # 2. Normalize and resolve column headers
        df.columns = [str(col).strip().lower() for col in df.columns]
        column_mapping = {}
        
        # Check aliases for each standard target field
        for target_field, aliases in COLUMN_ALIASES.items():
            for col in df.columns:
                # Direct match or alias match
                if col == target_field or col in aliases:
                    column_mapping[col] = target_field
                    break # Assign the first matching column for this target field

        # Rename the matched columns
        df = df.rename(columns=column_mapping)

        # 3. Validate presence of critical columns (except activity_type, which can be source-defaulted)
        required_fields = ['transaction_date', 'quantity', 'unit']
        missing_fields = [field for field in required_fields if field not in df.columns]
        
        if missing_fields:
            raise ValidationError(
                f"Missing critical columns in CSV. Could not resolve: {', '.join(missing_fields)}. "
                f"Available columns: {list(df.columns)}"
            )

        # Clean NaN/Null values in target columns to prevent parsing bugs down the road
        # We fill nulls in optional fields and clean string fields
        for col in ['transaction_date', 'unit']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        return df
