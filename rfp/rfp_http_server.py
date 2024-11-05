"""
This is an alternative for the app in case we want to have a server, instead of a streamlit app
"""
from flask import Flask, request, jsonify
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
import os
from datetime import datetime
import traceback
from rfp_filler import RFPFiller
rfp_fil = RFPFiller()
app = Flask(__name__)

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Flask server startup')


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('RFP_SERVER_API_KEY')
        if api_key and api_key == os.environ.get('RFP_SERVER_API_KEY'):
            return f(*args, **kwargs)
        return jsonify({'error': 'Invalid or missing API key'}), 401

    return decorated_function


@app.errorhandler(Exception)
def handle_error(error):
    app.logger.error(f'An error occurred: {error}\n{traceback.format_exc()}')
    return jsonify({
        'error': 'An internal error occurred',
        'timestamp': datetime.utcnow().isoformat()
    }), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/get_answer', methods=['POST'])
# @require_api_key
def get_answer():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        if 'query' not in data:
            return jsonify({'error': 'Missing text field'}), 400

        question = data['query']
        merchant_name = data.get('merchant_name', None)
        logging.info(f"Received question!\nmerchant name: {merchant_name}.\nQuestion: {question}")
        answer, prompt = rfp_fil.answer_question(question, merchant_name, return_prompt=True)
        app.logger.info(f"Answer: {answer}")
        app.logger.info(f"Prompt: {prompt}")
        # Example operation: reverse a string

        return jsonify({
            'answer': answer,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        app.logger.error(f'Error processing request: {str(e)}\n{traceback.format_exc()}')
        return jsonify({
            'error': 'Error processing request',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/api/save_answer', methods=['POST'])
@require_api_key
def save_answer():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        if 'query' not in data:
            return jsonify({'error': 'Missing query field'}), 400
        if 'answer' not in data:
            return jsonify({'error': 'Missing answer field'}), 400
        question = data['question']
        answer = data['answer']
        response = rfp_fil.rfp_pinecone_embedder.upsert_question(question, answer)

        app.logger.info(f'Successfully processed request for input: {response}')

        return jsonify({
            'pc_response': response,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        app.logger.error(f'Error processing request: {str(e)}\n{traceback.format_exc()}')
        return jsonify({
            'error': 'Error processing request',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))

    # In production, you should use a proper WSGI server like gunicorn
    # This is just for development
    app.run(host='0.0.0.0', port=port)
