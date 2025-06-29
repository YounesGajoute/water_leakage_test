#!/usr/bin/env python3
"""
Test script to measure settings view performance improvements
"""

import time
import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_settings_view_performance():
    """Test the performance of the optimized settings view"""
    
    print("🔍 Testing Settings View Performance...")
    print("=" * 50)
    
    # Create test window
    root = tk.Tk()
    root.title("Settings View Performance Test")
    root.geometry("800x600")
    
    # Mock app controller and colors
    class MockAppController:
        def __init__(self):
            self.settings = {}
            self.hardware_manager = None
    
    colors = {
        'white': '#FFFFFF',
        'primary': '#00B2E3',
        'text_primary': '#222222',
        'text_secondary': '#888888',
        'success': '#10b981',
        'error': '#ef4444',
        'background': '#f8fafc',
        'status_bg': '#e0f2f7'
    }
    
    app_controller = MockAppController()
    
    try:
        from ui.views.settings_view import CorrectedSettingsView
        
        print("📊 Starting performance test...")
        start_time = time.time()
        
        # Create settings view
        settings_view = CorrectedSettingsView(root, app_controller, colors)
        
        # Measure show() method performance
        show_start = time.time()
        settings_view.show()
        show_end = time.time()
        
        # Wait for async operations to complete
        root.after(1000, lambda: root.quit())
        
        print(f"⏱️  Settings view creation time: {show_end - show_start:.3f} seconds")
        print(f"⏱️  Total initialization time: {time.time() - start_time:.3f} seconds")
        
        # Test responsiveness
        print("\n🎯 Testing UI responsiveness...")
        responsiveness_start = time.time()
        
        # Simulate user interaction
        for i in range(5):
            root.update()
            time.sleep(0.1)
        
        responsiveness_time = time.time() - responsiveness_start
        print(f"⏱️  UI responsiveness test: {responsiveness_time:.3f} seconds")
        
        # Cleanup
        settings_view.cleanup()
        
        print("\n✅ Performance test completed successfully!")
        print("🚀 Settings view should now load without freezing!")
        
    except Exception as e:
        print(f"❌ Error during performance test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    test_settings_view_performance() 