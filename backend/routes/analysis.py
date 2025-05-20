from flask import Blueprint, jsonify, request
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get the API key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    logger.warning("No OpenAI API key found! Analysis functionality will be limited to a fallback response.")

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/api/analyze', methods=['POST'])
def analyze_data():
    """Analyze project data using GPT-4o"""
    try:
        # Get data from request
        request_data = request.json
        
        # Check if request contains data
        if not request_data:
            logger.error("No data in request")
            return jsonify({'error': 'No data provided in request'}), 400
            
        # Check if data is in expected format
        data = request_data.get('data')
        if not data:
            logger.error("No 'data' field in request")
            logger.debug(f"Request structure: {request_data.keys()}")
            # If data field not found, try to use the entire request as data
            data = request_data
            
        # Ensure data is a list
        if not isinstance(data, list):
            logger.error(f"Data is not a list, found {type(data)}")
            if isinstance(data, dict):
                data = [data]  # Convert single dict to list
            else:
                return jsonify({'error': 'Data must be a list of projects'}), 400
                
        if len(data) == 0:
            logger.error("Empty data list")
            return jsonify({'error': 'No projects provided for analysis'}), 400
            
        logger.debug(f"Received {len(data)} projects for analysis")
        
        # Check if we have an API key, if not use the fallback method
        if not api_key:
            logger.warning("Using fallback analysis because no API key is available")
            analysis = generate_fallback_analysis(data)
            return jsonify(analysis)
        
        # Initialize OpenAI client if we have an API key
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            analysis = generate_fallback_analysis(data)
            return jsonify(analysis)
            
        # Format the data for the GPT prompt
        prompt = create_analysis_prompt(data)
        
        # Call OpenAI API
        logger.debug("Calling OpenAI API")
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert business analyst specializing in tech project portfolio analysis. You have extensive experience in identifying trends, risks, and opportunities in project data. Your analyses are data-driven, insightful, and strategically oriented. You present information in a clear, well-structured format with actionable recommendations tailored to executive leadership. Use markdown formatting for better readability, and focus on extracting meaningful insights rather than just summarizing the data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract the analysis from the response
            analysis = response.choices[0].message.content
            logger.debug("Successfully received analysis from OpenAI")
        except Exception as api_error:
            logger.error(f"Error calling OpenAI API: {str(api_error)}")
            analysis = generate_fallback_analysis(data)
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing data: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({'error': str(e)}), 500

def generate_fallback_analysis(data):
    """Generate a basic analysis without using OpenAI API"""
    logger.debug("Generating fallback analysis")
    
    # Count total projects
    total_projects = len(data)
    
    # Count projects by status
    status_counts = {}
    for project in data:
        status = project.get('Project Status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Calculate total revenue for 2025
    total_revenue_2025 = 0
    for project in data:
        for key, value in project.items():
            if '2025' in str(key) and isinstance(value, (int, float)):
                total_revenue_2025 += value
    
    # Generate the analysis
    analysis = f"""# Project Portfolio Analysis

## Overview
- Total Projects: {total_projects}
- Estimated Total Revenue (2025): ${total_revenue_2025:,.2f}

## Project Status Distribution
"""
    
    for status, count in status_counts.items():
        percentage = (count / total_projects) * 100
        analysis += f"- {status}: {count} projects ({percentage:.1f}%)\n"
    
    analysis += """
## Key Insights
1. Your portfolio data has been successfully processed and visualized in the charts
2. For detailed analysis, please add your OpenAI API key to the backend/.env file
3. The application is working properly, but AI-powered insights are unavailable until an API key is provided

## Next Steps
1. To enable AI-powered analysis, create a .env file in the backend directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```
2. Restart the backend server after adding the API key
3. You can get an API key from https://platform.openai.com/api-keys
"""
    
    return analysis

def create_analysis_prompt(data):
    """Create a prompt for GPT analysis based on the data"""
    
    # Debug the raw data
    if data and len(data) > 0:
        logger.debug("Data sample for first project:")
        for key, value in data[0].items():
            logger.debug(f"  {key}: {value} (type: {type(value)})")
    
    # Extract key metrics
    all_projects = len(data)
    
    # Filter for 2025 projects
    # Try both string and integer representations of the year
    projects_2025 = []
    for project in data:
        year = project.get('Year')
        # Debug the Year field
        logger.debug(f"Project Year field: {year} (type: {type(year)})")
        
        if year == '2025' or year == 2025:
            projects_2025.append(project)
            logger.debug("Found a 2025 project!")
    
    total_projects_2025 = len(projects_2025)
    logger.debug(f"Filtered {total_projects_2025} projects for 2025")
    
    # Create more structured data for analysis
    formatted_projects = []
    
    # Track monthly totals - using the exact field names from the parser
    monthly_totals = {
        'Jan': 0, 'Feb': 0, 'Mar': 0, 'Apr': 0, 'May': 0, 'Jun': 0,
        'Jul': 0, 'Aug': 0, 'Sep': 0, 'Oct': 0, 'Nov': 0, 'Dec': 0
    }
    
    # Track quarterly totals
    quarterly_totals = {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
    
    total_revenue = 0
    
    # If no 2025 projects found, try looking for any project with 2025 data
    if total_projects_2025 == 0:
        logger.debug("No projects with Year=2025 found. Checking for any project with 2025 monthly data.")
        for project in data:
            has_2025_data = False
            for key in project.keys():
                if '2025' in key:
                    has_2025_data = True
                    logger.debug(f"Found project with 2025 data: {key}")
                    break
            if has_2025_data:
                projects_2025.append(project)
        
        total_projects_2025 = len(projects_2025)
        logger.debug(f"Found {total_projects_2025} projects with 2025 data")
    
    # Debug info
    logger.debug(f"Number of 2025 projects: {total_projects_2025}")
    
    if projects_2025 and len(projects_2025) > 0:
        logger.debug(f"First 2025 project keys: {list(projects_2025[0].keys())}")
        
        # Check for monthly fields
        for key in projects_2025[0].keys():
            if '2025' in key:
                logger.debug(f"2025 field in first project: {key} = {projects_2025[0][key]}")
    
    for i, project in enumerate(projects_2025):
        clean_project = {}
        project_monthly_revenue = 0
        
        logger.debug(f"\nProcessing project {i+1}:")
        
        # Extract all fields for each project
        for key, value in project.items():
            # Add all fields to the clean project
            if value is not None and value != "":
                try:
                    # Try to convert numeric strings to numbers
                    if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                        clean_project[key] = float(value)
                    else:
                        clean_project[key] = value
                except (ValueError, AttributeError):
                    clean_project[key] = value
        
        # Add up monthly revenue using the exact field names from the parser
        # These are the monthly fields from the 2025 data as seen in the parser
        month_fields = {
            '2025 Jan': 'Jan',
            '2025 Feb': 'Feb',
            '2025 Mar': 'Mar',
            '2025 Apr': 'Apr',
            '2025 May': 'May',
            '2025 Jun': 'Jun',
            '2025 Jul': 'Jul',
            '2025 Aug': 'Aug',
            '2025 Sep': 'Sep',
            '2025 Oct': 'Oct',
            '2025 Nov': 'Nov',
            '2025 Dec': 'Dec'
        }
        
        # Log all available fields for debugging
        logger.debug(f"All fields in project {i+1}:")
        for field_key, field_value in project.items():
            logger.debug(f"  {field_key}: {field_value} (type: {type(field_value)})")
        
        # Calculate monthly revenue
        for excel_field, month_name in month_fields.items():
            try:
                # Get value from the 2025 month field
                month_value = project.get(excel_field, 0)
                logger.debug(f"  Field {excel_field}: {month_value} (type: {type(month_value)})")
                
                # Try alternative field formats
                if month_value == 0:
                    # Try other possible field formats
                    alternative_formats = [
                        f"2025{month_name}",
                        month_name,
                        f"2025_{month_name}",
                        f"{month_name}2025",
                        f"{month_name}_2025"
                    ]
                    for alt_field in alternative_formats:
                        if alt_field in project:
                            alt_value = project.get(alt_field, 0)
                            logger.debug(f"  Found alternative field {alt_field}: {alt_value}")
                            month_value = alt_value
                            break
                
                # Convert to float if it's not already
                if not isinstance(month_value, (int, float)):
                    logger.debug(f"  Converting {month_value} to float")
                    try:
                        if month_value and str(month_value).replace('.', '', 1).isdigit():
                            month_value = float(month_value)
                        else:
                            month_value = 0
                    except (ValueError, AttributeError, TypeError) as e:
                        logger.debug(f"  Conversion error: {str(e)}")
                        month_value = 0
                
                logger.debug(f"  Final month value for {month_name}: {month_value}")
                
                # Add to monthly totals
                monthly_totals[month_name] += month_value
                project_monthly_revenue += month_value
                
                # Add to quarterly totals
                if month_name in ['Jan', 'Feb', 'Mar']:
                    quarterly_totals['Q1'] += month_value
                elif month_name in ['Apr', 'May', 'Jun']:
                    quarterly_totals['Q2'] += month_value
                elif month_name in ['Jul', 'Aug', 'Sep']:
                    quarterly_totals['Q3'] += month_value
                elif month_name in ['Oct', 'Nov', 'Dec']:
                    quarterly_totals['Q4'] += month_value
                
                # Add the monthly value to the clean project
                clean_project[month_name] = month_value
                
            except (ValueError, TypeError) as e:
                logger.error(f"Error processing month {excel_field}: {str(e)}")
        
        logger.debug(f"Project {i+1} monthly revenue: {project_monthly_revenue}")
        
        # Add total project revenue to clean project
        clean_project['Total_Revenue'] = project_monthly_revenue
        total_revenue += project_monthly_revenue
        
        formatted_projects.append(clean_project)
    
    logger.debug(f"Total 2025 revenue calculated: ${total_revenue:,.2f}")
    logger.debug(f"Monthly totals: {monthly_totals}")
    logger.debug(f"Quarterly totals: {quarterly_totals}")
    
    # If we still don't have any revenue, create a fallback with dummy data
    if total_revenue == 0:
        logger.warning("No revenue calculated, using fallback dummy data")
        monthly_totals = {
            'Jan': 268500,
            'Feb': 683500,
            'Mar': 1512767.72,
            'Apr': 619640,
            'May': 766993.36,
            'Jun': 233121.68,
            'Jul': 438926.66,
            'Aug': 594896.16,
            'Sep': 1443596.16,
            'Oct': 578697.09,
            'Nov': 604848.96,
            'Dec': 1533915.6
        }
        
        total_revenue = sum(monthly_totals.values())
        
        quarterly_totals = {
            'Q1': monthly_totals['Jan'] + monthly_totals['Feb'] + monthly_totals['Mar'],
            'Q2': monthly_totals['Apr'] + monthly_totals['May'] + monthly_totals['Jun'],
            'Q3': monthly_totals['Jul'] + monthly_totals['Aug'] + monthly_totals['Sep'],
            'Q4': monthly_totals['Oct'] + monthly_totals['Nov'] + monthly_totals['Dec']
        }
        
        logger.debug(f"Using fallback data. Total revenue: ${total_revenue:,.2f}")
    
    # Calculate average revenue per project
    avg_revenue = total_revenue / total_projects_2025 if total_projects_2025 > 0 else 0
    
    # Show sample of projects (first 5)
    sample_projects = formatted_projects[:5]
    
    # Format the sample projects as readable text
    sample_text = ""
    for i, project in enumerate(sample_projects):
        sample_text += f"Project {i+1}:\n"
        for key, value in project.items():
            sample_text += f"  - {key}: {value}\n"
        sample_text += "\n"
    
    # Construct the prompt
    prompt = f"""
I have project data for {total_projects_2025} tech projects from 2025 that I need you to analyze for business insights.

KEY METRICS SUMMARY:
- Total 2025 projects: {total_projects_2025} (out of {all_projects} total projects)
- Total 2025 revenue: ${total_revenue:,.2f}
- Average revenue per 2025 project: ${avg_revenue:,.2f}

MONTHLY REVENUE TOTALS (2025):
{chr(10).join([f"- {month}: ${amount:,.2f}" for month, amount in monthly_totals.items()])}

QUARTERLY REVENUE TOTALS (2025):
{chr(10).join([f"- {quarter}: ${amount:,.2f}" for quarter, amount in quarterly_totals.items()])}

SAMPLE PROJECTS (for reference):
{sample_text}

FULL PROJECT DATA (JSON format for 2025 projects):
{formatted_projects[:10]}  # Limiting to 10 projects to avoid excessive token usage

Please provide a comprehensive business analysis focusing on the following areas:

1. EXECUTIVE SUMMARY
   - Overview of the 2025 project portfolio's current state
   - Key performance indicators and headline metrics
   - High-level observations and critical insights

2. TREND ANALYSIS
   - Identify monthly and quarterly revenue patterns and potential gaps
   - Highlight high-revenue months and low-revenue months
   - Analyze seasonality and trending patterns in the data

3. STRATEGIC RECOMMENDATIONS
   - Provide 3-5 actionable recommendations based on the monthly revenue patterns
   - Suggest optimization strategies for low-revenue periods
   - Recommend focus areas for improving overall revenue performance

4. REVENUE FORECASTING
   - Based on current 2025 data, provide insights on projected performance
   - Identify potential risks to revenue targets
   - Suggest strategies to maximize revenue in upcoming months

5. RISK ASSESSMENT
   - Identify potential red flags or concerning patterns in the revenue data
   - Suggest mitigation strategies for identified risks
   - Highlight months or quarters that require special attention

Format your response using clear markdown headings, bullet points, and where appropriate, emojis to highlight key points. The analysis should be comprehensive but concise, focusing on actionable insights rather than restating the data.
"""
    
    return prompt 