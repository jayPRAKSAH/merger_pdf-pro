from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge', methods=['GET', 'POST'])
def merge_pdfs():
    if request.method == 'POST':
        # Check if files were uploaded
        if 'pdf_files' not in request.files:
            flash('No files selected', 'error')
            return redirect(request.url)
        
        files = request.files.getlist('pdf_files')
        
        if not files or all(file.filename == '' for file in files):
            flash('No files selected', 'error')
            return redirect(request.url)
        
        # Validate files
        valid_files = []
        for file in files:
            if file and allowed_file(file.filename):
                valid_files.append(file)
            elif file.filename != '':
                flash(f'Invalid file type: {file.filename}. Only PDF files are allowed.', 'error')
                return redirect(request.url)
        
        if len(valid_files) < 2:
            flash('Please select at least 2 PDF files to merge', 'error')
            return redirect(request.url)
        
        # TODO: Implement PDF merging functionality here
        flash(f'Successfully prepared {len(valid_files)} files for merging!', 'success')
        return redirect(url_for('merge_pdfs'))
    
    return render_template('merge.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)