from flask import Flask, request, jsonify, render_template
from ingest import ingest_data
from store import build_store
from retrieve import retrieve
from generate import generate_answer
import os
import shutil
from werkzeug.utils import secure_filename

print("=== DEBUG INFO ===")
print(f"Working directory: {os.getcwd()}")
print(f"Templates exists: {os.path.exists('templates')}")
print(f"index.html exists: {os.path.exists('templates/index.html')}")
print("==================")

app = Flask(__name__, template_folder='templates')

# Upload configuration
UPLOAD_FOLDER = 'data'
ALLOWED_EXTENSIONS = {
    'pdf': ['.pdf'],
    'image': ['.png', '.jpg', '.jpeg', '.gif', '.bmp'],
    'audio': ['.mp3', '.wav', '.m4a', '.ogg']
}

def allowed_file(filename, file_type):
    """Check if file extension is allowed"""
    if file_type not in ALLOWED_EXTENSIONS:
        return False
    
    filename = filename.lower()
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS[file_type])

# Global state
index = None
texts = None
full_data = None
system_ready = False

@app.route("/")
def home():
    print("Rendering index.html...")
    return render_template("index.html")

@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "ready": system_ready,
        "documents_loaded": len(full_data) if full_data else 0
    })

@app.route("/api/build", methods=["POST"])
def build():
    global index, texts, full_data, system_ready
    try:
        data = ingest_data()
        if not data:
            system_ready = False
            return jsonify({
                "error": True,
                "message": "❌ No valid documents found. Please upload files first."
            })
        index, texts, full_data = build_store(data)
        system_ready = True
        return jsonify({
            "error": False,
            "message": "✅ Knowledge base built successfully.",
            "documents": len(full_data)
        })
    except Exception as e:
        system_ready = False
        return jsonify({
            "error": True,
            "message": f"System error: {str(e)}"
        })

@app.route("/api/query", methods=["POST"])
def query():
    global index, texts, full_data, system_ready
    if not system_ready:
        return jsonify({
            "error": True,
            "message": "⚠️ System not ready. Please build knowledge base first."
        })
    payload = request.json
    user_query = payload.get("query", "").strip()
    if not user_query:
        return jsonify({
            "error": True,
            "message": "Please enter a question."
        })
    retrieved = retrieve(user_query, index, texts, full_data)
    if not retrieved:
        return jsonify({
            "error": False,
            "answer": "❌ Cannot answer. No evidence found in documents.",
            "sources": 0
        })
    answer = generate_answer(user_query, retrieved)
    return jsonify({
        "error": False,
        "answer": answer,
        "sources": len(retrieved)
    })

# ===========================================
# 🆕 FILE UPLOAD ENDPOINTS
# ===========================================

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle file uploads from web interface"""
    try:
        if 'file_count' not in request.form:
            return jsonify({'error': True, 'message': 'No files specified'})
        
        file_count = int(request.form['file_count'])
        uploaded_files = []
        
        for i in range(file_count):
            file_key = f'file{i}'
            type_key = f'type{i}'
            
            if file_key not in request.files or type_key not in request.form:
                continue
                
            file = request.files[file_key]
            file_type = request.form[type_key]
            
            if file.filename == '':
                continue
                
            if not allowed_file(file.filename, file_type):
                return jsonify({
                    'error': True, 
                    'message': f'File {file.filename} has invalid extension for type {file_type}'
                })
            
            # Secure filename and save to appropriate folder
            filename = secure_filename(file.filename)
            
            if file_type == 'pdf':
                save_path = os.path.join(UPLOAD_FOLDER, 'docs', filename)
            elif file_type == 'image':
                save_path = os.path.join(UPLOAD_FOLDER, 'images', filename)
            elif file_type == 'audio':
                save_path = os.path.join(UPLOAD_FOLDER, 'audio', filename)
            else:
                continue
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Save file
            file.save(save_path)
            uploaded_files.append(filename)
            print(f"✅ Uploaded: {filename} ({file_type})")
        
        if not uploaded_files:
            return jsonify({'error': True, 'message': 'No valid files uploaded'})
        
        # Reset system state since new files were added
        global index, texts, full_data, system_ready
        index = None
        texts = None
        full_data = None
        system_ready = False
        
        return jsonify({
            'error': False,
            'message': f'✅ Successfully uploaded {len(uploaded_files)} file(s)',
            'files': uploaded_files,
            'note': 'Please rebuild knowledge base to include new files'
        })
        
    except Exception as e:
        return jsonify({'error': True, 'message': f'Upload error: {str(e)}'})

@app.route('/api/file-counts', methods=['GET'])
def get_file_counts():
    """Get counts of files in data folders"""
    counts = {
        'pdfs': 0,
        'images': 0,
        'audios': 0,
        'total': 0
    }
    
    try:
        # Count PDFs
        pdf_folder = os.path.join(UPLOAD_FOLDER, 'docs')
        if os.path.exists(pdf_folder):
            counts['pdfs'] = len([f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')])
        
        # Count Images
        image_folder = os.path.join(UPLOAD_FOLDER, 'images')
        if os.path.exists(image_folder):
            image_extensions = ALLOWED_EXTENSIONS['image']
            counts['images'] = len([f for f in os.listdir(image_folder) 
                                  if any(f.lower().endswith(ext) for ext in image_extensions)])
        
        # Count Audio files
        audio_folder = os.path.join(UPLOAD_FOLDER, 'audio')
        if os.path.exists(audio_folder):
            audio_extensions = ALLOWED_EXTENSIONS['audio']
            counts['audios'] = len([f for f in os.listdir(audio_folder) 
                                  if any(f.lower().endswith(ext) for ext in audio_extensions)])
        
        # Calculate total
        counts['total'] = counts['pdfs'] + counts['images'] + counts['audios']
    
    except Exception as e:
        print(f"Error counting files: {e}")
    
    return jsonify(counts)

@app.route('/api/clear-files', methods=['POST'])
def clear_files():
    """Clear all uploaded files"""
    try:
        folders = ['docs', 'images', 'audio']
        cleared_count = 0
        
        for folder in folders:
            folder_path = os.path.join(UPLOAD_FOLDER, folder)
            if os.path.exists(folder_path):
                # Count files before clearing
                file_count = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
                cleared_count += file_count
                
                # Remove all files but keep the folder
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
        
        # Reset system state
        global index, texts, full_data, system_ready
        index = None
        texts = None
        full_data = None
        system_ready = False
        
        return jsonify({
            'error': False,
            'message': f'✅ Cleared {cleared_count} file(s). System reset.',
            'cleared': cleared_count
        })
        
    except Exception as e:
        return jsonify({'error': True, 'message': f'Clear error: {str(e)}'})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'RAG Document Assistant',
        'system_ready': system_ready,
        'upload_folder': os.path.abspath(UPLOAD_FOLDER)
    })

# ===========================================
# MAIN ENTRY POINT
# ===========================================

if __name__ == "__main__":
    # Create necessary folders if they don't exist
    folders = ['docs', 'images', 'audio']
    for folder in folders:
        os.makedirs(os.path.join(UPLOAD_FOLDER, folder), exist_ok=True)
    
    print("\n" + "="*50)
    print("🚀 AI Document Assistant - RAG System")
    print("="*50)
    print(f"📁 Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"📄 Templates: {os.path.exists('templates')}")
    print(f"🌐 Server URL: http://localhost:5050")
    print("="*50)
    print("\n📢 Available features:")
    print("  • 📤 File upload (PDF, Images, Audio)")
    print("  • 🔨 Knowledge base building")
    print("  • 🔍 Semantic search with evidence")
    print("  • 📝 AI-powered Q&A with citations")
    print("\nPress CTRL+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5050, use_reloader=False)