const fileInput = document.getElementById('file-input');
const fileLabel = document.getElementById('file-label');
const fileInfo = document.getElementById('file-info');
const fileName = document.getElementById('file-name');
const fileSize = document.getElementById('file-size');
const parseBtn = document.getElementById('parse-btn');
const message = document.getElementById('message');
const progressBar = document.getElementById('progress-bar');
const progressFill = document.getElementById('progress-fill');
const loading = document.getElementById('loading');
const chartsSection = document.getElementById('charts-section');
const yearSelector = document.getElementById('year-selector');
const monthlyYearSelector = document.getElementById('monthly-year-selector');
const quarterlyYearSelector = document.getElementById('quarterly-year-selector');

// Global variable to store project data for chart updates
let globalProjectData = [];
let globalRevenueData = [];

// File input change event
fileInput.addEventListener('change', handleFileSelect);

// Drag and drop events
fileLabel.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileLabel.classList.add('dragover');
});

fileLabel.addEventListener('dragleave', () => {
    fileLabel.classList.remove('dragover');
});

fileLabel.addEventListener('drop', (e) => {
    e.preventDefault();
    fileLabel.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files;
        handleFileSelect();
    }
});

function handleFileSelect() {
    const file = fileInput.files[0];
    if (file) {
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        fileInfo.classList.add('show');
        hideMessage();
        
        // Enable parse button immediately
        parseBtn.disabled = false;
        showMessage('File selected. Click "Parse Data" to extract and analyze project data.', 'success');
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Parse button click
parseBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) return;

    showLoading();
    parseBtn.disabled = true;

    try {
        // Read file as base64
        const fileData = await readFileAsBase64(file);
        
        const response = await fetch('/parse', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                file_data: fileData,
                filename: file.name 
            })
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            showMessage(result.message, 'success');
            
            // Show charts section and create charts
            chartsSection.style.display = 'block';
            
            // Store data globally for chart updates
            globalProjectData = result.project_data;
            globalRevenueData = result.rev_totals;
            
            // Set default year to current year
            const currentYear = new Date().getFullYear().toString();
            
            // Set default selections for year selectors
            if (monthlyYearSelector.querySelector(`option[value="${currentYear}"]`)) {
                monthlyYearSelector.value = currentYear;
            }
            if (quarterlyYearSelector.querySelector(`option[value="${currentYear}"]`)) {
                quarterlyYearSelector.value = currentYear;
            }
            
            // Populate year selector for project status chart
            populateYearSelector(result.project_data);
            
            // Create charts
            createMonthlyRevenueChart(result.rev_totals, currentYear);
            createQuarterlyRevenueChart(result.rev_totals, currentYear);
            createExpectedVsActualChart(result.rev_totals, result.invoice_totals_2025);
            createProjectStatusChart(result.project_data);
            
            // Display project insights if available
            if (result.project_insights) {
                displayProjectInsights(result.project_insights);
            }
            
        } else {
            showMessage(result.error || 'Parsing failed', 'error');
        }
        
        parseBtn.disabled = false;
    } catch (error) {
        hideLoading();
        showMessage('Parsing failed: ' + error.message, 'error');
        parseBtn.disabled = false;
    }
});

// Helper function to read file as base64
function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function showProgress() {
    progressBar.style.display = 'block';
    progressFill.style.width = '100%';
}

function hideProgress() {
    setTimeout(() => {
        progressBar.style.display = 'none';
        progressFill.style.width = '0%';
    }, 500);
}

function showLoading() {
    loading.style.display = 'block';
}

function hideLoading() {
    loading.style.display = 'none';
}

function showMessage(text, type) {
    message.textContent = text;
    message.className = `message ${type} show`;
}

function hideMessage() {
    message.classList.remove('show');
}

// Chart creation functions
function createMonthlyRevenueChart(revenueData, year) {
    // Filter data for the selected year
    const filteredData = revenueData.filter(item => item.month.includes(year));
    
    const months = filteredData.map(item => {
        const date = new Date(item.month);
        return date.toLocaleDateString('en-US', { month: 'short' });
    });
    const revenues = filteredData.map(item => item.revenue_total);
    
    const trace = {
        x: months,
        y: revenues,
        type: 'bar',
        marker: {
            color: '#667eea',
            line: { color: '#5a6fd8', width: 1 }
        },
        name: `${year} Monthly Revenue`
    };
    
    const layout = {
        title: {
            text: `Monthly Revenue for ${year}`,
            font: { size: 16, color: '#333' }
        },
        xaxis: { title: 'Month' },
        yaxis: { 
            title: 'Revenue ($)',
            tickformat: ',.0f'
        },
        margin: { l: 80, r: 40, t: 60, b: 50 }
    };
    
    Plotly.newPlot('monthly-revenue-chart', [trace], layout, {responsive: true});
}

function createQuarterlyRevenueChart(revenueData, year) {
    // Filter data for the selected year
    const filteredData = revenueData.filter(item => item.month.includes(year));
    
    // Group by quarters
    const quarters = ['Q1', 'Q2', 'Q3', 'Q4'];
    const quarterlyTotals = [0, 0, 0, 0];
    
    filteredData.forEach((item, index) => {
        const quarterIndex = Math.floor(index / 3);
        quarterlyTotals[quarterIndex] += item.revenue_total;
    });
    
    const trace = {
        x: quarters,
        y: quarterlyTotals,
        type: 'bar',
        marker: {
            color: '#28a745',
            line: { color: '#1e7e34', width: 1 }
        },
        name: `${year} Quarterly Revenue`
    };
    
    const layout = {
        title: {
            text: `Quarterly Revenue for ${year}`,
            font: { size: 16, color: '#333' }
        },
        xaxis: { title: 'Quarter' },
        yaxis: { 
            title: 'Revenue ($)',
            tickformat: ',.0f'
        },
        margin: { l: 80, r: 40, t: 60, b: 50 }
    };
    
    Plotly.newPlot('quarterly-revenue-chart', [trace], layout, {responsive: true});
}

function createExpectedVsActualChart(revenueData, invoiceData) {
    // Filter for only 2025 data (keep this chart fixed to 2025)
    const revenueData2025 = revenueData.filter(item => item.month.includes('2025'));
    
    const months = revenueData2025.map(item => {
        const date = new Date(item.month);
        return date.toLocaleDateString('en-US', { month: 'short' });
    });
    
    const expectedRevenues = revenueData2025.map(item => item.revenue_total);
    const actualRevenues = invoiceData.map(item => item.invoice_total);
    
    const trace1 = {
        x: months,
        y: expectedRevenues,
        type: 'bar',
        name: 'Expected Revenue',
        marker: { color: '#667eea' }
    };
    
    const trace2 = {
        x: months,
        y: actualRevenues,
        type: 'bar',
        name: 'Actual Invoices',
        marker: { color: '#fd7e14' }
    };
    
    const layout = {
        title: {
            text: 'Expected vs Actual Revenue 2025',
            font: { size: 16, color: '#333' }
        },
        xaxis: { title: 'Month' },
        yaxis: { 
            title: 'Revenue ($)',
            tickformat: ',.0f'
        },
        barmode: 'group',
        margin: { l: 80, r: 40, t: 60, b: 50 }
    };
    
    Plotly.newPlot('expected-vs-actual-chart', [trace1, trace2], layout, {responsive: true});
}

function createProjectStatusChart(projectData, selectedYear = 'all') {
    // Filter data by year if specified
    let filteredData = projectData;
    if (selectedYear !== 'all') {
        filteredData = projectData.filter(project => {
            const projectYear = project['Year'];
            return projectYear && projectYear.toString() === selectedYear.toString();
        });
    }
    
    // Count project statuses
    const statusCounts = {};
    filteredData.forEach(project => {
        const status = project['Project Status'] || 'Unknown';
        statusCounts[status] = (statusCounts[status] || 0) + 1;
    });
    
    const labels = Object.keys(statusCounts);
    const values = Object.values(statusCounts);
    
    const trace = {
        labels: labels,
        values: values,
        type: 'pie',
        hole: 0.4,
        marker: {
            colors: ['#667eea', '#28a745', '#fd7e14', '#6f42c1', '#dc3545', '#17a2b8', '#ffc107']
        },
        textinfo: 'label+percent',
        textposition: 'outside'
    };
    
    const yearText = selectedYear === 'all' ? 'All Years' : selectedYear;
    const layout = {
        title: {
            text: `Project Status Distribution (${yearText})`,
            font: { size: 16, color: '#333' }
        },
        margin: { l: 40, r: 40, t: 60, b: 40 },
        showlegend: true,
        legend: {
            orientation: 'v',
            x: 1.02,
            y: 0.5
        }
    };
    
    Plotly.newPlot('project-status-chart', [trace], layout, {responsive: true});
}

function populateYearSelector(projectData) {
    // Get unique years from project data
    const years = [...new Set(projectData.map(project => project['Year']))].filter(year => year != null).sort();
    
    // Clear existing options except "All Years"
    yearSelector.innerHTML = '<option value="all">All Years</option>';
    
    // Add year options
    years.forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelector.appendChild(option);
    });
}

// Year selector event listeners
yearSelector.addEventListener('change', function() {
    const selectedYear = this.value;
    createProjectStatusChart(globalProjectData, selectedYear);
});

monthlyYearSelector.addEventListener('change', function() {
    const selectedYear = this.value;
    createMonthlyRevenueChart(globalRevenueData, selectedYear);
});

quarterlyYearSelector.addEventListener('change', function() {
    const selectedYear = this.value;
    createQuarterlyRevenueChart(globalRevenueData, selectedYear);
});

// Function to display project insights
function displayProjectInsights(insightsData) {
    // Create insights section if it doesn't exist
    let insightsSection = document.getElementById('insights-section');
    if (!insightsSection) {
        insightsSection = document.createElement('div');
        insightsSection.id = 'insights-section';
        insightsSection.className = 'insights-section';
        insightsSection.style.marginTop = '30px';
        
        // Insert after the charts section
        const chartsSection = document.getElementById('charts-section');
        chartsSection.parentNode.insertBefore(insightsSection, chartsSection.nextSibling);
    }
    
    // Clear previous content
    insightsSection.innerHTML = '';
    
    if (insightsData.success) {
        const metrics = insightsData.metrics;
        const insights = insightsData.insights;
        
        insightsSection.innerHTML = `
            <h3>🧠 AI-Generated Project Insights</h3>
            <div class="insights-metrics">
                <div class="metric-card">
                    <div class="metric-value">${metrics.project_count}</div>
                    <div class="metric-label">Current Year Projects</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">$${metrics.total_revenue.toLocaleString()}</div>
                    <div class="metric-label">Total Revenue</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">$${metrics.avg_revenue.toLocaleString()}</div>
                    <div class="metric-label">Avg Revenue/Project</div>
                </div>
            </div>
            <div class="insights-content">
                <div class="insights-text" id="insights-markdown"></div>
            </div>
        `;
        
        // Parse and render markdown content
        const markdownElement = document.getElementById('insights-markdown');
        if (markdownElement && typeof marked !== 'undefined') {
            markdownElement.innerHTML = marked.parse(insights);
        } else {
            // Fallback if marked.js isn't available
            markdownElement.innerHTML = insights.replace(/\n/g, '<br>');
        }
        
        insightsSection.style.display = 'block';
        console.log('Project insights generated:', insightsData);
        
    } else {
        insightsSection.innerHTML = `
            <h3>🧠 AI-Generated Project Insights</h3>
            <div class="insights-error">
                <p>⚠️ Failed to generate insights: ${insightsData.error}</p>
                <div class="insights-metrics">
                    <div class="metric-card">
                        <div class="metric-value">${insightsData.metrics.project_count}</div>
                        <div class="metric-label">Current Year Projects</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">$${insightsData.metrics.total_revenue.toLocaleString()}</div>
                        <div class="metric-label">Total Revenue</div>
                    </div>
                </div>
            </div>
        `;
        
        insightsSection.style.display = 'block';
        console.log('Failed to generate insights:', insightsData.error);
    }
} 