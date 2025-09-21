#!/usr/bin/env python3
"""
Simple run script for the AI Timetable Generator
Run without virtual environment using system Python
"""

import sys
import os

# Add src directory to Python path so imports work
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    # Import and run the Flask app
    from app import app
    
    if __name__ == '__main__':
        print("🚀 Starting AI Timetable Generator...")
        print("📍 Server will be available at: http://127.0.0.1:8080")
        print("🔑 Demo credentials:")
        print("   - Admin: admin/admin123")
        print("   - Faculty: faculty/faculty123") 
        print("   - Student: student1/student123")
        print("⚡ Press Ctrl+C to stop the server")
        print("-" * 50)
        
        app.run(debug=True, host='127.0.0.1', port=8080)
        
except ImportError as e:
    print(f"❌ Error importing required modules: {e}")
    print("\n💡 Please install the required dependencies:")
    print("   pip3 install -r requirements.txt")
    print("\n🔧 Or install individually:")
    print("   pip3 install Flask Flask-Login numpy networkx")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting the application: {e}")
    sys.exit(1)