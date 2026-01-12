from pypdf import PdfReader
from PIL import Image
import pytesseract
import os
import whisper
import traceback

# Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load Whisper model for audio (only if needed)
audio_model = None

def get_audio_model():
    """Lazy load audio model to save memory"""
    global audio_model
    if audio_model is None:
        print("Loading Whisper model for audio...")
        audio_model = whisper.load_model("base")
    return audio_model

def read_audio(path):
    """Read audio file and transcribe"""
    try:
        model = get_audio_model()
        result = model.transcribe(path)
        return result['text'], result.get('segments', [])
    except Exception as e:
        print(f"❌ Error reading audio {path}: {e}")
        return "", []

def read_pdf(path):
    """Read PDF file"""
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"❌ Error reading PDF {path}: {e}")
        return ""

def read_image(path):
    """Read image file with OCR"""
    try:
        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        print(f"❌ Error reading image {path}: {e}")
        return ""

def ingest_data():
    """Ingest all documents from data folder"""
    data = []
    
    # Ensure directories exist
    for folder in ['docs', 'images', 'audio']:
        os.makedirs(f"data/{folder}", exist_ok=True)
    
    # Process PDFs
    pdf_folder = "data/docs"
    if os.path.exists(pdf_folder):
        for file in os.listdir(pdf_folder):
            if file.lower().endswith('.pdf'):
                filepath = os.path.join(pdf_folder, file)
                print(f"📄 Processing PDF: {file}")
                text = read_pdf(filepath)
                if text:
                    data.append({
                        "content": text,
                        "source": file,
                        "type": "pdf"
                    })
    
    # Process Images
    image_folder = "data/images"
    if os.path.exists(image_folder):
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        for file in os.listdir(image_folder):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                filepath = os.path.join(image_folder, file)
                print(f"🖼️ Processing image: {file}")
                text = read_image(filepath)
                if text:
                    data.append({
                        "content": text,
                        "source": file,
                        "type": "image"
                    })
    
    # Process Audio (optional)
    audio_folder = "data/audio"
    if os.path.exists(audio_folder):
        audio_extensions = ['.mp3', '.wav', '.m4a', '.ogg']
        for file in os.listdir(audio_folder):
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                filepath = os.path.join(audio_folder, file)
                print(f"🎵 Processing audio: {file}")
                text, segments = read_audio(filepath)
                if text:
                    data.append({
                        "content": text,
                        "source": file,
                        "type": "audio",
                        "segments": segments
                    })
    
    print(f"✅ Ingested {len(data)} documents total")
    return data