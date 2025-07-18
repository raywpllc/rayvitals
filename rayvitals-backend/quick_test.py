#!/usr/bin/env python3
"""
Quick test to check if we can import and start the app
"""

import sys
import os

# Add the current directory to path
sys.path.insert(0, '/Users/arosenkoetter/Sites/RavVitals/rayvitals-backend')

try:
    print("Testing imports...")
    from app.main import app
    print("✅ Successfully imported app.main")
    
    from app.services.audit_service import AuditService
    print("✅ Successfully imported AuditService")
    
    from app.services.security_scanner import SecurityScanner
    print("✅ Successfully imported SecurityScanner")
    
    from app.services.performance_scanner import PerformanceScanner
    print("✅ Successfully imported PerformanceScanner")
    
    from app.services.accessibility_scanner import AccessibilityScanner
    print("✅ Successfully imported AccessibilityScanner")
    
    from app.services.ux_scanner import UXScanner
    print("✅ Successfully imported UXScanner")
    
    from app.services.ai_analyzer import AIAnalyzer
    print("✅ Successfully imported AIAnalyzer")
    
    print("\n✅ All imports successful! The application should be able to start.")
    
    # Try to create instances
    print("\nTesting instantiation...")
    audit_service = AuditService()
    print("✅ AuditService instantiated")
    
    security_scanner = SecurityScanner()
    print("✅ SecurityScanner instantiated")
    
    performance_scanner = PerformanceScanner()
    print("✅ PerformanceScanner instantiated")
    
    accessibility_scanner = AccessibilityScanner()
    print("✅ AccessibilityScanner instantiated")
    
    ux_scanner = UXScanner()
    print("✅ UXScanner instantiated")
    
    ai_analyzer = AIAnalyzer()
    print("✅ AIAnalyzer instantiated")
    
    print("\n✅ All services instantiated successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)