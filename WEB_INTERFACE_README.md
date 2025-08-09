# Grounded CV Generator - Web Interface

A beautiful, Apple-style web interface for the Grounded CV Generator MVP.

## Features

- **Clean, Minimal Design**: Apple-inspired interface with plenty of white space
- **File Upload**: Support for PDF and DOCX CV files
- **Job Description Input**: Large text area for job descriptions
- **Real-time Processing**: Progress indicators for each step
- **Results Display**: Match scores, metrics, and downloadable outputs
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

### Option 1: Using the PowerShell Script
```powershell
# Make sure your virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Run the web interface
.\run_web_app.ps1
```

### Option 2: Direct Streamlit Command
```powershell
# Make sure your virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Run the web interface
streamlit run web_app.py
```

### Option 3: Custom Port
```powershell
# Run on a different port (e.g., 8502)
.\run_web_app.ps1 -Port 8502
```

## Accessing the Web Interface

Once running, open your browser and go to:
- **Default**: http://localhost:8501
- **Custom port**: http://localhost:[PORT]

## How to Use

1. **Upload CV**: Click the upload area and select your CV file (PDF or DOCX)
2. **Enter Job Description**: Paste the job description in the text area
3. **Generate CV**: Click the "Generate Grounded CV" button
4. **View Results**: See the match score, metrics, and download options
5. **Download Results**: Download the generated CV, evidence report, and job analysis

## Design Features

- **Gradient Background**: Subtle gradient from light blue to purple
- **Glass Morphism**: Semi-transparent cards with blur effects
- **Smooth Animations**: Hover effects and transitions
- **Typography**: Clean, readable fonts with proper hierarchy
- **Color Scheme**: Purple/blue gradient with white cards
- **Spacing**: Generous white space for a clean look

## Technical Details

- **Framework**: Streamlit
- **Styling**: Custom CSS with Apple-inspired design
- **File Handling**: Temporary file storage for uploads
- **Error Handling**: Graceful error messages and validation
- **Progress Tracking**: Real-time progress indicators

## Troubleshooting

### Port Already in Use
If port 8501 is already in use, try:
```powershell
.\run_web_app.ps1 -Port 8502
```

### Virtual Environment Issues
If you get import errors, make sure the virtual environment is activated:
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Streamlit Not Found
If Streamlit isn't installed:
```powershell
pip install streamlit
```

## File Structure

```
Apps/1.Aligna/
├── web_app.py              # Main web interface
├── run_web_app.ps1         # PowerShell launcher
├── WEB_INTERFACE_README.md # This file
├── main.py                 # Core application logic
├── requirements.txt        # Dependencies
└── .env                   # Environment variables
```

## Customization

### Changing Colors
Edit the CSS variables in `web_app.py`:
```css
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    /* Change these colors */
}
```

### Adding Features
The web interface is modular and easy to extend. Add new sections by following the existing pattern in the `main()` function.

## Security Notes

- The web interface runs locally by default
- File uploads are stored temporarily and cleaned up automatically
- No data is stored permanently on the server
- API keys should be kept secure in the `.env` file
