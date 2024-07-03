from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import cv2
from langchain_community.llms import HuggingFaceHub
from PIL import Image
import pytesseract
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.chains.question_answering import load_qa_chain

os.environ["HUGGINGFACEHUB_API_TOKEN"] ='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'

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Define a dictionary to store usernames and passwords
user_database = {
    "user1": "1",
    "user2": "2",
    "caretaker1": "1",
    "caretaker2": "2"
}

def ocr_with_pytesseract(path):
    img_cv = cv2.imread(path)
    text = pytesseract.image_to_string(img_cv)
    return text

def get_chat_response(document_search, chain):
    query = "Display items purchased and total amount from the text in point wise manner within 467 characters."
    docs = document_search.similarity_search(query)
    a = chain.run(input_documents=docs, question=query)
    output = ''.join(a)
    output = output[output.index('Answer:'):]
    return output

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username in user_database and user_database[username] == password:
        if username.startswith('caretaker'):
            return redirect(url_for('caretaker_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    else:
        return "Invalid username or password"

@app.route('/user_dashboard')
def user_dashboard():
    return render_template('user_dashboard.html')

@app.route('/caretaker_dashboard')
def caretaker_dashboard():
    return render_template('caretaker_dashboard.html')

@app.route('/progressive_report')
def progressive_report():
    return render_template('progressive_report.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Perform OCR using pytesseract
        extracted_text = ocr_with_pytesseract(file_path)

        # Split the text using Character Text Split
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=2000,
            chunk_overlap=1000,
            length_function=len,
        )
        texts = text_splitter.split_text(extracted_text)

        # Create embeddings and perform search
        embeddings = HuggingFaceEmbeddings()
        document_search = FAISS.from_texts(texts, embeddings)

        # Load Question Answering chain
        chain = load_qa_chain(HuggingFaceHub(repo_id='mistralai/Mixtral-8x7B-Instruct-v0.1'), chain_type="stuff")

        # Get response using Question Answering chain
        response = get_chat_response(document_search, chain)

        # Send the extracted text and model response back to the client
        return jsonify({'model_response': response})

if __name__ == '__main__':
    app.run(debug=True)
