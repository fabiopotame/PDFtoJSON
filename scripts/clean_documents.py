#!/usr/bin/env python3
"""
Script to clean old document folders
"""

import os
import shutil
from pathlib import Path

def clean_documents_folder():
    """Remove documents folder and recreate it empty"""
    documents_path = Path("documents")
    
    if documents_path.exists():
        print(f"Removing folder {documents_path}...")
        shutil.rmtree(documents_path)
        print("Folder removed successfully!")
    
    # Recreate empty folder
    documents_path.mkdir(exist_ok=True)
    print(f"Folder {documents_path} recreated empty!")

def main():
    """Main function"""
    print("===========================================")
    print("Cleaning documents folder")
    print("===========================================")
    
    try:
        clean_documents_folder()
        print("Cleanup completed successfully!")
    except Exception as e:
        print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    main() 