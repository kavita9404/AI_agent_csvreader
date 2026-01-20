
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os 
from manipulator import process_csv_file
import shutil
from pathlib import Path
import dotenv
dotenv.load_dotenv()
app = FastAPI(
    title="CSV Uploader API",
    description="API for uploading and processing CSV files from Next.js frontend.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL")],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="Root endpoint", response_description="Basic API status message")
async def read_root():
    return {"message": "CSV Upload Python Backend is running!"}


@app.post("/uploadcsv")
async def upload_csv_file(
    csv_file: UploadFile = File(...),
    query: str = Form(...), 
):
    if not csv_file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only CSV files are allowed.",
        )
    saved_filename = f"{Path(csv_file.filename).stem}.csv"
    file_location = os.path.join(saved_filename)  
    print(f"Attempting to save file to: {file_location}")
    try:
        with open(file_location, "wb") as buffer:
            await csv_file.seek(
                0
            ) 
            shutil.copyfileobj(
                csv_file.file, buffer
            ) 
        print(
            f"File '{csv_file.filename}' saved successfully as '{saved_filename}' at '{file_location}'"
        )
        print("request received")
        processed_data = process_csv_file(file_location, query)
        print("processed data")
        print(processed_data)
        return JSONResponse(
            {
                "message": f"File '{csv_file.filename}' uploaded successfully!",
                "filename": csv_file.filename,
                "content_type": csv_file.content_type,
                **processed_data,
            }
        )

    except ValueError as ve:
        
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=f"CSV data processing error: {str(ve)}",
        )
    except Exception as e:
        print(f"An unexpected error occurred in the upload endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred during file upload or processing: {str(e)}",
        )
    finally:
        if os.path.exists(file_location):
            try:
                os.remove(file_location)
                print(f"Successfully deleted temporary file: {file_location}")
            except OSError as e:
                print(f"Error deleting file {file_location}: {e}")
