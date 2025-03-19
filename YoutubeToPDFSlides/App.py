from flask import Flask, request, render_template, send_file
import os
import re
import time
import logging
from yt_dlp import YoutubeDL
from moviepy.video.io.VideoFileClip import VideoFileClip
import cv2
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from skimage.metrics import structural_similarity as ssim
import numpy as np

# Fetch FFMPEG path from environment variables
FFMPEG_PATH = "./ffmpeg-7.1.1-full_build/bin/ffmpeg.exe"

# Initialize Flask app
app = Flask(__name__)

# Define the directory to save downloaded files
DOWNLOAD_DIR = os.path.abspath("./downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def sanitize_filename(filename):
    """
    Sanitizes the filename by removing invalid characters.
    """
    return re.sub(r'[<>:"/\\|?*\n\r]', '_', filename)

def download_video(video_url, download_dir):
    """
    Downloads a video from the given URL as MP4 and renames it without quality info.
    """
    try:
        logging.debug(f"Downloading video from {video_url} to {download_dir}")

        # Configure yt-dlp options
        ydl_opts = {
            'ffmpeg_location': FFMPEG_PATH,
            'format': 'bestvideo[height<=1080]+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'quiet': True,
        }

        # Download the video
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            original_path = ydl.prepare_filename(info_dict).replace('.webm', '.mp4')

            # Sanitize the title to remove invalid characters
            sanitized_title = sanitize_filename(info_dict['title'])

            # Define the new filename without quality appended
            new_filename = f"{sanitized_title}.mp4"
            new_path = os.path.join(download_dir, new_filename)

            # Rename the downloaded file only if it doesn't already exist
            if not os.path.exists(new_path):
                os.rename(original_path, new_path)
            else:
                logging.debug(f"File already exists: {new_path}")
                new_path = original_path  # Use the original path if the file already exists

        # Set modification date to current time
        current_time = time.time()
        os.utime(new_path, (current_time, current_time))

        return new_path
    except Exception as e:
        logging.error(f"Failed to download {video_url}: {e}")
        raise Exception(f"Failed to download {video_url}: {e}")

def extract_frames(video_path, output_folder, interval=1):
    """
    Extracts frames from the video at the specified interval (in seconds).
    """
    os.makedirs(output_folder, exist_ok=True)
    clip = VideoFileClip(video_path)
    duration = clip.duration
    frame_count = 0

    for t in range(0, int(duration), interval):
        frame_filename = os.path.join(output_folder, f"frame_{frame_count:04d}.png")
        clip.save_frame(frame_filename, t)
        frame_count += 1

    clip.close()

def is_black_and_white(image_path, threshold=0.95):
    """
    Checks if an image is black and white.
    """
    img = cv2.imread(image_path)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Calculate the standard deviation of pixel values
    std_dev = np.std(img_gray)
    # If the standard deviation is low, the image is likely black and white
    return std_dev < 25  # Adjust this threshold as needed

def compare_images(image1, image2, threshold=0.9875):
    """
    Compares two images using SSIM and returns True if they are similar.
    """
    img1 = cv2.imread(image1)
    img2 = cv2.imread(image2)
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    similarity = ssim(img1_gray, img2_gray)
    return similarity >= threshold

def create_pdf(image_folder, output_pdf, threshold=0.9875):
    """
    Creates a PDF of unique images from the folder.
    """
    images = sorted([os.path.join(image_folder, img) for img in os.listdir(image_folder) if img.endswith(".png")])
    unique_images = []

    for i, image in enumerate(images):
        if i == 0:
            unique_images.append(image)
        else:
            if not compare_images(unique_images[-1], image, threshold):
                unique_images.append(image)

    # Filter to include only the first and last slide of annotated sequences
    filtered_images = []
    i = 0
    while i < len(unique_images):
        if is_black_and_white(unique_images[i]):
            # Add the first slide (question)
            filtered_images.append(unique_images[i])
            # Skip intermediate annotated slides
            j = i + 1
            while j < len(unique_images) and compare_images(unique_images[i], unique_images[j], threshold):
                j += 1
            # Add the last slide (solution)
            if j - 1 > i:
                filtered_images.append(unique_images[j - 1])
            i = j
        else:
            filtered_images.append(unique_images[i])
            i += 1

    # Create a horizontal PDF
    c = canvas.Canvas(output_pdf, pagesize=landscape(A4))
    width, height = landscape(A4)

    for img in filtered_images:
        c.drawImage(img, 0, 0, width=width, height=height, preserveAspectRatio=True, anchor='c')
        c.showPage()

    c.save()

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    download_link = None

    if request.method == 'POST':
        url = request.form.get('url')
        threshold = 0.9875  # Fixed threshold

        if not url:
            error = "Please provide a YouTube URL."
        else:
            try:
                # Download the video
                video_path = download_video(url, DOWNLOAD_DIR)
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                frames_folder = os.path.join(DOWNLOAD_DIR, video_name + "_frames")
                pdf_path = os.path.join(DOWNLOAD_DIR, video_name + "_unique_frames.pdf")

                # Extract frames
                extract_frames(video_path, frames_folder)

                # Create PDF of unique frames
                create_pdf(frames_folder, pdf_path, threshold)

                download_link = os.path.basename(pdf_path)

            except Exception as e:
                error = str(e)

    return render_template('index.html', error=error, download_link=download_link)

@app.route('/download/<filename>')
def download_file(filename):
    # Serve the downloaded file to the user.
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    try:
        return send_file(file_path, as_attachment=True)
    except FileNotFoundError:
        return "File not found", 404

if __name__ == "__main__":
    app.run(debug=True)