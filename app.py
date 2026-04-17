from flask import Flask, jsonify, request, send_from_directory
import time
import json
import os
from flask_cors import CORS
import requests
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__, static_folder='')

CORS(app)

# Email configuration
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@thewordofgodchurch.com')
TO_EMAIL = os.getenv('TO_EMAIL', 'churchthewordofgoddeliverance@gmail.com')
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS', '')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD', '')

LIVE_STATE_FILE = 'live_state.json'
SIGNALING_FILE = 'signaling_data.json'
CONTACT_MESSAGES_FILE = 'contact_messages.json'
SAVE_CONTACTS_ON_FAILURE = os.getenv('SAVE_CONTACTS_ON_FAILURE', 'true').lower() in ('1', 'true', 'yes')

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


def send_email_via_gmail(to_email, subject, plain_body, html_body, from_name='The Word of God Church'):
    """Send email using Gmail SMTP as fallback"""
    try:
        if not GMAIL_ADDRESS or not GMAIL_PASSWORD:
            print("Gmail credentials not configured", file=sys.stderr)
            return False
        
        print(f"Attempting Gmail SMTP send to {to_email}", file=sys.stderr)
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{GMAIL_ADDRESS}>"
        msg['To'] = to_email
        
        part1 = MIMEText(plain_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as server:
            server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, [to_email], msg.as_string())
        
        print(f"Gmail SMTP sent successfully to {to_email}", file=sys.stderr)
        return True
    
    except smtplib.SMTPAuthenticationError:
        print("Gmail authentication failed - check credentials", file=sys.stderr)
        return False
    except smtplib.SMTPException as e:
        print(f"Gmail SMTP error: {str(e)}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Gmail error: {str(e)}", file=sys.stderr)
        return False


def save_contact_message(entry):
    try:
        messages = []
        if os.path.exists(CONTACT_MESSAGES_FILE):
            with open(CONTACT_MESSAGES_FILE, 'r', encoding='utf-8') as f:
                messages = json.load(f)
    except Exception:
        messages = []

    messages.append(entry)
    with open(CONTACT_MESSAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(messages, f, indent=2)
    print(f"Saved contact fallback to {CONTACT_MESSAGES_FILE}", file=sys.stderr)

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
        print("=== CONTACT FORM REQUEST RECEIVED ===", file=sys.stderr)
        data = request.get_json()
        print(f"Request data: {data}", file=sys.stderr)
        
        if not data:
            print("No data provided", file=sys.stderr)
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        message = data.get('message', '').strip()
        to_email = data.get('to_email', '').strip()
        
        print(f"Parsed data - Name: {name}, Email: {email}, Phone: {phone}, Message length: {len(message)}", file=sys.stderr)
        
        # Validate required fields
        if not name or not email or not phone or not message:
            print("Validation failed - missing required fields", file=sys.stderr)
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        print("Validation passed, preparing to send email...", file=sys.stderr)
        
        # Determine recipient based on form type
        if to_email:
            recipient = to_email
            subject = f'Message from {name} via Media Panel'
        else:
            recipient = TO_EMAIL
            subject = f'New Contact Message from {name}'
        
        print(f"Sending email to: {recipient}", file=sys.stderr)
        
        # Create email body
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
        
        html_body = f"""
<html>
  <body>
    <h2>The Word of God Deliverance Vineyard Church</h2>
    <h3>New Contact Message</h3>
    <p><strong>Name:</strong> {name}</p>
    <p><strong>Email:</strong> {email}</p>
    <p><strong>Phone:</strong> {phone}</p>
    <h3>Message:</h3>
    <p>{message}</p>
    <hr>
    <p>This message was sent from the church website contact form.</p>
  </body>
</html>
"""

        contact_entry = {
            'timestamp': int(time.time()),
            'name': name,
            'email': email,
            'phone': phone,
            'message': message,
            'recipient': recipient,
            'subject': subject
        }

        def respond_with_saved_message(message):
            if SAVE_CONTACTS_ON_FAILURE:
                save_contact_message(contact_entry)
            return jsonify({'success': True, 'message': message}), 200

        # Send email via configured provider
        try:
            if SENDGRID_API_KEY:
                print("Preparing SendGrid request...", file=sys.stderr)
                sendgrid_url = 'https://api.sendgrid.com/v3/mail/send'
                headers = {
                    'Authorization': f'Bearer {SENDGRID_API_KEY}',
                    'Content-Type': 'application/json'
                }
                payload = {
                    'personalizations': [
                        {
                            'to': [{'email': recipient}],
                            'subject': subject
                        }
                    ],
                    'from': {'email': FROM_EMAIL, 'name': 'The Word of God Church'},
                    'content': [
                        {'type': 'text/plain', 'value': plain_body},
                        {'type': 'text/html', 'value': html_body}
                    ]
                }
                if not to_email:
                    payload['reply_to'] = {'email': email}
                print(f"Sending to SendGrid: {recipient}", file=sys.stderr)
                response = requests.post(sendgrid_url, json=payload, headers=headers, timeout=10)
                
                if response.status_code in [200, 201, 202]:
                    print(f"Email sent successfully to {recipient}", file=sys.stderr)
                    return jsonify({'success': True, 'message': 'Your message has been sent successfully!'})
                else:
                    # SendGrid failed, try Gmail SMTP fallback
                    print(f'SendGrid Error {response.status_code}: Attempting Gmail fallback', file=sys.stderr)
                    if send_email_via_gmail(recipient, subject, plain_body, html_body):
                        print(f"Email sent successfully via Gmail to {recipient}", file=sys.stderr)
                        return jsonify({'success': True, 'message': 'Your message has been sent successfully!'})
                    else:
                        print(f'Both SendGrid and Gmail failed - saving to fallback', file=sys.stderr)
                        return respond_with_saved_message('Email service unavailable. Your message has been stored and will be reviewed by the administrator.')
            else:
                # No SendGrid API key, try Gmail SMTP
                print("No SendGrid API key - attempting Gmail SMTP", file=sys.stderr)
                if send_email_via_gmail(recipient, subject, plain_body, html_body):
                    print(f"Email sent successfully via Gmail to {recipient}", file=sys.stderr)
                    return jsonify({'success': True, 'message': 'Your message has been sent successfully!'})
                else:
                    print(f'Gmail failed - saving to fallback', file=sys.stderr)
                    return respond_with_saved_message('Email service not configured. Your message has been stored and will be reviewed by the administrator.')
        
        except requests.exceptions.Timeout:
            print(f'SendGrid timeout - attempting Gmail fallback', file=sys.stderr)
            if send_email_via_gmail(recipient, subject, plain_body, html_body):
                print(f"Email sent successfully via Gmail to {recipient}", file=sys.stderr)
                return jsonify({'success': True, 'message': 'Your message has been sent successfully!'})
            else:
                return respond_with_saved_message('Email service timed out. Your message has been stored and will be reviewed by the administrator.')
        
        except requests.exceptions.RequestException as req_err:
            print(f'SendGrid request error - attempting Gmail fallback: {str(req_err)}', file=sys.stderr)
            if send_email_via_gmail(recipient, subject, plain_body, html_body):
                print(f"Email sent successfully via Gmail to {recipient}", file=sys.stderr)
                return jsonify({'success': True, 'message': 'Your message has been sent successfully!'})
            else:
                return respond_with_saved_message('Failed to send email. Your message has been stored and will be reviewed by the administrator.')
            
        except Exception as e:
            import traceback
            print(f'Unexpected error in email send: {str(e)}', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return respond_with_saved_message('Failed to send email. Your message has been stored and will be reviewed by the administrator.')
    
    except Exception as e:
        import traceback
        error_msg = f'Error processing request'
        print(f'Unexpected error: {str(e)}', file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return jsonify({'success': False, 'error': error_msg}), 500

if __name__ == '__main__':
    # For local development
    app.run(host='0.0.0.0', port=5000, debug=True)

# For production deployment with gunicorn
# This ensures proper error handling in production
if __name__ != '__main__':
    # Production mode - disable debug
    app.debug = False
