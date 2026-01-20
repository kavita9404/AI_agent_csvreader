# AI-Powered CSV Data Insight Engine


##  Project Overview

Welcome to the AI-Powered CSV Data Insight Engine! This project provides a robust solution for extracting meaningful insights from CSV files using the power of Generative AI. Upload your CSV, ask natural language questions about its content, and let the intelligent backend provide structured answers, leveraging Pandas for data manipulation and Google's Gemini LLM for advanced analysis.

This application is split into two main components: a resilient FastAPI backend and a responsive Next.js frontend, designed to deliver a seamless user experience.

##  Features

* **Intuitive CSV Upload:** Easily upload your `.csv` files through a clean web interface.
* **Natural Language Querying:** Ask complex questions about your CSV data in plain English.
* **AI-Powered Analysis:** Utilizes Google's Gemini LLM (via LangChain integration) to interpret queries and extract insights.
* **Robust Data Processing:** Leverages the power of Pandas for efficient and accurate data manipulation on the backend.
* **Dynamic Output:** Receives and displays processed data or analytical results in a clear format.
* **Responsive UI:** Built with `react-resizable-panels` for a customizable layout and `react-toastify` for engaging user feedback.
* **Secure Environment:** Uses `.env` files for managing sensitive API keys and configurations.

##  Tech Stack

### Backend (Python)

* **Framework:** FastAPI
* **Data Analysis:** Pandas, NumPy
* **AI/LLM Integration:** `google-generativeai` SDK, LangChain, `langchain-google-genai`
* **Web Server:** Uvicorn
* **Environment Management:** `python-dotenv`
* **File Handling:** `python-multipart`


### Frontend (React / Next.js)

* **Framework:** Next.js (React)
* **Styling:** Tailwind CSS
* **HTTP Client:** Axios
* **UI Components:** `react-resizable-panels`
* **Notifications:** `react-toastify`

##  Prerequisites

Before you begin, ensure you have the following installed on your system:

* **Git:** For cloning the repository.
* **Python 3.9+:** Recommended for the backend.
* **pip:** Python package installer (usually comes with Python).
* **Node.js 18+ & npm/yarn:** For the frontend.

##  Getting Started

Follow these steps to get your development environment set up.

### 1. Clone the Repository

```bash
git clone https://github.com/kavita9404/AI_agent_csvreader
cd AI_agent_csvreader
```

### 2.Navigate to backend

```bash
cd backend
```
### (optional) You can create a virtual environment for installing the dependencies. [Refer this](https://docs.python.org/3/library/venv.html)

### 3. Install Dependencies (use pip3 for MACos)

```
pip install -r requirements.txt
```

### 4. Set environment variables 
* Create a .env file and add the following variables
```
GOOGLE_API_KEY="YOUR_GOOGLE_GENERATIVE_AI_API_KEY"
FRONTEND_URL="Your frontend url"
```

### 5. Ensure that uvicorn is set up in your system's path
### Run backend

```
uvicorn main:app --reload --port 8000
```

## 6. Frontend Setup

### 7. Navigate to frontend 
```
cd "path to the frontend folder"
```

### 8. Install dependencies
```
npm install 
```

### 9. Configure Environment variables 

```
NEXT_PUBLIC_BACKEND_URL="your backend url"
```

### 10. Run the frontend

```
npm run dev
```
###
###
###

## Have a Look at the Application 
### Upload a CSV file into the application
<img width="1470" alt="Screenshot 2025-05-23 at 9 57 30 PM" src="https://github.com/user-attachments/assets/d3e811be-470e-4867-a6c5-2014a7250faf" />

### Ask a relevant Query and submit it .
<img width="1468" alt="Screenshot 2025-05-23 at 9 58 34 PM" src="https://github.com/user-attachments/assets/ff3efbae-e498-46e2-941a-45fbb07a11f1" />

### Get your output 
<img width="1469" alt="Screenshot 2025-05-23 at 9 59 21 PM" src="https://github.com/user-attachments/assets/d7fd8132-55c0-4d5b-8e5d-b10159ab77e7" />
