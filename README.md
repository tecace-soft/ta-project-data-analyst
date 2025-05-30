# Technical Analysis Data Visualization App

A comprehensive React and Flask application for analyzing and visualizing project revenue data with AI-powered insights.

## 🚀 Features

- **Excel Data Import**: Upload and process project data from Excel files
- **Interactive Charts**: Monthly and quarterly revenue visualization with Plotly.js
- **AI Analysis**: Generate business insights using OpenAI GPT-4 (optional)
- **Chat Interface**: Interactive chat window for data queries via webhook integration
- **Invoice Tracking**: Compare expected vs actualized revenue
- **Project Status Dashboard**: Visualize project distribution and status

## 📋 Prerequisites

- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **npm** or **yarn**

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd ta-project-data-analyst
```

### 2. Frontend Setup
```bash
# Navigate to frontend directory and install dependencies
cd frontend
npm install
```

### 3. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the `backend/` directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
FLASK_ENV=development
```

**Note**: OpenAI API key is optional. The app will use fallback analysis if not provided.

## 🚀 Running the Application

### Method 1: Start Both Services Separately

#### Terminal 1 - Backend Server:
```bash
cd backend
python app.py
```
The backend will start on `http://localhost:5000`

#### Terminal 2 - Frontend Development Server:
```bash
# Navigate to frontend directory
cd frontend
npm start
```
The frontend will start on `http://localhost:3000`

### Method 2: Build and Serve (Production)

#### Build Frontend:
```bash
# Navigate to frontend directory and build
cd frontend
npm run build
```

#### Serve Built App:
```bash
# Start backend (serves both API and built frontend)
cd backend
python app.py
```

### 🚀 **Development Mode (Two terminals):**

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### 🏗️ **Production Build:**
```bash
# Build frontend
cd frontend
npm run build

# Serve built app
cd ../backend
python app.py
```

## 📖 Usage Guide

### 1. Upload Data
- Click "Upload Excel File" button
- Select your project data Excel file
- The app will process and display charts automatically

### 2. View Charts
- **Chart 1**: Monthly Revenue with cumulative tracking
- **Chart 2**: Quarterly Revenue breakdown
- **Chart 3**: Expected vs Actualized Revenue comparison
- **Chart 4**: Project Status Distribution

### 3. Generate Analysis
- Click "Update Data" button to open the chat interface
- The AI will analyze your data and provide business insights
- Chat responses support markdown formatting including images

### 4. Interactive Features
- Switch between different years using dropdown selectors
- Hover over charts for detailed information
- Use the chat interface for custom queries about your data

## 📁 Project Structure

```
ta-project-data-analyst/
├── frontend/
│   ├── public/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── ProjectCharts.jsx
│   │   │   │   ├── UpdateButton.jsx
│   │   │   │   └── ChatWindow.jsx
│   │   │   ├── contexts/
│   │   │   │   └── DataContext.js
│   │   │   ├── services/
│   │   │   │   └── chatApi.js
│   │   │   ├── styles/
│   │   │   └── App.js
│   │   ├── package.json
│   └── backend/
│       ├── routes/
│       │   ├── analysis.py
│       │   └── data.py
│       ├── utils/
│       │   └── parser.py
│       ├── app.py
│       ├── requirements.txt
│       └── .env (create this)
├── .gitignore
└── README.md
```

## 🔧 Configuration

### Chat Webhook Configuration
The chat interface is configured to use a webhook. To modify the endpoint:

1. Edit `frontend/src/services/chatApi.js`
2. Update the `WEBHOOK_URL` constant
3. Ensure your webhook expects the following JSON structure:
```json
{
  "request": "user message",
  "projectData": [...],
  "invoiceData": [...],
  "sessionId": "random_number"
}
```

### Excel Data Format
Your Excel file should contain:
- **Project Code**: Unique identifier for each project
- **Year**: Project year (2024, 2025, etc.)
- **Monthly Columns**: "2025 Jan", "2025 Feb", etc.
- **Project Status**: Current status of the project

## 🔍 Available Scripts

### Frontend Scripts (from frontend directory):
```bash
cd frontend
npm start          # Start development server
npm run build      # Build for production
npm test           # Run tests
npm run eject      # Eject from Create React App
```

### Backend Scripts (from backend directory):
```bash
python app.py      # Start Flask server
```

## 🐛 Troubleshooting

### Common Issues:

1. **Charts showing doubled values**
   - This was a known issue that has been fixed in the latest version
   - Ensure you're using the deduplicated calculation logic

2. **OpenAI Analysis not working**
   - Check that your `OPENAI_API_KEY` is set in `backend/.env`
   - The app will use fallback analysis if the API key is missing

3. **Excel upload fails**
   - Ensure your Excel file has the correct column structure
   - Check the browser console for specific error messages

4. **Chat interface not responding**
   - Verify the webhook URL in `chatApi.js`
   - Check that your webhook endpoint is accessible

5. **Port conflicts**
   - Frontend default: `http://localhost:3000`
   - Backend default: `http://localhost:5000`
   - Modify ports in the respective configuration files if needed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

[Add your license information here]

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the browser console for error messages
3. Check the backend terminal for API errors
4. [Add your contact information or issue tracker]

---

**Happy Analyzing!** 📊✨ 

### 🔧 **Initial Setup (One-time):**
```bash
# Install frontend dependencies
cd frontend
npm install

# Setup backend
cd ../backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
``` 