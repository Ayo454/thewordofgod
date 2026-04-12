#!/usr/bin/env python3
"""
Test script for church website contact form
Run this locally to test the contact form functionality
"""

import requests
import json

def test_contact_form():
    """Test the contact form endpoint"""
    url = "http://127.0.0.1:5000/send-contact"

    # Test data
    test_data = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "123-456-7890",
        "message": "This is a test message from the test script."
    }

    print("Testing contact form...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")

    try:
        response = requests.post(url, json=test_data, headers={'Content-Type': 'application/json'})

        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        try:
            result = response.json()
            print(f"Response JSON: {json.dumps(result, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response Text: {response.text[:500]}...")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_contact_form()