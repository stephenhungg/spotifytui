#!/usr/bin/env python3
"""
Real-time log viewer for SpotifyTUI debug logs
Run this in a separate terminal to monitor what's happening in real-time
"""

import os
import time
import sys
from pathlib import Path

def get_log_path():
    """Get the debug log file path"""
    # Look for the log file in the current directory
    log_path = Path("spotifytui_debug.log")
    if not log_path.exists():
        # Try in parent directory if running from src/
        log_path = Path("../spotifytui_debug.log")
    
    return log_path.resolve()

def monitor_log(log_path):
    """Monitor log file for new entries in real-time"""
    print(f"🔍 Monitoring SpotifyTUI debug log: {log_path}")
    print("📝 Press Ctrl+C to stop monitoring\n")
    
    if not log_path.exists():
        print(f"❌ Log file not found: {log_path}")
        print("\n💡 Make sure SpotifyTUI is running first!")
        print("   The log file will be created automatically when you start the app.")
        return
    
    # Show initial content
    print("=" * 80)
    print("📋 LAST 20 LOG ENTRIES:")
    print("=" * 80)
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                # Show last 20 lines
                for line in lines[-20:]:
                    print(line.rstrip())
            else:
                print("📝 Log file is empty - waiting for first entries...")
    except Exception as e:
        print(f"❌ Error reading log: {e}")
        return
    
    print("\n" + "=" * 80)
    print("🔄 LIVE MONITORING (new entries will appear below):")
    print("=" * 80)
    
    # Monitor for new entries
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            # Go to end of file
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    print(line.rstrip())
                else:
                    time.sleep(0.1)  # Small delay to avoid busy waiting
                    
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped")
    except Exception as e:
        print(f"\n❌ Error monitoring log: {e}")

def show_log_stats(log_path):
    """Show basic statistics about the log file"""
    if not log_path.exists():
        print(f"❌ Log file not found: {log_path}")
        return
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        print(f"📊 Log file statistics:")
        print(f"   📁 Location: {log_path}")
        print(f"   📄 Total lines: {len(lines)}")
        
        if lines:
            # Count log levels
            levels = {}
            for line in lines:
                if ' | ' in line:
                    parts = line.split(' | ')
                    if len(parts) >= 3:
                        level = parts[2].strip()
                        levels[level] = levels.get(level, 0) + 1
            
            print(f"   📈 Log levels:")
            for level, count in sorted(levels.items()):
                print(f"      {level}: {count}")
            
            # Show last entry
            last_line = lines[-1].strip()
            if last_line:
                print(f"   🕐 Last entry: {last_line[:100]}...")
        
    except Exception as e:
        print(f"❌ Error reading log stats: {e}")

def main():
    """Main function"""
    log_path = get_log_path()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--stats":
            show_log_stats(log_path)
            return
        elif sys.argv[1] == "--help":
            print("🔍 SpotifyTUI Log Viewer")
            print("=" * 40)
            print("Usage:")
            print("  python3 log_viewer.py          # Live monitoring")
            print("  python3 log_viewer.py --stats  # Show log statistics")
            print("  python3 log_viewer.py --help   # Show this help")
            print()
            print("💡 Run this in a separate terminal while SpotifyTUI is running")
            print("   to see real-time debug information!")
            return
    
    # Default: live monitoring
    print("🔍 SpotifyTUI Log Viewer")
    print("=" * 40)
    monitor_log(log_path)

if __name__ == "__main__":
    main()


