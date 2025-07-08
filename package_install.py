#!/usr/bin/env python3

import subprocess
import sys
import os
import glob

def parse_package_file(filename):
    """Parse package file and return dictionary of sections and packages"""
    packages = {}
    current_section = None
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            elif line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]  # Remove brackets
                packages[current_section] = []
            elif current_section:
                packages[current_section].append(line)
    
    return packages

def install_packages(package_list, section_name):
    """Install packages using apt and return success status with error message"""
    print(f"Installing {section_name} packages...")
    try:
        subprocess.run(['sudo', 'apt', 'install', '-y'] + package_list, 
                      check=True, capture_output=True, text=True)
        print(f"✓ {section_name} packages installed successfully")
        return True, ""
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to install {section_name} packages: {e.stderr}"
        print(f"✗ {error_msg}")
        return False, error_msg

def install_basic_packages(packages):
    """Install basic development packages"""
    if 'dev' not in packages:
        return False, "No 'dev' section found in package list"
    
    success, error = install_packages(packages['dev'], 'basic development')
    return success, error

def install_dwm_dependencies(packages):
    """Install DWM dependencies and compile suckless programs"""
    if 'dwm' not in packages:
        return False, "No 'dwm' section found in package list"
    
    # Install dependencies
    success, error = install_packages(packages['dwm'], 'DWM dependencies')
    if not success:
        return False, error
    
    # Check for suckless programs
    suckless_path = os.path.expanduser("~/projects/programs/suckless/")
    if not os.path.exists(suckless_path):
        return False, f"Suckless directory not found: {suckless_path}"
    
    required_programs = ['dwm', 'st', 'dmenu', 'slock']
    found_programs = []
    
    for program in required_programs:
        pattern = os.path.join(suckless_path, f"{program}*")
        matches = glob.glob(pattern)
        if matches:
            found_programs.extend(matches)
        else:
            return False, f"Required program '{program}' not found in {suckless_path}"
    
    # Compile each program
    for program_path in found_programs:
        if os.path.isdir(program_path):
            print(f"Compiling {os.path.basename(program_path)}...")
            try:
                subprocess.run(['make'], cwd=program_path, check=True, capture_output=True, text=True)
                print(f"✓ {os.path.basename(program_path)} compiled successfully")
            except subprocess.CalledProcessError as e:
                return False, f"Failed to compile {os.path.basename(program_path)}: {e.stderr}"
    
    return True, ""

def install_emacs(packages):
    """Install Emacs from source"""
    # Ask for version
    version = input("Enter Emacs version (default: 30.1): ").strip()
    if not version:
        version = "30.1"
    
    # Download Emacs
    url = f"https://ftp.gnu.org/gnu/emacs/emacs-{version}.tar.gz"
    download_path = f"/tmp/emacs-{version}.tar.gz"
    extract_path = f"/tmp/emacs-{version}"
    
    print(f"Downloading Emacs {version}...")
    try:
        subprocess.run(['wget', url, '-O', download_path], check=True, capture_output=True, text=True)
        print("✓ Emacs downloaded successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to download Emacs: {e.stderr}"
    
    # Extract
    print("Extracting Emacs...")
    try:
        subprocess.run(['tar', '-xzf', download_path, '-C', '/tmp'], check=True, capture_output=True, text=True)
        print("✓ Emacs extracted successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to extract Emacs: {e.stderr}"
    
    # Install dependencies
    if 'emacs' not in packages:
        return False, "No 'emacs' section found in package list"
    
    success, error = install_packages(packages['emacs'], 'Emacs dependencies')
    if not success:
        return False, error
    
    # Configure
    print("Configuring Emacs...")
    try:
        subprocess.run(['./configure', '--with-x-toolkit=gtk3', '--with-native-compilation', 
                       '--with-json', '--with-tree-sitter', '--with-cairo', '--with-modules'], 
                      cwd=extract_path, check=True, capture_output=True, text=True)
        print("✓ Emacs configured successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to configure Emacs: {e.stderr}"
    
    # Make
    print("Compiling Emacs...")
    try:
        nproc = subprocess.run(['nproc'], capture_output=True, text=True).stdout.strip()
        subprocess.run(['make', f'-j{nproc}'], cwd=extract_path, check=True, capture_output=True, text=True)
        print("✓ Emacs compiled successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to compile Emacs: {e.stderr}"
    
    # Make check
    print("Running Emacs tests...")
    try:
        subprocess.run(['make', 'check'], cwd=extract_path, check=True, capture_output=True, text=True)
        print("✓ Emacs tests passed successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to run Emacs tests: {e.stderr}"
    
    # Install Emacs
    print("Installing Emacs...")
    try:
        subprocess.run(['sudo', 'make', 'install'], cwd=extract_path, check=True, capture_output=True, text=True)
        print("✓ Emacs installed successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to install Emacs: {e.stderr}"
    
    return True, ""

def install_stow():
    """Install GNU Stow from source"""
    # Download Stow
    url = "https://ftp.gnu.org/gnu/stow/stow-latest.tar.gz"
    download_path = "/tmp/stow-latest.tar.gz"
    
    print("Downloading GNU Stow...")
    try:
        subprocess.run(['wget', url, '-O', download_path], check=True, capture_output=True, text=True)
        print("✓ GNU Stow downloaded successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to download GNU Stow: {e.stderr}"
    
    # Extract
    print("Extracting GNU Stow...")
    try:
        subprocess.run(['tar', '-xzf', download_path, '-C', '/tmp'], check=True, capture_output=True, text=True)
        print("✓ GNU Stow extracted successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to extract GNU Stow: {e.stderr}"
    
    # Find extracted directory
    try:
        stow_dirs = glob.glob('/tmp/stow-*')
        if not stow_dirs:
            return False, "Could not find extracted Stow directory"
        extract_path = stow_dirs[0]  # Use first match
        print(f"Found extracted directory: {extract_path}")
    except Exception as e:
        return False, f"Error finding extracted directory: {e}"
    
    # Configure
    print("Configuring GNU Stow...")
    try:
        subprocess.run(['./configure'], cwd=extract_path, check=True, capture_output=True, text=True)
        print("✓ GNU Stow configured successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to configure GNU Stow: {e.stderr}"
    
    # Make
    print("Compiling GNU Stow...")
    try:
        subprocess.run(['make'], cwd=extract_path, check=True, capture_output=True, text=True)
        print("✓ GNU Stow compiled successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to compile GNU Stow: {e.stderr}"
    
    # Install Stow
    print("Installing GNU Stow...")
    try:
        subprocess.run(['sudo', 'make', 'install'], cwd=extract_path, check=True, capture_output=True, text=True)
        print("✓ GNU Stow installed successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to install GNU Stow: {e.stderr}"
    
    return True, ""

def install_utils(packages):
    """Install utility packages"""
    if 'utils' not in packages:
        return False, "No 'utils' section found in package list"
    
    success, error = install_packages(packages['utils'], 'utilities')
    return success, error

def show_menu_and_get_choice():
    """Display menu and get user choice"""
    print("\n" + "="*50)
    print("DEBIAN PACKAGE INSTALLER")
    print("="*50)
    print("[0] Install basic development packages")
    print("[1] Install DWM dependencies and compile suckless programs")
    print("[2] Install Emacs from source")
    print("[3] Install GNU Stow from source")
    print("[4] Install basic utilities")
    print("="*50)
    
    choice = input("Enter your choice (e.g., 0,3,5 or 'all'): ").strip()
    return choice

def main():
    # Check if package_list.txt exists
    package_file = os.path.join(os.path.dirname(__file__), 'package_list.txt')
    if not os.path.exists(package_file):
        print(f"Error: package_list.txt not found at {package_file}")
        sys.exit(1)
    
    # Parse package file
    try:
        packages = parse_package_file(package_file)
    except Exception as e:
        print(f"Error parsing package file: {e}")
        sys.exit(1)
    
    # Function mapping
    functions = {
        '0': install_basic_packages,
        '1': install_dwm_dependencies,
        '2': install_emacs,
        '3': install_stow,
        '4': install_utils
    }
    
    while True:
        choice = show_menu_and_get_choice()
        
        if choice.lower() == 'all':
            selected = ['0', '1', '2', '3', '4']
        else:
            selected = [x.strip() for x in choice.split(',')]
        
        for selection in selected:
            if selection in functions:
                print(f"\n--- Executing option {selection} ---")
                success, error = functions[selection](packages)
                if success:
                    print(f"✓ Option {selection} completed successfully")
                else:
                    print(f"✗ Option {selection} failed: {error}")
                    break
            else:
                print(f"Invalid option: {selection}")
        
        continue_choice = input("\nDo you want to continue? (y/n): ").strip().lower()
        if continue_choice != 'y':
            break

if __name__ == "__main__":
    main()
