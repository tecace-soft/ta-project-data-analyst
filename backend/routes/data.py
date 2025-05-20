from flask import Blueprint, jsonify, request, current_app
from backend.utils.parser import parse_project_data, parse_invoice_data
import logging
from werkzeug.utils import secure_filename
import os
import json
import tempfile
import glob
import math

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

data_bp = Blueprint('data', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'xlsm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@data_bp.route('/api/data', methods=['POST'])
def get_data():
    """Get project data from uploaded Excel file"""
    temp_fd = None
    temp_path = None
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Get file metadata and sheet names
        file_info = {
            'name': file.filename,
            'type': file.content_type,
            'sheetNames': []
        }
        
        # Create a copy of the file in memory to avoid file locking issues
        file_content = file.read()
        
        # Get a temporary file name but don't create it yet
        temp_fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1])
        
        # Close the file descriptor immediately to avoid file locking
        os.close(temp_fd)
        temp_fd = None
        
        # Write the content to the temporary file
        with open(temp_path, 'wb') as f:
            f.write(file_content)
            
        logger.debug(f"Saved temporary file at: {temp_path}")
        
        # Get sheet names
        try:
            import pandas as pd
            xls = pd.ExcelFile(temp_path)
            file_info['sheetNames'] = xls.sheet_names
            logger.debug(f"Excel file contains sheets: {file_info['sheetNames']}")
        except Exception as e:
            logger.error(f"Error getting sheet names: {str(e)}")
            
        # Parse the Excel file for project data
        logger.debug(f"Processing file: {file.filename}")
        
        try:
            with open(temp_path, 'rb') as project_file:
                projects = parse_project_data(project_file)
        except Exception as e:
            logger.error(f"Error parsing project data: {str(e)}")
            projects = []
        
        # Parse the Excel file for invoice data
        try:
            with open(temp_path, 'rb') as invoice_file:
                invoices = parse_invoice_data(invoice_file)
        except Exception as e:
            logger.error(f"Error parsing invoice data: {str(e)}")
            invoices = []
        
        # Log the number of invoices found
        logger.debug(f"Processed {len(invoices)} invoices")
        
        # Log the first project's data types for debugging
        if projects:
            first_project = projects[0]
            logger.debug("First project data types:")
            for key, value in first_project.items():
                logger.debug(f"{key}: {type(value)} = {value}")
        
        logger.debug(f"Successfully processed {len(projects)} projects")
        
        # If invoice data is empty, try one more approach - check for sheets containing specific patterns
        if len(invoices) == 0 and temp_path:
            logger.warning("No invoices found with standard approach, trying alternative methods")
            try:
                # Look for any sheet containing 'payment' or similar words
                for sheet_name in file_info['sheetNames']:
                    sheet_lower = sheet_name.lower()
                    if any(term in sheet_lower for term in ['payment', 'invoice', 'bill', 'receipt', 'transaction']):
                        logger.info(f"Trying to extract invoice data from sheet '{sheet_name}'")
                        try:
                            df = pd.read_excel(temp_path, sheet_name=sheet_name)
                            
                            # Check if this sheet has the minimum columns we need
                            if len(df.columns) >= 3:  # At minimum we need ID, date, and amount
                                logger.debug(f"Sheet '{sheet_name}' has {len(df.columns)} columns, attempting extraction")
                                
                                # Create a simple invoice structure
                                temp_invoices = []
                                for i in range(len(df)):
                                    try:
                                        # Get data from first 3 columns
                                        invoice_id = str(df.iloc[i, 0]) if pd.notna(df.iloc[i, 0]) else f"INV{i+1:04d}"
                                        
                                        # Try to determine project code
                                        project_code = "UNKNOWN"
                                        for j in range(1, min(5, len(df.columns))):
                                            if pd.notna(df.iloc[i, j]):
                                                val = str(df.iloc[i, j])
                                                # Look for something that might be a project code
                                                if ('PRJ' in val or 'PROJ' in val or val.isalnum()) and len(val) < 20:
                                                    project_code = val
                                                    break
                                        
                                        # Try to find a date column
                                        invoice_date = None
                                        for j in range(1, min(6, len(df.columns))):
                                            cell_value = df.iloc[i, j]
                                            if isinstance(cell_value, (pd.Timestamp, pd.DatetimeTZDtype)):
                                                invoice_date = cell_value
                                                break
                                            elif pd.notna(cell_value):
                                                try:
                                                    parsed_date = pd.to_datetime(cell_value)
                                                    if not pd.isna(parsed_date):
                                                        invoice_date = parsed_date
                                                        break
                                                except:
                                                    pass
                                        
                                        # Default to today if no date found
                                        if invoice_date is None:
                                            invoice_date = pd.Timestamp.now()
                                        
                                        # Try to find a numeric column for payment amount
                                        payment_amount = 0
                                        for j in range(1, len(df.columns)):
                                            if pd.api.types.is_numeric_dtype(df.iloc[:, j]):
                                                val = df.iloc[i, j]
                                                if pd.notna(val) and val > 0:
                                                    payment_amount = float(val)
                                                    break
                                        
                                        # Create invoice object
                                        invoice = {
                                            'invoice_id': invoice_id,
                                            'project_code': project_code,
                                            'invoice_date': str(invoice_date),
                                            'payment_amount_usd': payment_amount,
                                            'invoice_month': invoice_date.month,
                                            'invoice_month_name': invoice_date.strftime('%b'),
                                            'invoice_year': invoice_date.year
                                        }
                                        temp_invoices.append(invoice)
                                    except Exception as row_error:
                                        logger.error(f"Error processing row {i}: {str(row_error)}")
                                
                                # If we extracted anything useful, use it
                                if temp_invoices:
                                    logger.info(f"Extracted {len(temp_invoices)} invoices from sheet '{sheet_name}' using alternative method")
                                    invoices = temp_invoices
                                    break
                        except Exception as sheet_error:
                            logger.error(f"Error processing sheet '{sheet_name}': {str(sheet_error)}")
            except Exception as alt_error:
                logger.error(f"Error in alternative invoice extraction: {str(alt_error)}")
        
        # Convert projects to JSON-serializable format
        serializable_projects = []
        for project in projects:
            serializable_project = {}
            for key, value in project.items():
                # Convert key to string
                str_key = str(key)
                # Handle NaN values which cause JSON serialization errors
                if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                    serializable_project[str_key] = None
                # Handle value based on type
                elif isinstance(value, (int, float, str, bool, type(None))):
                    serializable_project[str_key] = value
                else:
                    serializable_project[str_key] = str(value)
            serializable_projects.append(serializable_project)
        
        # Convert invoices to JSON-serializable format
        serializable_invoices = []
        for invoice in invoices:
            serializable_invoice = {}
            for key, value in invoice.items():
                # Convert key to string
                str_key = str(key)
                # Handle NaN values which cause JSON serialization errors
                if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                    serializable_invoice[str_key] = None
                # Handle value based on type
                elif isinstance(value, (int, float, str, bool, type(None))):
                    serializable_invoice[str_key] = value
                else:
                    serializable_invoice[str_key] = str(value)
            serializable_invoices.append(serializable_invoice)
        
        # Add counts to file info
        file_info['projectCount'] = len(serializable_projects)
        file_info['invoiceCount'] = len(serializable_invoices)
        
        # Check for duplicate projects
        if projects:
            project_codes = [p.get('Project Code', '') for p in projects]
            unique_codes = set(project_codes)
            logger.debug(f"Total projects: {len(projects)}, Unique project codes: {len(unique_codes)}")
            
            if len(unique_codes) < len(projects):
                logger.warning(f"WARNING: {len(projects) - len(unique_codes)} duplicate projects found!")
                
                # Find the duplicates
                duplicates = []
                seen = set()
                for code in project_codes:
                    if code in seen and code not in duplicates:
                        duplicates.append(code)
                    seen.add(code)
                
                logger.warning(f"Duplicate project codes: {duplicates}")
                
                # CRITICAL FIX: Remove duplicates before sending to frontend
                unique_projects = []
                seen_codes = set()
                
                for project in projects:
                    code = project.get('Project Code', '')
                    if code not in seen_codes:
                        seen_codes.add(code)
                        unique_projects.append(project)
                
                logger.info(f"After deduplication: {len(unique_projects)} unique projects")
                projects = unique_projects
        
        # Return both projects and invoices in the response
        response_data = {
            'projects': serializable_projects,
            'invoices': serializable_invoices,
            'fileInfo': file_info
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Always cleanup temporary file
        try:
            if temp_fd is not None:
                os.close(temp_fd)
            if temp_path is not None and os.path.exists(temp_path):
                os.remove(temp_path)
                logger.debug(f"Cleaned up temporary file: {temp_path}")
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up temporary file: {str(cleanup_error)}")

@data_bp.route('/api/check-invoice-data', methods=['GET'])
def check_invoice_data():
    """Diagnostic endpoint to check for invoice data in sample files"""
    try:
        results = {}
        
        # Look for Excel files in the current directory and parent directories
        search_paths = [
            '*.xlsx', '*.xls', '*.xlsm',  # Current directory
            '../*.xlsx', '../*.xls', '../*.xlsm',  # Parent directory
            '../../*.xlsx', '../../*.xls', '../../*.xlsm',  # Grandparent directory
            # Add sample/test data directory if it exists
            'sample_data/*.xlsx', 'sample_data/*.xls', 'sample_data/*.xlsm',
            'test_data/*.xlsx', 'test_data/*.xls', 'test_data/*.xlsm',
            # Look in user's documents folder for Windows
            os.path.expanduser('~/Documents/*.xlsx'), 
            os.path.expanduser('~/Documents/*.xls'),
            os.path.expanduser('~/Documents/*.xlsm')
        ]
        
        found_files = []
        for pattern in search_paths:
            found_files.extend(glob.glob(pattern))
        
        logger.debug(f"Found {len(found_files)} Excel files to check")
        results['found_files'] = found_files
        
        # Check each file for invoice data
        file_results = []
        for file_path in found_files[:5]:  # Limit to first 5 files to avoid overload
            try:
                logger.debug(f"Checking file: {file_path}")
                with open(file_path, 'rb') as file:
                    # Get all sheet names
                    try:
                        import pandas as pd
                        xls = pd.ExcelFile(file)
                        sheet_names = xls.sheet_names
                        logger.debug(f"File {file_path} contains sheets: {sheet_names}")
                    except Exception as e:
                        logger.error(f"Error reading sheet names from {file_path}: {str(e)}")
                        sheet_names = []
                
                # Reset file pointer and try to parse invoice data
                with open(file_path, 'rb') as file:
                    invoices = parse_invoice_data(file)
                    
                file_result = {
                    'file_path': file_path,
                    'sheet_names': sheet_names,
                    'invoice_count': len(invoices),
                    'has_invoice_data': len(invoices) > 0
                }
                
                # Include sample of invoice data if available
                if invoices and len(invoices) > 0:
                    sample_invoice = invoices[0]
                    # Convert any non-serializable types
                    sample = {}
                    for key, value in sample_invoice.items():
                        if isinstance(value, (int, float, str, bool, type(None))):
                            sample[key] = value
                        else:
                            sample[key] = str(value)
                    file_result['sample_invoice'] = sample
                
                file_results.append(file_result)
                
            except Exception as e:
                logger.error(f"Error checking file {file_path}: {str(e)}")
                file_results.append({
                    'file_path': file_path,
                    'error': str(e)
                })
        
        results['file_results'] = file_results
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in check-invoice-data endpoint: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({'error': str(e)}), 500

@data_bp.route('/api/excel-diagnostic', methods=['POST'])
def excel_diagnostic():
    """Diagnostic endpoint to inspect Excel file structure"""
    temp_fd = None
    temp_path = None
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Save the file temporarily
        import pandas as pd
        
        # Create a copy of the file in memory to avoid file locking issues
        file_content = file.read()
        
        # Get a temporary file name but don't create it yet
        import tempfile
        temp_fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1])
        
        # Close the file descriptor immediately to avoid file locking
        os.close(temp_fd)
        temp_fd = None
        
        # Write the content to the temporary file
        with open(temp_path, 'wb') as f:
            f.write(file_content)
            
        logger.debug(f"Saved temporary file at: {temp_path}")
        
        # Analyze the Excel file
        results = {
            'file_name': file.filename,
            'sheet_count': 0,
            'sheet_names': [],
            'sheets': {}
        }
        
        # Get sheet names using pandas - this handles file closing for us
        try:
            xls = pd.ExcelFile(temp_path)
            results['sheet_names'] = xls.sheet_names
            results['sheet_count'] = len(xls.sheet_names)
            
            # Analyze each sheet
            for sheet_name in results['sheet_names']:
                sheet_data = {
                    'row_count': 0,
                    'column_count': 0,
                    'columns': [],
                    'sample_rows': []
                }
                
                try:
                    # Read the sheet
                    df = pd.read_excel(temp_path, sheet_name=sheet_name)
                    sheet_data['row_count'] = len(df)
                    sheet_data['column_count'] = len(df.columns)
                    
                    # Get column information
                    for i, col in enumerate(df.columns):
                        col_info = {
                            'index': i,
                            'name': str(col),
                            'excel_column': chr(65 + i) if i < 26 else chr(64 + i // 26) + chr(65 + i % 26),
                            'data_type': str(df[col].dtype)
                        }
                        sheet_data['columns'].append(col_info)
                    
                    # Get sample rows
                    sample_count = min(5, len(df))
                    for i in range(sample_count):
                        # Convert row to serializable format
                        row_dict = {}
                        for j, col in enumerate(df.columns):
                            value = df.iloc[i, j]
                            if isinstance(value, (int, float, str, bool)) or value is None:
                                row_dict[str(col)] = value
                            else:
                                row_dict[str(col)] = str(value)
                        sheet_data['sample_rows'].append(row_dict)
                    
                except Exception as e:
                    sheet_data['error'] = str(e)
                
                # Add sheet data to results
                results['sheets'][sheet_name] = sheet_data
            
            del xls  # Explicitly delete to release file handle
            
        except Exception as e:
            logger.error(f"Error analyzing Excel file: {str(e)}")
            return jsonify({'error': f'Error analyzing Excel structure: {str(e)}'}), 500
        
        return jsonify(results)
            
    except Exception as e:
        logger.error(f"Error in Excel diagnostic: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Always cleanup temporary file
        try:
            if temp_fd is not None:
                os.close(temp_fd)
            if temp_path is not None and os.path.exists(temp_path):
                os.remove(temp_path)
                logger.debug(f"Cleaned up temporary file: {temp_path}")
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up temporary file: {str(cleanup_error)}") 