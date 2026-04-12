from flask import Flask, jsonify, request, send_from_directory
import time
import json
import os
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__, static_folder='')

CORS(app)

# Email configuration
GMAIL_ADDRESS = 'churchthewordofgoddeliverance@gmail.com'
GMAIL_PASSWORD = 'iqicottabtvmxlix'  # Removed spaces from the original password

LIVE_STATE_FILE = 'live_state.json'
SIGNALING_FILE = 'signaling_data.json'

def load_live_state():
    if os.path.exists(LIVE_STATE_FILE):
        with open(LIVE_STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'live': False,
        'started_at': None,
        'viewers': 0,
        'video_url': 'https://www.youtube.com/embed/YOUR_LIVE_VIDEO_ID?autoplay=1&mute=0'
    }

def save_live_state(state):
    with open(LIVE_STATE_FILE, 'w') as f:
        json.dump(state, f)

def load_signaling_data():
    if os.path.exists(SIGNALING_FILE):
        with open(SIGNALING_FILE, 'r') as f:
            return json.load(f)
    return {
        'offer': None,
        'answer': None,
        'candidates': [],
        'viewer_candidates': []
    }

def save_signaling_data(data):
    with open(SIGNALING_FILE, 'w') as f:
        json.dump(data, f)

live_state = load_live_state()

# WebRTC signaling
signaling_data = load_signaling_data()

@app.route('/')
def homepage():
    return send_from_directory('.', 'index.html')

@app.route('/live')
def watch_live():
    return send_from_directory('.', 'live.html')

@app.route('/media-panel/go-live')
def go_live_panel():
    return send_from_directory('media-panel', 'go-live.html')

@app.route('/media-panel/projector')
def projector_panel():
    return send_from_directory('media-panel', 'projector.html')

@app.route('/logo.jpg')
def serve_logo():
    return send_from_directory('.', 'logo.jpg')

@app.route('/logo.svg')
def serve_logo_svg():
    return send_from_directory('.', 'logo.svg')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('.', 'logo.jpg')

@app.route('/status')
def status():
    if live_state['live'] and live_state['started_at']:
        elapsed = int(time.time() - live_state['started_at'])
        viewers = max(1, int(elapsed / 5) + 1)
        live_state['viewers'] = viewers
        return jsonify(
            live=True,
            viewers=viewers,
            duration=elapsed,
            video_url=live_state['video_url']
        )

    return jsonify(live=False, viewers=0, duration=0, video_url='')

@app.route('/start-live', methods=['POST'])
def start_live():
    if not live_state['live']:
        live_state['live'] = True
        live_state['started_at'] = time.time()
        live_state['viewers'] = 1
        save_live_state(live_state)
    return jsonify(
        live=True,
        viewers=live_state['viewers'],
        video_url=live_state['video_url']
    )

@app.route('/stop-live', methods=['POST'])
def stop_live():
    live_state['live'] = False
    live_state['started_at'] = None
    live_state['viewers'] = 0
    save_live_state(live_state)
    signaling_data['offer'] = None
    signaling_data['answer'] = None
    signaling_data['candidates'] = []
    signaling_data['viewer_candidates'] = []
    save_signaling_data(signaling_data)
    return jsonify(live=False)

# WebRTC signaling endpoints
@app.route('/webrtc/offer', methods=['POST', 'OPTIONS'])
def webrtc_offer():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = request.get_json()
    signaling_data['offer'] = data
    save_signaling_data(signaling_data)
    return jsonify({'status': 'ok'})

@app.route('/webrtc/answer', methods=['POST', 'OPTIONS'])
def webrtc_answer():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = request.get_json()
    signaling_data['answer'] = data
    save_signaling_data(signaling_data)
    return jsonify({'status': 'ok'})

@app.route('/webrtc/candidate', methods=['POST', 'OPTIONS'])
def webrtc_candidate():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = request.get_json()
    signaling_data['candidates'].append(data)
    save_signaling_data(signaling_data)
    return jsonify({'status': 'ok'})

@app.route('/webrtc/viewer-candidate', methods=['POST', 'OPTIONS'])
def webrtc_viewer_candidate():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = request.get_json()
    signaling_data['viewer_candidates'].append(data)
    save_signaling_data(signaling_data)
    return jsonify({'status': 'ok'})

@app.route('/webrtc/viewer-candidates')
def get_viewer_candidates():
    return jsonify(signaling_data['viewer_candidates'])

@app.route('/webrtc/offer')
def get_offer():
    return jsonify(signaling_data['offer'] or {})

@app.route('/webrtc/answer')
def get_answer():
    return jsonify(signaling_data['answer'] or {})

@app.route('/webrtc/candidates')
def get_candidates():
    return jsonify(signaling_data['candidates'])

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Custom error handlers for API endpoints
@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({'success': False, 'error': 'Bad request'}), 400

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/send-contact', methods=['POST', 'OPTIONS'])
def send_contact():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        print("=== CONTACT FORM REQUEST RECEIVED ===")
        data = request.get_json()
        print(f"Request data: {data}")
        
        if not data:
            print("No data provided")
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        message = data.get('message', '').strip()
        to_email = data.get('to_email', '').strip()  # New field for custom recipient
        
        print(f"Parsed data - Name: {name}, Email: {email}, Phone: {phone}, Message length: {len(message)}")
        
        # Validate required fields
        if not name or not email or not phone or not message:
            print("Validation failed - missing required fields")
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        print("Validation passed, preparing to send email...")
        
        # Determine recipient based on form type
        if to_email:
            # Media panel form
            recipient = to_email
            subject = f'Message from {name} via Media Panel'
        else:
            # Main contact form - send to church email
            recipient = GMAIL_ADDRESS
            subject = f'New Contact Message from {name}'
        
        print(f"Sending email to: {recipient}")
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['From'] = 'The Word of God Deliverance Vineyard Church <' + GMAIL_ADDRESS + '>'
        msg['To'] = recipient
        msg['Subject'] = subject
        if not to_email:
            msg['Reply-To'] = email
        
        # Use simple text email for now to avoid HTML issues
        plain_body = f"""
The Word of God Deliverance Vineyard Church

New Contact Message:

Name: {name}
Email: {email}
Phone: {phone}

Message:
{message}

---
This message was sent from the church website contact form.
"""

        msg.attach(MIMEText(plain_body, 'plain'))
        
        # Send email
        try:
            print("Connecting to Gmail SMTP...")
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
                server.send_message(msg)
            print(f'✓ Email sent successfully to {recipient}')
            return jsonify({'success': True, 'message': 'Your message has been sent successfully!'})
            
        except smtplib.SMTPAuthenticationError as auth_err:
            error_msg = 'Gmail authentication failed. Check credentials and ensure 2FA is disabled or an App Password is used.'
            print(f'✗ {error_msg}: {str(auth_err)}')
            return jsonify({'success': False, 'error': error_msg}), 500
            
        except smtplib.SMTPException as smtp_err:
            error_msg = f'Email service error: {str(smtp_err)}'
            print(f'✗ {error_msg}')
            return jsonify({'success': False, 'error': error_msg}), 500
    
    except Exception as e:
        import traceback
        error_msg = f'Error processing request: {str(e)}'
        print(f'✗ {error_msg}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': error_msg}), 500

if __name__ == '__main__':
    # For local development
    app.run(host='0.0.0.0', port=5000, debug=True)

# For production deployment with gunicorn
# This ensures proper error handling in production
if __name__ != '__main__':
    # Production mode - disable debug
    app.debug = False
