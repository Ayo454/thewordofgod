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

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/send-contact', methods=['POST', 'OPTIONS'])
def send_contact():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        message = data.get('message', '').strip()
        to_email = data.get('to_email', '').strip()  # New field for custom recipient
        
        # For media panel form, only email, phone, message are required
        # For main contact form, name is also required
        if to_email:
            # Media panel form - send to specified email
            if not name or not email or not phone or not message:
                return jsonify({'success': False, 'error': 'All fields are required'}), 400
            recipient = to_email
            subject = f'Message from {name} via Media Panel'
        else:
            # Main contact form - send to church email
            if not name or not email or not phone or not message:
                return jsonify({'success': False, 'error': 'All fields are required'}), 400
            recipient = GMAIL_ADDRESS
            subject = f'New Contact Message from {name}'
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['From'] = 'The Word of God Deliverance Vineyard Church <' + GMAIL_ADDRESS + '>'
        msg['To'] = recipient
        msg['Subject'] = subject
        if not to_email:
            msg['Reply-To'] = email
        
        if to_email:
            # Media panel message
            plain_body = f"""
The Word of God Deliverance Vineyard Church
Message from Media Panel:

Name: {name}
Phone: {phone}

Message:
{message}

Reply to: {email}
"""

            html_body = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #333; background: #f7f7f7; margin: 0; padding: 0;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); overflow: hidden;">
      <!-- Header with Logo and Church Name -->
      <tr>
        <td style="padding: 24px; text-align: center; background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);">
          <img src="https://god-word.onrender.com/logo.jpg" alt="The Word of God Deliverance Vineyard Church" style="max-width: 80px; height: auto; margin-bottom: 16px; border-radius: 8px;">
          <h1 style="margin: 0 0 4px; color: #ffffff; font-size: 24px; font-weight: bold;">The Word of God Deliverance</h1>
          <p style="margin: 0; color: #e0e7ff; font-size: 14px;">Vineyard Church</p>
        </td>
      </tr>
      <!-- Content -->
      <tr>
        <td style="padding: 24px;">
          <h2 style="margin: 0 0 12px; color: #1d4ed8;">New Message Received</h2>
          <p style="margin: 0 0 20px; color: #555; font-size: 14px;">A message has been sent from the media panel contact form.</p>
          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">
            <tr>
              <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb; font-weight: bold; color: #1d4ed8; width: 130px;">Name</td>
              <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb; color: #333;">{name}</td>
            </tr>
            <tr>
              <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb; font-weight: bold; color: #1d4ed8;">Phone</td>
              <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;"><a href="tel:{phone}" style="color: #2563eb; text-decoration: none;">{phone}</a></td>
            </tr>
            <tr>
              <td style="padding: 12px 0; font-weight: bold; color: #1d4ed8; vertical-align: top;">Message</td>
              <td style="padding: 12px 0; white-space: pre-wrap; color: #444; line-height: 1.6;">{message}</td>
            </tr>
          </table>
          <p style="margin: 16px 0 0; padding-top: 16px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 12px;"><strong>From:</strong> {email}</p>
        </td>
      </tr>
      <!-- Footer -->
      <tr>
        <td style="padding: 20px 24px; background: #f3f4f6; text-align: center; border-top: 1px solid #e5e7eb;">
          <p style="margin: 0; color: #6b7280; font-size: 12px;">© 2026 The Word of God Deliverance Vineyard Church. All rights reserved.</p>
          <p style="margin: 8px 0 0; color: #9ca3af; font-size: 11px;">This is an automated message from our contact management system.</p>
        </td>
      </tr>
    </table>
  </body>
</html>
"""
        else:
            # Original contact form message
            plain_body = f"""
The Word of God Deliverance Vineyard Church
New Contact Message:

Name: {name}
Phone: {phone}

Message:
{message}

Reply to: {email}
"""

            html_body = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #333; background: #f7f7f7; margin: 0; padding: 0;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); overflow: hidden;">
      <!-- Header with Logo and Church Name -->
      <tr>
        <td style="padding: 24px; text-align: center; background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);">
          <img src="https://god-word.onrender.com/logo.jpg" alt="The Word of God Deliverance Vineyard Church" style="max-width: 80px; height: auto; margin-bottom: 16px; border-radius: 8px;">
          <h1 style="margin: 0 0 4px; color: #ffffff; font-size: 24px; font-weight: bold;">The Word of God Deliverance</h1>
          <p style="margin: 0; color: #e0e7ff; font-size: 14px;">Vineyard Church</p>
        </td>
      </tr>
      <!-- Content -->
      <tr>
        <td style="padding: 24px;">
          <h2 style="margin: 0 0 12px; color: #1d4ed8;">New Contact Message</h2>
          <p style="margin: 0 0 20px; color: #555; font-size: 14px;">A new message has been submitted through the contact form.</p>
          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">
            <tr>
              <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb; font-weight: bold; color: #1d4ed8; width: 130px;">Name</td>
              <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb; color: #333;">{name}</td>
            </tr>
            <tr>
              <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb; font-weight: bold; color: #1d4ed8;">Phone</td>
              <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;"><a href="tel:{phone}" style="color: #2563eb; text-decoration: none;">{phone}</a></td>
            </tr>
            <tr>
              <td style="padding: 12px 0; font-weight: bold; color: #1d4ed8; vertical-align: top;">Message</td>
              <td style="padding: 12px 0; white-space: pre-wrap; color: #444; line-height: 1.6;">{message}</td>
            </tr>
          </table>
          <p style="margin: 16px 0 0; padding-top: 16px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 12px;"><strong>From:</strong> {email}</p>
        </td>
      </tr>
      <!-- Footer -->
      <tr>
        <td style="padding: 20px 24px; background: #f3f4f6; text-align: center; border-top: 1px solid #e5e7eb;">
          <p style="margin: 0; color: #6b7280; font-size: 12px;">© 2026 The Word of God Deliverance Vineyard Church. All rights reserved.</p>
          <p style="margin: 8px 0 0; color: #9ca3af; font-size: 11px;">This is an automated message from our contact management system.</p>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

        msg.attach(MIMEText(plain_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
                server.send_message(msg)
            print(f'✓ Email sent successfully from {GMAIL_ADDRESS} to {recipient}')
        except smtplib.SMTPAuthenticationError as auth_err:
            print(f'✗ Gmail authentication failed: {str(auth_err)}')
            print(f'  Check the Gmail password and ensure 2FA is disabled or an App Password is used.')
            raise
        except smtplib.SMTPException as smtp_err:
            print(f'✗ SMTP error: {str(smtp_err)}')
            raise
        
        return jsonify({'success': True, 'message': 'Your message has been sent successfully!'})
    
    except Exception as e:
        import traceback
        print(f'✗ Error sending email: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to send message. Please try again.'}), 500

if __name__ == '__main__':
    # For local development
    app.run(host='0.0.0.0', port=5000, debug=True)

    # For production deployment with gunicorn, use:
    # gunicorn app:app -b 0.0.0.0:$PORT
