# YouTube Video to PDF Converter

## Description
This is an application to convert YouTube videos—primarily slideshow-based educational videos with tutors—into PDFs. The application extracts unique frames from the video and compiles them into a PDF, making it easier for students to take notes and study efficiently.

## Features
- Download YouTube videos in MP4 format.
- Extract frames at regular intervals from the downloaded video.
- Identify and filter out duplicate or highly similar frames.
- Detect black-and-white slides to differentiate annotated sequences.
- Generate a structured PDF containing unique and relevant slides.
- Provide a download link for the generated PDF.

## Prerequisites
Ensure you have the following installed:
- Python 3.10
- FFMPEG (Ensure the path is correctly set in the script)
- Required Python packages:
  ```sh
  pip install flask yt-dlp moviepy opencv-python-headless numpy reportlab scikit-image
  ```

## Installation & Usage
1. Clone this repository:
   ```sh
   git clone https://github.com/your-repo/youtube-to-pdf.git
   cd youtube-to-pdf
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the application:
   ```sh
   python app.py
   ```
4. Open a web browser and visit `http://127.0.0.1:5000/`
5. Enter the YouTube video URL and generate the PDF.
6. Download the generated PDF for studying and note-taking.

## File Structure
- `app.py` - The main Flask application.
- `templates/index.html` - Frontend HTML form for user input.
- `downloads/` - Directory where downloaded videos, extracted frames, and PDFs are stored.

## API Endpoints
- `/` (GET, POST) - Home page for URL input and PDF generation.
- `/download/<filename>` (GET) - Endpoint to download the generated PDF.

## Notes
- The application uses Structural Similarity Index (SSIM) to compare images and remove redundant frames.
- It processes black-and-white slides separately to maintain key information.

## License
This project is open-source under the MIT License.

## Acknowledgments
Special thanks to open-source libraries like Flask, yt-dlp, MoviePy, OpenCV, and ReportLab for making this application possible.

