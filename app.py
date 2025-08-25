from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from PyPDF2 import PdfReader, PdfWriter
from werkzeug.utils import secure_filename
import os
import tempfile
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size (increased)

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
        try:
            if 'pdf_files' not in request.files:
                flash('No files were selected. Please choose PDF files to merge.', 'error')
                return redirect(request.url)
            
            files = request.files.getlist('pdf_files')
            files = [f for f in files if f.filename != '']
            if not files:
                flash('No files were selected. Please choose PDF files to merge.', 'error')
                return redirect(request.url)
            
            valid_files = []
            temp_paths = []
            page_selections = {}

            # Save files and get page selections
            for file in files:
                if file and allowed_file(file.filename):
                    unique_filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
                    temp_path = os.path.join(tempfile.gettempdir(), unique_filename)
                    file.save(temp_path)
                    temp_paths.append(temp_path)
                    valid_files.append((file.filename, temp_path))
                    # Get page selection from form
                    page_input = request.form.get(f'pages_{file.filename}', '')
                    page_selections[file.filename] = page_input

            if len(valid_files) < 2:
                flash('Please select at least 2 PDF files to merge.', 'warning')
                for path in temp_paths:
                    try: os.remove(path)
                    except: pass
                return redirect(request.url)

            merger = PdfWriter()
            for orig_filename, pdf_path in valid_files:
                try:
                    reader = PdfReader(pdf_path)
                    pages_str = page_selections.get(orig_filename, '')
                    pages_to_add = []
                    # Parse page ranges
                    for part in pages_str.split(','):
                        part = part.strip()
                        if '-' in part:
                            start, end = map(int, part.split('-'))
                            pages_to_add.extend(range(start-1, end))  # 0-indexed
                        elif part.isdigit():
                            pages_to_add.append(int(part)-1)
                    # Add selected pages
                    for page_num in pages_to_add:
                        if 0 <= page_num < len(reader.pages):
                            merger.add_page(reader.pages[page_num])
                except Exception as e:
                    flash(f'Error processing {orig_filename}: {str(e)}', 'warning')
                    continue

            output_filename = f"merged_{uuid.uuid4()}.pdf"
            output_path = os.path.join(tempfile.gettempdir(), output_filename)
            with open(output_path, 'wb') as output_file:
                merger.write(output_file)
            for _, path in valid_files:
                try: os.remove(path)
                except: pass
            merger.close()
            return send_file(output_path, as_attachment=True, download_name='merged_document.pdf', mimetype='application/pdf')

        except Exception as e:
            flash(f'An unexpected error occurred: {str(e)}', 'error')
            return redirect(request.url)

    return render_template('merge.html')

@app.route('/about')
def about():
    return render_template('about.html')

# Error handler for file size limit
@app.errorhandler(413)
def too_large(e):
    flash('File is too large. Maximum file size is 50MB.', 'error')
    return redirect(request.url), 413

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
