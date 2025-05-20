import pandas as pd
import logging
from datetime import datetime
import numpy as np
import json
import math

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Helper function to sanitize values for JSON
def sanitize_for_json(value):
    """Convert values that are problematic for JSON (like NaN) to None."""
    if isinstance(value, (np.integer, np.floating)):
        # Convert numpy types to Python native types
        value = float(value)
        # Handle NaN and infinity
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    elif isinstance(value, np.bool_):
        return bool(value)
    elif isinstance(value, np.datetime64):
        return str(value) if pd.notnull(value) else None
    elif pd.isna(value):
        return None
    return value

def excel_col_to_index(col_letter):
    """
    Convert Excel column letter(s) to zero-based index.
    Handles both single and multi-letter column names (e.g., 'A', 'AA', 'AU', etc.)
    """
    index = 0
    for char in col_letter:
        index = index * 26 + (ord(char.upper()) - ord('A') + 1)
    return index - 1  # Convert to zero-based index

def parse_project_data(file):
    """
    Parse project data from an Excel file.
    
    Args:
        file: FileStorage object from Flask request
        
    Returns:
        list: List of dictionaries containing project data
    """
    try:
        logger.debug("Starting to parse Excel file")
        
        # Read the Project Table sheet, starting from row 3
        df = pd.read_excel(file, sheet_name='Project Table', skiprows=2)
        logger.debug(f"Successfully read Excel file with {len(df)} rows")
        
        # Log the column names for debugging
        logger.debug("Column names in Excel file:")
        for col in df.columns:
            logger.debug(f"Column: {col}")
        
        # Create a new DataFrame with the correct structure
        new_df = pd.DataFrame()
        
        # Map columns A-R (0-17) for basic project info
        basic_info_mapping = {
            0: 'Project Code',
            1: 'Title',
            2: 'Customer',
            3: 'Department',
            4: 'Platform',
            5: 'Type',
            6: 'Project Status',
            7: 'Contract Status',
            8: 'Possibility %',
            9: 'R&D Tax Credit',
            10: 'Expected Revenue',
            11: 'Contract Start',
            12: 'Contract End',
            13: 'Prj Start',
            14: 'Prj End',
            15: 'Location',
            16: 'Year',
            17: 'Updated'
        }
        
        # Map the basic info columns
        for excel_col, new_col in basic_info_mapping.items():
            if excel_col < len(df.columns):
                new_df[new_col] = df.iloc[:, excel_col]
        
        # Initialize all monthly fields with 0
        monthly_fields = [
            '2024 Total', '2024 Jan', '2024 Feb', '2024 Mar', '2024 Apr', '2024 May',
            '2024 Jun', '2024 Jul', '2024 Aug', '2024 Sep', '2024 Oct', '2024 Nov',
            '2024 Dec', '2024 Total2', '2025 Total', '2025 Jan', '2025 Feb', '2025 Mar',
            '2025 Apr', '2025 May', '2025 Jun', '2025 Jul', '2025 Aug', '2025 Sep',
            '2025 Oct', '2025 Nov', '2025 Dec'
        ]
        
        for field in monthly_fields:
            new_df[field] = 0
        
        # Map 2024 monthly data (starting from column AU)
        month_2024_mapping = {
            'AU': '2024 Total',
            'AV': '2024 Jan',
            'AW': '2024 Feb',
            'AX': '2024 Mar',
            'AY': '2024 Apr',
            'AZ': '2024 May',
            'BA': '2024 Jun',
            'BB': '2024 Jul',
            'BC': '2024 Aug',
            'BD': '2024 Sep',
            'BE': '2024 Oct',
            'BF': '2024 Nov',
            'BG': '2024 Dec',
            'BH': '2024 Total2'
        }
        
        # Map 2025 monthly data (starting from column BI)
        month_2025_mapping = {
            'BI': '2025 Total',
            'BJ': '2025 Jan',
            'BK': '2025 Feb',
            'BL': '2025 Mar',
            'BM': '2025 Apr',
            'BN': '2025 May',
            'BO': '2025 Jun',
            'BP': '2025 Jul',
            'BQ': '2025 Aug',
            'BR': '2025 Sep',
            'BS': '2025 Oct',
            'BT': '2025 Nov',
            'BU': '2025 Dec'
        }
        
        # DEBUGGING: Check raw values from Excel for the first few rows
        logger.debug("DEBUGGING 2025 MONTHLY VALUES FROM EXCEL:")
        if len(df) > 0:
            for i in range(min(5, len(df))):
                project_code = df.iloc[i, 0] if 0 < len(df.columns) else "Unknown"
                logger.debug(f"Project {i+1} ({project_code}):")
                for excel_col, new_col in month_2025_mapping.items():
                    col_index = excel_col_to_index(excel_col)
                    if col_index < len(df.columns):
                        raw_value = df.iloc[i, col_index]
                        logger.debug(f"  {new_col}: {raw_value} (type: {type(raw_value).__name__})")
        
        # Map 2024 monthly data
        for excel_col, new_col in month_2024_mapping.items():
            col_index = excel_col_to_index(excel_col)
            if col_index < len(df.columns):
                new_df[new_col] = df.iloc[:, col_index]
        
        # Map 2025 monthly data
        for excel_col, new_col in month_2025_mapping.items():
            col_index = excel_col_to_index(excel_col)
            if col_index < len(df.columns):
                new_df[new_col] = df.iloc[:, col_index]
        
        # Convert string columns
        string_columns = ['Project Code', 'Title', 'Customer', 'Department', 'Platform', 
                        'Type', 'Project Status', 'Contract Status', 'Location']
        for col in string_columns:
            if col in new_df.columns:
                new_df[col] = new_df[col].fillna('').astype(str)
        
        # Convert date columns
        date_columns = ['Contract Start', 'Contract End', 'Prj Start', 'Prj End', 'Updated']
        for col in date_columns:
            if col in new_df.columns:
                new_df[col] = pd.to_datetime(new_df[col], errors='coerce')
        
        # Convert Possibility % to percentage (multiply by 100)
        if 'Possibility %' in new_df.columns:
            new_df['Possibility %'] = pd.to_numeric(new_df['Possibility %'], errors='coerce').fillna(0) * 100
        
        # Convert other numeric columns
        numeric_columns = ['Expected Revenue', 'Year'] + monthly_fields
        for col in numeric_columns:
            if col in new_df.columns:
                new_df[col] = pd.to_numeric(new_df[col], errors='coerce').fillna(0)
        
        # DEBUGGING: Check processed monthly values for the first few rows
        logger.debug("PROCESSED 2025 MONTHLY VALUES:")
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        if len(new_df) > 0:
            for i in range(min(5, len(new_df))):
                project_code = new_df.iloc[i]['Project Code']
                logger.debug(f"Project {i+1} ({project_code}):")
                for month in months:
                    field_name = f"2025 {month}"
                    value = new_df.iloc[i][field_name]
                    logger.debug(f"  {field_name}: {value}")
        
        # DEBUGGING: Calculate expected monthly totals
        logger.debug("CALCULATED 2025 MONTHLY TOTALS:")
        for month in months:
            field_name = f"2025 {month}"
            total = new_df[field_name].sum()
            logger.debug(f"  {field_name}: {total:,.2f}")
        
        # Convert DataFrame to list of dictionaries
        projects = new_df.to_dict('records')
        
        # Convert numpy types to Python native types and sanitize values for JSON
        for project in projects:
            for key, value in list(project.items()):
                # Use the sanitize function to clean up any problematic values
                project[key] = sanitize_for_json(value)
        
        # Log the first few projects in a readable format
        logger.debug("\nFirst 5 projects in final format:")
        for i, project in enumerate(projects[:5]):
            logger.debug(f"\nProject {i + 1}:")
            for key, value in project.items():
                logger.debug(f"  {key}: {value}")
        
        logger.debug(f"\nConverted {len(projects)} projects to dictionary format")
        return projects
    except Exception as e:
        logger.error(f"Error in parse_project_data: {str(e)}", exc_info=True)
        raise

def parse_invoice_data(file):
    """
    Parse invoice data from the 'Invoice Data Imported' sheet of an Excel file.
    
    Args:
        file: FileStorage object from Flask request
        
    Returns:
        list: List of dictionaries containing invoice data with fields:
              invoice_id, project_code, invoice_date, payment_amount_usd
    """
    try:
        logger.debug("Starting to parse Invoice Data from Excel file")
        
        # List all sheet names in the Excel file for debugging
        try:
            xls = pd.ExcelFile(file)
            sheet_names = xls.sheet_names
            logger.debug(f"Excel file contains these sheets: {sheet_names}")
        except Exception as e:
            logger.error(f"Error reading Excel file sheet names: {str(e)}")
            return []
        
        # Use the exact sheet name specified
        target_sheet = 'Invoice Data Imported'
        
        # If the target sheet isn't found, try alternative names
        if target_sheet not in sheet_names:
            logger.warning(f"Sheet '{target_sheet}' not found. Available sheets: {sheet_names}")
            
            # Try several possible sheet names for invoice data
            alternative_sheet_names = [
                'Invoice Data',
                'Invoices',
                'Invoice',
                'Payments',
                'Payment',
                'Invoice_Data',
                'invoice data',
                'invoices',
                'payment data',
                'Invoice Table',
                'invoices imported'
            ]
            
            for alt_sheet in alternative_sheet_names:
                if alt_sheet in sheet_names:
                    logger.info(f"Using alternative sheet '{alt_sheet}' for invoice data")
                    target_sheet = alt_sheet
                    break
            else:
                # Try a fuzzy match approach - look for sheets containing invoice-related terms
                for sheet in sheet_names:
                    sheet_lower = sheet.lower()
                    if 'invoice' in sheet_lower or 'payment' in sheet_lower:
                        logger.info(f"Using sheet '{sheet}' which contains invoice-related terms")
                        target_sheet = sheet
                        break
                else:
                    # Last resort: try to use any available sheet except "Project Table"
                    for sheet in sheet_names:
                        if sheet != 'Project Table' and sheet != 'Sheet1' and sheet != 'Sheet2':
                            logger.warning(f"Using '{sheet}' as a last resort for invoice data")
                            target_sheet = sheet
                            break
                    else:
                        logger.error("No suitable invoice data sheet found in the Excel file")
                        return []
        
        # Read the sheet with headers on row 1 (index 0) and data starting from row 2 (index 1)
        try:
            logger.debug(f"Reading sheet: {target_sheet}")
            df = pd.read_excel(file, sheet_name=target_sheet, header=0)
            logger.debug(f"Successfully read sheet with {len(df)} rows and {len(df.columns)} columns")
            
            # If sheet is empty, return empty list
            if len(df) == 0 or df.empty:
                logger.warning(f"Sheet '{target_sheet}' is empty")
                return []
        except Exception as e:
            logger.error(f"Error reading sheet '{target_sheet}': {str(e)}")
            # Try to read without specifying header
            try:
                df = pd.read_excel(file, sheet_name=target_sheet)
                logger.info(f"Successfully read sheet without header specification")
            except:
                return []
        
        # Log the column names and first few rows for debugging
        logger.debug("Column names in sheet:")
        for i, col in enumerate(df.columns):
            logger.debug(f"Column {i}: {col}")
        
        logger.debug("First 3 rows of data:")
        for i in range(min(3, len(df))):
            logger.debug(f"Row {i+1}: {df.iloc[i].to_dict()}")
        
        # Create a new DataFrame to hold the invoice data
        invoices_df = pd.DataFrame()
        
        # DIRECT METHOD: Try to directly use columns A, B, C, and O as specified
        try:
            logger.debug("Attempting direct column extraction from A, B, C, O")
            
            # Check if we have enough columns
            if len(df.columns) >= 15:  # Column O is index 14 (0-based)
                logger.debug("File has enough columns for direct extraction")
                
                # Extract column A (invoice_id)
                invoices_df['invoice_id'] = df.iloc[:, 0].astype(str)
                logger.debug(f"Extracted {len(invoices_df)} invoice IDs from column A (index 0)")
                
                # Extract column B (project_code)
                invoices_df['project_code'] = df.iloc[:, 1].astype(str)
                logger.debug(f"Extracted {len(invoices_df)} project codes from column B (index 1)")
                
                # Extract column C (invoice_date)
                try:
                    invoices_df['invoice_date'] = pd.to_datetime(df.iloc[:, 2], errors='coerce')
                    logger.debug(f"Extracted {len(invoices_df)} invoice dates from column C (index 2)")
                except Exception as date_error:
                    logger.error(f"Error extracting dates from column C: {str(date_error)}")
                    # Use a default date as fallback
                    invoices_df['invoice_date'] = pd.Timestamp.now()
                
                # Extract column O (payment_amount_usd)
                try:
                    # Assuming index 14 corresponds to column O
                    if len(df.columns) > 14:
                        payment_values = df.iloc[:, 14]
                        
                        # If the payment column has string values with currency symbols
                        if payment_values.dtype == 'object':
                            # Remove currency symbols and commas
                            clean_values = payment_values.astype(str).str.replace(r'[$£€,]', '', regex=True)
                            invoices_df['payment_amount_usd'] = pd.to_numeric(clean_values, errors='coerce').fillna(0)
                        else:
                            invoices_df['payment_amount_usd'] = pd.to_numeric(payment_values, errors='coerce').fillna(0)
                            
                        logger.debug(f"Extracted {len(invoices_df)} payment amounts from column O (index 14)")
                    else:
                        logger.warning(f"File doesn't have column O (index 14), looking for numeric columns")
                        # Find a numeric column for payment amount
                        for i in range(3, len(df.columns)):
                            if pd.api.types.is_numeric_dtype(df.iloc[:, i]):
                                logger.info(f"Using column {i} for payment amounts")
                                invoices_df['payment_amount_usd'] = pd.to_numeric(df.iloc[:, i], errors='coerce').fillna(0)
                                break
                        else:
                            logger.warning("No suitable numeric column found for payment amount, using zeros")
                            invoices_df['payment_amount_usd'] = 0
                except Exception as payment_error:
                    logger.error(f"Error extracting payment amounts: {str(payment_error)}")
                    invoices_df['payment_amount_usd'] = 0
                    
                logger.info(f"Direct extraction completed with {len(invoices_df)} invoices")
            else:
                logger.warning(f"File only has {len(df.columns)} columns, not enough for direct extraction")
                # Fall back to the regular method below
                raise ValueError("Not enough columns for direct extraction")
                
        except Exception as direct_extract_error:
            logger.warning(f"Direct column extraction failed: {str(direct_extract_error)}")
            logger.info("Falling back to column header identification method")
            
            # First approach: try to identify columns by headers
            id_columns = ['Invoice ID', 'Invoice Number', 'Invoice #', 'ID', 'Invoice', 'Number']
            project_columns = ['Project Code', 'Project', 'Project ID', 'Project Number', 'Code']
            date_columns = ['Invoice Date', 'Date', 'Payment Date']
            amount_columns = ['Payment Amount (USD)', 'Payment Amount', 'Amount', 'Payment', 'USD', 'Value', 'Total']
            
            # Look for columns with matching headers
            invoice_id_col = None
            project_code_col = None
            invoice_date_col = None
            payment_amount_col = None
            
            # Check each column header against our lists of possible headers
            for i, col in enumerate(df.columns):
                col_str = str(col).lower()
                
                # Check for invoice ID column
                if any(id_name.lower() in col_str for id_name in id_columns):
                    invoice_id_col = i
                    logger.debug(f"Found invoice ID column: {col} (index {i})")
                
                # Check for project code column
                elif any(project_name.lower() in col_str for project_name in project_columns):
                    project_code_col = i
                    logger.debug(f"Found project code column: {col} (index {i})")
                
                # Check for date column
                elif any(date_name.lower() in col_str for date_name in date_columns):
                    invoice_date_col = i
                    logger.debug(f"Found invoice date column: {col} (index {i})")
                
                # Check for amount column
                elif any(amount_name.lower() in col_str for amount_name in amount_columns):
                    payment_amount_col = i
                    logger.debug(f"Found payment amount column: {col} (index {i})")
            
            # If we couldn't identify columns by headers, try using the user's specified positions
            if invoice_id_col is None:
                logger.warning("Could not identify invoice ID column by header, using column A (index 0)")
                invoice_id_col = 0
            
            if project_code_col is None:
                logger.warning("Could not identify project code column by header, using column B (index 1)")
                project_code_col = 1
            
            if invoice_date_col is None:
                logger.warning("Could not identify invoice date column by header, using column C (index 2)")
                invoice_date_col = 2
            
            if payment_amount_col is None:
                logger.warning("Could not identify payment amount column by header, using column O (index 14)")
                # Make sure index 14 (column O) exists
                if len(df.columns) > 14:
                    payment_amount_col = 14
                else:
                    # If not enough columns, try to use the last numeric column as the payment amount
                    logger.warning(f"Sheet only has {len(df.columns)} columns, looking for a numeric column for payment amount")
                    for i in range(len(df.columns) - 1, 2, -1):  # Start from the last column, going backward
                        if pd.api.types.is_numeric_dtype(df.iloc[:, i]):
                            payment_amount_col = i
                            logger.info(f"Using column {i} as payment amount (numeric column)")
                            break
                    else:
                        # If no numeric column found, use the last column
                        payment_amount_col = len(df.columns) - 1
                        logger.warning(f"No suitable numeric column found, using last column ({payment_amount_col}) for payment amount")
            
            # Extract the identified columns
            try:
                invoices_df['invoice_id'] = df.iloc[:, invoice_id_col].astype(str)
                logger.debug(f"Extracted {len(invoices_df)} invoice IDs from column {invoice_id_col}")
            except Exception as e:
                logger.error(f"Error extracting invoice IDs: {str(e)}")
                invoices_df['invoice_id'] = [f"INV{i+1:04d}" for i in range(len(df))]
            
            try:
                invoices_df['project_code'] = df.iloc[:, project_code_col].astype(str)
                logger.debug(f"Extracted {len(invoices_df)} project codes from column {project_code_col}")
            except Exception as e:
                logger.error(f"Error extracting project codes: {str(e)}")
                invoices_df['project_code'] = 'UNKNOWN'
            
            try:
                invoices_df['invoice_date'] = pd.to_datetime(df.iloc[:, invoice_date_col], errors='coerce')
                logger.debug(f"Extracted {len(invoices_df)} invoice dates from column {invoice_date_col}")
                
                # Check if we have valid dates
                valid_dates = invoices_df['invoice_date'].notna().sum()
                logger.debug(f"Found {valid_dates} valid dates out of {len(invoices_df)} entries")
                
                # If most dates are invalid, try alternative formats
                if valid_dates < len(invoices_df) / 2:
                    logger.warning("Most dates are invalid, trying alternative formats")
                    try:
                        # Try European format (DD/MM/YYYY)
                        invoices_df['invoice_date'] = pd.to_datetime(df.iloc[:, invoice_date_col], format='%d/%m/%Y', errors='coerce')
                        valid_dates = invoices_df['invoice_date'].notna().sum()
                        logger.debug(f"After European format: {valid_dates} valid dates")
                    except Exception as e:
                        logger.error(f"Error parsing dates with European format: {str(e)}")
            except Exception as e:
                logger.error(f"Error extracting invoice dates: {str(e)}")
                # Use today's date as fallback
                invoices_df['invoice_date'] = pd.Timestamp.now()
            
            try:
                # Try to extract numeric values, handling different formats
                payment_values = df.iloc[:, payment_amount_col]
                
                # If the payment column has string values with currency symbols
                if payment_values.dtype == 'object':
                    # Remove currency symbols and commas
                    clean_values = payment_values.astype(str).str.replace(r'[$£€,]', '', regex=True)
                    invoices_df['payment_amount_usd'] = pd.to_numeric(clean_values, errors='coerce').fillna(0)
                else:
                    invoices_df['payment_amount_usd'] = pd.to_numeric(payment_values, errors='coerce').fillna(0)
                
                logger.debug(f"Extracted {len(invoices_df)} payment amounts from column {payment_amount_col}")
                logger.debug(f"Payment amount range: min={invoices_df['payment_amount_usd'].min()}, max={invoices_df['payment_amount_usd'].max()}")
            except Exception as e:
                logger.error(f"Error extracting payment amounts: {str(e)}")
                invoices_df['payment_amount_usd'] = 0
        
        # Add month and year fields for easier aggregation
        invoices_df['invoice_month'] = invoices_df['invoice_date'].dt.month
        invoices_df['invoice_month_name'] = invoices_df['invoice_date'].dt.strftime('%b')
        invoices_df['invoice_year'] = invoices_df['invoice_date'].dt.year
        
        # Log summary of extracted data
        logger.debug("\nExtracted invoice data summary:")
        logger.debug(f"Total invoices: {len(invoices_df)}")
        logger.debug(f"Total payment amount: {invoices_df['payment_amount_usd'].sum()}")
        logger.debug(f"Invoices by year: {invoices_df['invoice_year'].value_counts().to_dict()}")
        
        # Log first few rows of processed data
        logger.debug("\nFirst 5 rows of processed invoice data:")
        logger.debug(invoices_df.head().to_string())
        
        # Convert DataFrame to list of dictionaries
        invoices = invoices_df.to_dict('records')
        
        # Convert numpy types to Python native types and sanitize values for JSON
        for invoice in invoices:
            for key, value in list(invoice.items()):
                # Use the sanitize function to clean up any problematic values
                invoice[key] = sanitize_for_json(value)
        
        logger.debug(f"Converted {len(invoices)} invoices to dictionary format")
        return invoices
        
    except Exception as e:
        logger.error(f"Error parsing invoice data: {str(e)}")
        logger.exception("Full traceback:")
        return []  # Return empty list on error 