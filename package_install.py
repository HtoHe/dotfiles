#!/usr/bin/env python3

import subprocess
import sys
import os
import glob
import re
import urllib.request

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
    
    required_programs = ['dwm', 'st', 'dmenu', 'slock', 'slstatus']
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
            program_name = os.path.basename(program_path)
            print(f"Compiling {program_name}...")
            try:
                subprocess.run(['make'], cwd=program_path, check=True, capture_output=True, text=True)
                print(f"✓ {program_name} compiled successfully")
            except subprocess.CalledProcessError as e:
                return False, f"Failed to compile {program_name}: {e.stderr}"
            
            # Install the program
            print(f"Installing {program_name}...")
            try:
                subprocess.run(['sudo', 'make', 'install'], cwd=program_path, check=True, capture_output=True, text=True)
                print(f"✓ {program_name} installed successfully")
            except subprocess.CalledProcessError as e:
                return False, f"Failed to install {program_name}: {e.stderr}"
    
    return True, ""

def get_latest_emacs_version():
    """Fetch the latest Emacs version from ftp.gnu.org"""
    try:
        print("Fetching latest Emacs version...")
        response = urllib.request.urlopen('https://ftp.gnu.org/gnu/emacs/', timeout=10)
        html = response.read().decode('utf-8')
        
        # Find all emacs version links (emacs-X.Y.tar.gz format)
        version_pattern = r'emacs-([0-9]+\.[0-9]+(?:\.[0-9]+)?).tar.gz'
        matches = re.findall(version_pattern, html)
        
        if matches:
            # Sort versions and get the latest
            versions = []
            for version in matches:
                # Parse version numbers for proper sorting
                parts = [int(x) for x in version.split('.')]
                versions.append((parts, version))
            
            versions.sort(reverse=True)
            latest_version = versions[0][1]
            print(f"✓ Latest Emacs version found: {latest_version}")
            return latest_version
        else:
            print("⚠ Could not determine latest version, using fallback")
            return "30.1"
    except Exception as e:
        print(f"⚠ Error fetching latest version ({e}), using fallback")
        return "30.1"

def install_emacs(packages):
    """Install Emacs from source"""
    # Get latest version as default
    latest_version = get_latest_emacs_version()
    
    # Ask for version
    version = input(f"Enter Emacs version (default: {latest_version}): ").strip()
    if not version:
        version = latest_version
    
    # Download Emacs with backup mirrors
    download_path = f"/tmp/emacs-{version}.tar.gz"
    extract_path = f"/tmp/emacs-{version}"
    
    # Define mirror list in order of preference
    mirrors = [
        f"https://ftp.kaist.ac.kr/gnu/emacs/emacs-{version}.tar.gz",
        f"https://ftp.gnu.org/gnu/emacs/emacs-{version}.tar.gz",
        f"https://ftp.jaist.ac.jp/pub/GNU/emacs/emacs-{version}.tar.gz",
        f"https://ftpmirror.gnu.org/emacs/emacs-{version}.tar.gz"
    ]
    
    print(f"Downloading Emacs {version}...")
    download_success = False
    
    for i, url in enumerate(mirrors):
        mirror_name = url.split('/')[2]  # Extract domain name
        print(f"Trying mirror {i+1}/{len(mirrors)}: {mirror_name}")
        print(f"URL: {url}")
        try:
            # Use timeout of 60 seconds per attempt and show progress
            subprocess.run(['wget', '--timeout=60', '--tries=2', '--progress=dot:giga',
                          url, '-O', download_path], check=True, text=True)
            print("✓ Emacs downloaded successfully")
            download_success = True
            break
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed from {mirror_name}: {e.returncode}")
            if i < len(mirrors) - 1:  # Not the last mirror
                print("  Trying next mirror...")
            continue
    
    if not download_success:
        return False, f"Failed to download Emacs from all mirrors"
    
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
                        '--with-json', '--with-tree-sitter', '--with-cairo', '--with-modules', '--with-xml2'], 
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
    nproc = subprocess.run(['nproc'], capture_output=True, text=True).stdout.strip()
    result = subprocess.run(['make', 'check', f'-j{nproc}'], cwd=extract_path, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Emacs tests passed successfully")
    else:
        print("⚠ Emacs tests completed with issues (this may be due to dbus bug)")
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print("STDOUT:", result.stdout[-1000:])  # Show last 1000 chars
        if result.stderr:
            print("STDERR:", result.stderr[-1000:])  # Show last 1000 chars
        
        proceed = input("\nDo you want to proceed with installation despite test issues? (y/n): ").strip().lower()
        if proceed != 'y':
            return False, "Installation cancelled by user due to test issues"
    
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
        # First, remove any existing stow directories to avoid conflicts
        existing_dirs = glob.glob('/tmp/stow-*')
        for d in existing_dirs:
            if os.path.isdir(d):
                subprocess.run(['rm', '-rf', d], check=True)
        
        subprocess.run(['tar', '-xzf', download_path, '-C', '/tmp'], check=True, capture_output=True, text=True)
        print("✓ GNU Stow extracted successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to extract GNU Stow: {e.stderr}"
    
    # Find extracted directory (should be created after extraction)
    try:
        stow_dirs = glob.glob('/tmp/stow-*')
        stow_dirs = [d for d in stow_dirs if os.path.isdir(d)]  # Only directories
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

def install_bluetuith():
    """Install bluetuith - TUI bluetooth manager"""
    print("Installing bluetuith dependencies...")
    
    # Install dependencies
    deps = ['golang-go', 'bluez', 'bluetooth', 'pulseaudio-module-bluetooth', 'wget']
    try:
        subprocess.run(['sudo', 'apt', 'install', '-y'] + deps, 
                      check=True, capture_output=True, text=True)
        print("✓ bluetuith dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to install bluetuith dependencies: {e.stderr}"
    
    # Set up Go environment with custom GOPATH
    go_path = os.path.expanduser("~/.local/share/go")
    os.makedirs(go_path, exist_ok=True)
    
    env = os.environ.copy()
    env['GOPATH'] = go_path
    env['PATH'] = f"{go_path}/bin:{env.get('PATH', '')}"
    
    print(f"Using custom GOPATH: {go_path}")
    
    # Install bluetuith using go install (updated repository path)
    print("Installing bluetuith...")
    try:
        subprocess.run(['go', 'install', 'github.com/darkhz/bluetuith@latest'],
                      check=True, capture_output=True, text=True, env=env)
        print("✓ bluetuith installed successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to install bluetuith: {e.stderr}"
    
    # Add Go bin to PATH in .bashrc if not already present
    bashrc_path = os.path.expanduser('~/.bashrc')
    go_path_line = f'export PATH="{go_path}/bin:$PATH"'
    
    try:
        if os.path.exists(bashrc_path):
            with open(bashrc_path, 'r') as f:
                content = f.read()
            if go_path_line not in content:
                with open(bashrc_path, 'a') as f:
                    f.write(f'\n# Go PATH for bluetuith\n{go_path_line}\n')
        else:
            with open(bashrc_path, 'w') as f:
                f.write(f'# Go PATH for bluetuith\n{go_path_line}\n')
        print("✓ Go PATH added to .bashrc")
    except Exception as e:
        print(f"⚠ Warning: Failed to update .bashrc: {e}")
    
    print(f"\n✓ bluetuith installation completed!")
    print(f"Binary location: {go_path}/bin/bluetuith")
    print("Please restart your shell or run 'source ~/.bashrc' to update PATH")
    
    return True, ""

def install_ncpamixer():
    """Install ncpamixer - ncurses PulseAudio mixer"""
    print("Installing ncpamixer dependencies...")
    
    # Install dependencies
    deps = ['libpulse-dev', 'libncurses5-dev', 'libncursesw5-dev', 'cmake', 
            'pulseaudio', 'build-essential', 'git', 'pandoc']
    try:
        subprocess.run(['sudo', 'apt', 'install', '-y'] + deps, 
                      check=True, capture_output=True, text=True)
        print("✓ ncpamixer dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to install ncpamixer dependencies: {e.stderr}"
    
    # Clone ncpamixer repository
    temp_dir = "/tmp/ncpamixer"
    print("Cloning ncpamixer repository...")
    try:
        if os.path.exists(temp_dir):
            subprocess.run(['rm', '-rf', temp_dir], check=True)
        subprocess.run(['git', 'clone', 'https://github.com/fulhax/ncpamixer.git', temp_dir], 
                      check=True, capture_output=True, text=True)
        print("✓ ncpamixer repository cloned successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to clone ncpamixer repository: {e.stderr}"
    
    # Build ncpamixer
    print("Building ncpamixer...")
    try:
        subprocess.run(['make', 'USE_WIDE=True'], cwd=temp_dir, check=True, capture_output=True, text=True)
        print("✓ ncpamixer compiled successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to compile ncpamixer: {e.stderr}"
    
    # Install ncpamixer
    print("Installing ncpamixer...")
    try:
        subprocess.run(['sudo', 'make', 'install'], cwd=temp_dir, check=True, capture_output=True, text=True)
        print("✓ ncpamixer installed successfully")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to install ncpamixer: {e.stderr}"
    
    # Add pulseaudio --start to .xinitrc
    xinitrc_path = os.path.expanduser('~/.xinitrc')
    pulseaudio_line = 'pulseaudio --start'
    
    print("Adding pulseaudio --start to .xinitrc...")
    try:
        if os.path.exists(xinitrc_path):
            with open(xinitrc_path, 'r') as f:
                content = f.read()
            if pulseaudio_line not in content:
                with open(xinitrc_path, 'a') as f:
                    f.write(f'\n# Start PulseAudio for ncpamixer\n{pulseaudio_line}\n')
        else:
            with open(xinitrc_path, 'w') as f:
                f.write(f'# Start PulseAudio for ncpamixer\n{pulseaudio_line}\n')
        print("✓ pulseaudio --start added to .xinitrc")
    except Exception as e:
        print(f"⚠ Warning: Failed to update .xinitrc: {e}")
    
    print("\n✓ ncpamixer installation completed!")
    print("Run 'ncpamixer' to start the mixer")
    
    return True, ""

def check_emacs_server_status():
    """Check if Emacs server systemctl service is configured"""
    emacs_path = subprocess.run(['which', 'emacs'], capture_output=True, text=True)
    if emacs_path.returncode != 0:
        return 'N'  # Emacs not installed
    
    service_file = os.path.expanduser('~/.config/systemd/user/emacs.service')
    if not os.path.exists(service_file):
        return 'X'  # Service file doesn't exist
    
    bashrc_path = os.path.expanduser('~/.bashrc')
    if os.path.exists(bashrc_path):
        with open(bashrc_path, 'r') as f:
            content = f.read()
            if 'alias emacs="emacsclient -c -a emacs"' not in content:
                return 'X'  # Alias not configured
    else:
        return 'X'  # .bashrc doesn't exist
    
    try:
        enabled = subprocess.run(['systemctl', '--user', 'is-enabled', 'emacs.service'], 
                               capture_output=True, text=True)
        active = subprocess.run(['systemctl', '--user', 'is-active', 'emacs.service'], 
                               capture_output=True, text=True)
        if enabled.returncode == 0 and active.returncode == 0:
            return 'O'  # Service enabled and running
        else:
            return 'X'  # Service exists but not enabled or not running
    except:
        return 'X'

def setup_emacs_server():
    """Setup Emacs server as systemctl service"""
    emacs_path = subprocess.run(['which', 'emacs'], capture_output=True, text=True)
    if emacs_path.returncode != 0:
        return False, "Emacs not installed"
    
    emacs_executable = emacs_path.stdout.strip()
    
    # Create systemd user directory
    user_systemd_dir = os.path.expanduser('~/.config/systemd/user')
    os.makedirs(user_systemd_dir, exist_ok=True)
    
    # Create service file
    service_content = f"""[Unit]
Description=Emacs text editor
Documentation=info:emacs man:emacs(1) https://gnu.org/software/emacs/

[Service]
Type=forking
ExecStart={emacs_executable} --daemon
ExecStop={emacs_executable} --eval "(kill-emacs)"
Environment=SSH_AUTH_SOCK=%t/keyring/ssh
Restart=on-failure
TimeoutStartSec=10

[Install]
WantedBy=default.target
"""
    
    service_file = os.path.join(user_systemd_dir, 'emacs.service')
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        print("✓ Emacs service file created")
    except Exception as e:
        return False, f"Failed to create service file: {e}"
    
    # Add function and alias to .bashrc
    bashrc_path = os.path.expanduser('~/.bashrc')
    emacs_config = '''# Emacs client function and alias
emacs() {
    emacsclient -c "$@" &
}
alias emacsnw='emacsclient -t'
'''
    
    try:
        if os.path.exists(bashrc_path):
            with open(bashrc_path, 'r') as f:
                content = f.read()
            if 'emacs()' not in content:
                with open(bashrc_path, 'a') as f:
                    f.write(f'\n{emacs_config}')
                print("✓ Emacs function and terminal alias added to .bashrc")
            else:
                print("✓ Emacs function already configured in .bashrc")
        else:
            with open(bashrc_path, 'w') as f:
                f.write(f'{emacs_config}')
            print("✓ Created .bashrc with Emacs function and terminal alias")
    except Exception as e:
        return False, f"Failed to update .bashrc: {e}"
    
    # Create Emacs wrapper script for dmenu
    print("Creating Emacs wrapper script for dmenu...")
    wrapper_content = '''#!/bin/bash
export DISPLAY=:0
export XDG_RUNTIME_DIR=/run/user/$(id -u)
emacsclient -c -a emacs "$@"
'''
    
    try:
        subprocess.run(['sudo', 'tee', '/usr/local/bin/Emacs'], 
                      input=wrapper_content.encode(), check=True, capture_output=True)
        subprocess.run(['sudo', 'chmod', '+x', '/usr/local/bin/Emacs'], check=True)
        print("✓ Emacs wrapper script created for dmenu")
    except subprocess.CalledProcessError as e:
        print(f"⚠ Warning: Failed to create wrapper script: {e}")
    
    # Enable and start service
    try:
        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', '--user', 'enable', 'emacs.service'], check=True)
        subprocess.run(['systemctl', '--user', 'start', 'emacs.service'], check=True)
        print("✓ Emacs service enabled and started")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to enable service: {e}"
    
    return True, ""

def check_firefox_private_status():
    """Check if Firefox private dmenu item is configured"""
    dmenu_path = subprocess.run(['which', 'dmenu'], capture_output=True, text=True)
    if dmenu_path.returncode != 0:
        return 'N'  # dmenu not installed
    
    firefox_files = glob.glob('/usr/share/applications/*firefox*')
    if not firefox_files:
        return 'N'  # Firefox not installed
    
    private_desktop = '/usr/share/applications/firefox-private.desktop'
    if os.path.exists(private_desktop):
        return 'O'  # Firefox private desktop file exists
    else:
        return 'X'  # Firefox private desktop file doesn't exist

def check_displayport_status():
    """Check if DisplayPort auto-switching is configured"""
    xrandr_path = subprocess.run(['which', 'xrandr'], capture_output=True, text=True)
    if xrandr_path.returncode != 0:
        return 'N'  # xrandr not installed
    
    udev_rule = '/etc/udev/rules.d/95-displayport-monitor.rules'
    switch_script = '/usr/local/bin/display-switch.sh'
    
    if os.path.exists(udev_rule) and os.path.exists(switch_script):
        # Check if script is executable
        if os.access(switch_script, os.X_OK):
            return 'O'  # Both files exist and script is executable
        else:
            return 'X'  # Files exist but script not executable
    else:
        return 'X'  # Files don't exist

def check_power_management_status():
    """Check if power management (screen timeout + hibernate) is configured"""
    xset_path = subprocess.run(['which', 'xset'], capture_output=True, text=True)
    if xset_path.returncode != 0:
        return 'N'  # xset not installed
    
    # Check if xprofile has xset dpms setting
    xprofile_path = os.path.expanduser('~/.xprofile')
    has_xprofile_setting = False
    if os.path.exists(xprofile_path):
        with open(xprofile_path, 'r') as f:
            content = f.read()
            if 'xset dpms' in content:
                has_xprofile_setting = True
    
    # Check if logind.conf has hibernate setting
    logind_config = '/etc/systemd/logind.conf'
    has_hibernate_setting = False
    if os.path.exists(logind_config):
        try:
            with open(logind_config, 'r') as f:
                content = f.read()
                if 'IdleAction=hibernate' in content and 'IdleActionSec=15min' in content:
                    has_hibernate_setting = True
        except PermissionError:
            # Can't read the file, assume not configured
            pass
    
    if has_xprofile_setting and has_hibernate_setting:
        return 'O'  # Both configured
    elif has_xprofile_setting or has_hibernate_setting:
        return 'X'  # Partially configured
    else:
        return 'X'  # Not configured

def setup_firefox_private():
    """Setup Firefox private dmenu item"""
    dmenu_path = subprocess.run(['which', 'dmenu'], capture_output=True, text=True)
    if dmenu_path.returncode != 0:
        return False, "dmenu not installed"
    
    firefox_files = glob.glob('/usr/share/applications/*firefox*')
    if not firefox_files:
        return False, "Firefox not installed"
    
    # Create Firefox private desktop file
    desktop_content = """[Desktop Entry]
Name=Firefox Private
Comment=Browse the Web in Private Mode
GenericName=Web Browser
X-GNOME-FullName=Firefox Private Web Browser
Exec=firefox --private-window
Terminal=false
X-MultipleArgs=false
Type=Application
Icon=firefox
Categories=Network;WebBrowser;
MimeType=text/html;text/xml;application/xhtml+xml;application/xml;application/vnd.mozilla.xul+xml;application/rss+xml;application/rdf+xml;image/gif;image/jpeg;image/png;x-scheme-handler/http;x-scheme-handler/https;x-scheme-handler/ftp;x-scheme-handler/chrome;video/webm;application/x-xpinstall;
StartupNotify=true
"""
    
    desktop_file = '/usr/share/applications/firefox-private.desktop'
    try:
        subprocess.run(['sudo', 'tee', desktop_file], input=desktop_content.encode(), check=True, capture_output=True)
        subprocess.run(['sudo', 'chmod', '644', desktop_file], check=True)
        print("✓ Firefox private desktop file created")
    except Exception as e:
        return False, f"Failed to create desktop file: {e}"
    
    return True, ""

def setup_displayport_switching():
    """Setup DisplayPort auto-switching with udev rules"""
    xrandr_path = subprocess.run(['which', 'xrandr'], capture_output=True, text=True)
    if xrandr_path.returncode != 0:
        return False, "xrandr not installed"
    
    # Create udev rule content - improved to trigger on specific events
    udev_rule_content = '''# DisplayPort hotplug detection
ACTION=="change", SUBSYSTEM=="drm", ENV{HOTPLUG}=="1", RUN+="/usr/local/bin/display-switch.sh"
# Additional rule for connector status changes
ACTION=="change", SUBSYSTEM=="drm", KERNEL=="card[0-9]-*", RUN+="/usr/local/bin/display-switch.sh"
'''
    
    # Create improved display switching script content
    script_content = """#!/bin/bash

# Enhanced DisplayPort auto-switching script
# Log for debugging
exec >> /tmp/display-switch.log 2>&1
echo "$(date): Display switch event triggered by udev"
echo "$(date): Event details: ACTION=$ACTION SUBSYSTEM=$SUBSYSTEM HOTPLUG=$HOTPLUG"

# Enhanced X server detection and user identification
wait_for_x_server() {
    local max_wait=45
    local count=0
    
    echo "$(date): Starting X server detection..."
    
    while [ $count -lt $max_wait ]; do
        # Method 1: Check for active X sessions via loginctl (most reliable)
        if command -v loginctl >/dev/null 2>&1; then
            ACTIVE_SESSION=$(loginctl list-sessions --no-legend | awk '$3=="active" && $4=="x11" {print $1}' | head -1)
            if [ -n "$ACTIVE_SESSION" ]; then
                X_USER=$(loginctl show-session "$ACTIVE_SESSION" -p Name --value 2>/dev/null)
                DISPLAY_VAR=$(loginctl show-session "$ACTIVE_SESSION" -p Display --value 2>/dev/null)
                if [ -n "$X_USER" ] && [ -n "$DISPLAY_VAR" ]; then
                    export DISPLAY="$DISPLAY_VAR"
                    export XAUTHORITY="/home/$X_USER/.Xauthority"
                    echo "$(date): Found active X11 session: user=$X_USER, display=$DISPLAY_VAR"
                    
                    # Test X server accessibility with timeout
                    if timeout 10 sudo -u "$X_USER" -E /usr/bin/xrandr --query >/dev/null 2>&1; then
                        echo "$(date): X server accessible via loginctl method"
                        return 0
                    fi
                fi
            fi
        fi
        
        # Method 2: Look for X processes and match with users
        X_PROC=$(pgrep -f "Xorg.*:0\|X.*:0" | head -1)
        if [ -n "$X_PROC" ]; then
            X_USER=$(ps -o user= -p "$X_PROC" 2>/dev/null)
            if [ -n "$X_USER" ] && [ "$X_USER" != "root" ]; then
                export DISPLAY=:0
                export XAUTHORITY="/home/$X_USER/.Xauthority"
                echo "$(date): Found X process: user=$X_USER, pid=$X_PROC"
                
                # Test X server accessibility
                if timeout 10 sudo -u "$X_USER" -E /usr/bin/xrandr --query >/dev/null 2>&1; then
                    echo "$(date): X server accessible via process method"
                    return 0
                fi
            fi
        fi
        
        # Method 3: Check for users logged into graphical sessions
        for user in $(who | awk '$2 ~ /^:[0-9]/ || $2 ~ /^tty[0-9]/ {print $1}' | sort -u); do
            if [ -f "/home/$user/.Xauthority" ]; then
                export DISPLAY=:0
                export XAUTHORITY="/home/$user/.Xauthority"
                echo "$(date): Trying user from who output: $user"
                
                if timeout 10 sudo -u "$user" -E /usr/bin/xrandr --query >/dev/null 2>&1; then
                    X_USER="$user"
                    echo "$(date): X server accessible via who method, user=$user"
                    return 0
                fi
            fi
        done
        
        echo "$(date): Waiting for X server... attempt $((count + 1))/$max_wait"
        sleep 2
        count=$((count + 1))
    done
    
    echo "$(date): ERROR: Timeout waiting for accessible X server after $max_wait attempts"
    return 1
}

# Function to perform display switching with better error handling
perform_display_switch() {
    local user="$1"
    
    echo "$(date): Performing display switch as user: $user"
    
    # Check current display configuration
    local current_displays
    current_displays=$(timeout 10 sudo -u "$user" -E /usr/bin/xrandr 2>/dev/null)
    if [ $? -ne 0 ]; then
        echo "$(date): ERROR: Failed to query current display configuration"
        return 1
    fi
    
    echo "$(date): Current display status:"
    echo "$current_displays" | grep -E "(connected|disconnected)" | while read line; do
        echo "$(date):   $line"
    done
    
    # Check for connected DisplayPort
    local dp_outputs
    dp_outputs=$(echo "$current_displays" | grep -E "DP-[0-9](-[0-9])* connected" | awk '{print $1}')
    
    if [ -n "$dp_outputs" ]; then
        # DisplayPort connected - switch to external display
        local primary_dp
        primary_dp=$(echo "$dp_outputs" | head -1)
        echo "$(date): DisplayPort detected: $primary_dp"
        echo "$(date): Switching to external DisplayPort display"
        
        # Switch to DisplayPort and turn off laptop display
        if timeout 15 sudo -u "$user" -E /usr/bin/xrandr --output eDP-1 --off --output "$primary_dp" --auto --primary 2>/dev/null; then
            echo "$(date): SUCCESS: Switched to DisplayPort $primary_dp"
        else
            echo "$(date): ERROR: Failed to switch to DisplayPort $primary_dp"
            return 1
        fi
    else
        # No DisplayPort connected - switch back to laptop display
        echo "$(date): No DisplayPort detected, switching to laptop display"
        
        # Turn off all DisplayPort outputs and enable laptop display
        local all_dp_outputs
        all_dp_outputs=$(echo "$current_displays" | grep -E "DP-[0-9](-[0-9])*" | awk '{print $1}')
        
        for dp in $all_dp_outputs; do
            timeout 10 sudo -u "$user" -E /usr/bin/xrandr --output "$dp" --off 2>/dev/null
            echo "$(date): Turned off DisplayPort: $dp"
        done
        
        # Enable laptop display
        if timeout 15 sudo -u "$user" -E /usr/bin/xrandr --output eDP-1 --auto --primary 2>/dev/null; then
            echo "$(date): SUCCESS: Switched to laptop display (eDP-1)"
        else
            echo "$(date): ERROR: Failed to switch to laptop display"
            return 1
        fi
    fi
    
    return 0
}

# Main execution
echo "$(date): ==================================="
echo "$(date): DisplayPort Auto-Switch Starting"
echo "$(date): ==================================="

# Wait for X server to be available
if ! wait_for_x_server; then
    echo "$(date): FATAL: X server not accessible, aborting"
    exit 1
fi

# Perform the display switch
if perform_display_switch "$X_USER"; then
    echo "$(date): Display switch completed successfully"
else
    echo "$(date): Display switch failed"
    exit 1
fi

echo "$(date): ==================================="
echo "$(date): DisplayPort Auto-Switch Complete"
echo "$(date): ==================================="
"""
    
    # Step 1: Create udev rule file
    print("Creating udev rule file...")
    try:
        subprocess.run(['sudo', 'tee', '/etc/udev/rules.d/95-displayport-monitor.rules'], 
                      input=udev_rule_content.encode(), check=True, capture_output=True)
        print("✓ udev rule file created")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to create udev rule file: {e}"
    
    # Step 2: Create the switching script
    print("Creating display switching script...")
    try:
        subprocess.run(['sudo', 'tee', '/usr/local/bin/display-switch.sh'], 
                      input=script_content.encode(), check=True, capture_output=True)
        print("✓ Display switching script created")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to create switching script: {e}"
    
    # Step 3: Make script executable
    print("Making script executable...")
    try:
        subprocess.run(['sudo', 'chmod', '+x', '/usr/local/bin/display-switch.sh'], check=True)
        print("✓ Script made executable")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to make script executable: {e}"
    
    # Step 4: Reload udev rules
    print("Reloading udev rules...")
    try:
        subprocess.run(['sudo', 'udevadm', 'control', '--reload-rules'], check=True)
        print("✓ udev rules reloaded")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to reload udev rules: {e}"
    
    # Step 5: Trigger udev rules to ensure they're active
    print("Triggering udev rules for DRM subsystem...")
    try:
        subprocess.run(['sudo', 'udevadm', 'trigger', '--subsystem-match=drm'], check=True)
        print("✓ udev rules triggered")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to trigger udev rules: {e}"
    
    # Step 6: Create systemd service to ensure script runs on boot (backup method)
    print("Creating systemd service for boot-time display detection...")
    service_content = """[Unit]
Description=DisplayPort Auto-Switch Boot Service
After=graphical.target
Wants=graphical.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/display-switch.sh
RemainAfterExit=yes
TimeoutStartSec=60

[Install]
WantedBy=graphical.target
"""
    
    try:
        subprocess.run(['sudo', 'tee', '/etc/systemd/system/displayport-autoswitch.service'], 
                      input=service_content.encode(), check=True, capture_output=True)
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        subprocess.run(['sudo', 'systemctl', 'enable', 'displayport-autoswitch.service'], check=True)
        print("✓ Boot service created and enabled")
    except subprocess.CalledProcessError as e:
        print(f"⚠ Warning: Failed to create boot service: {e}")
    
    print("\n✓ DisplayPort auto-switching setup completed")
    print("Features enabled:")
    print("  • Real-time hotplug detection via udev rules")
    print("  • Enhanced X server detection with multiple fallback methods")
    print("  • Boot-time display detection service")
    print("  • Detailed logging to /tmp/display-switch.log")
    print("\nTest by plugging/unplugging DisplayPort monitor")
    
    return True, ""

def setup_power_management():
    """Setup power management: screen off after 3 minutes, hibernate after 15 minutes"""
    xset_path = subprocess.run(['which', 'xset'], capture_output=True, text=True)
    if xset_path.returncode != 0:
        return False, "xset not installed (install x11-xserver-utils or xorg package)"
    
    # Step 1: Configure screen timeout with xset dpms
    print("Configuring screen timeout (3 minutes)...")
    xprofile_path = os.path.expanduser('~/.xprofile')
    xset_line = 'xset dpms 180 180 180'
    
    try:
        if os.path.exists(xprofile_path):
            with open(xprofile_path, 'r') as f:
                content = f.read()
            if xset_line not in content:
                with open(xprofile_path, 'a') as f:
                    f.write(f'\n# Screen power management - turn off after 3 minutes\n{xset_line}\n')
                print("✓ Screen timeout added to ~/.xprofile")
            else:
                print("✓ Screen timeout already configured in ~/.xprofile")
        else:
            with open(xprofile_path, 'w') as f:
                f.write(f'# Screen power management - turn off after 3 minutes\n{xset_line}\n')
            print("✓ Created ~/.xprofile with screen timeout")
    except Exception as e:
        return False, f"Failed to configure screen timeout: {e}"
    
    # Step 2: Configure system hibernate after 15 minutes
    print("Configuring system hibernate (15 minutes)...")
    logind_config = '/etc/systemd/logind.conf'
    
    try:
        # Read current logind.conf
        if os.path.exists(logind_config):
            with open(logind_config, 'r') as f:
                lines = f.readlines()
        else:
            return False, f"systemd logind config not found at {logind_config}"
        
        # Modify the configuration
        modified_lines = []
        idle_action_set = False
        idle_action_sec_set = False
        
        for line in lines:
            # Handle IdleAction
            if line.strip().startswith('#IdleAction=') or line.strip().startswith('IdleAction='):
                modified_lines.append('IdleAction=hibernate\n')
                idle_action_set = True
            # Handle IdleActionSec
            elif line.strip().startswith('#IdleActionSec=') or line.strip().startswith('IdleActionSec='):
                modified_lines.append('IdleActionSec=15min\n')
                idle_action_sec_set = True
            else:
                modified_lines.append(line)
        
        # Add settings if not found
        if not idle_action_set:
            modified_lines.append('IdleAction=hibernate\n')
        if not idle_action_sec_set:
            modified_lines.append('IdleActionSec=15min\n')
        
        # Write back to file (requires sudo)
        temp_config = '/tmp/logind.conf.tmp'
        with open(temp_config, 'w') as f:
            f.writelines(modified_lines)
        
        subprocess.run(['sudo', 'cp', temp_config, logind_config], check=True)
        subprocess.run(['rm', temp_config], check=True)
        print("✓ System hibernate configured in logind.conf")
        
    except subprocess.CalledProcessError as e:
        return False, f"Failed to configure system hibernate: {e}"
    except Exception as e:
        return False, f"Failed to configure system hibernate: {e}"
    
    # Step 3: Restart systemd-logind service
    print("Restarting systemd-logind service...")
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'systemd-logind'], check=True)
        print("✓ systemd-logind service restarted")
    except subprocess.CalledProcessError as e:
        return False, f"Failed to restart systemd-logind: {e}"
    
    # Step 4: Apply screen settings immediately
    print("Applying screen timeout settings immediately...")
    try:
        subprocess.run(['xset', 'dpms', '180', '180', '180'], check=True)
        print("✓ Screen timeout applied to current session")
    except subprocess.CalledProcessError as e:
        print(f"⚠ Warning: Failed to apply screen timeout to current session: {e}")
    
    print("\n✓ Power management setup completed!")
    print("Configuration:")
    print("  • Screen turns off after 3 minutes of inactivity")
    print("  • System hibernates after 15 minutes of inactivity")
    print("\nNote: Screen timeout will be active after next login/restart")
    
    return True, ""

def show_main_menu():
    """Display main menu and get user choice"""
    print("\n" + "="*50)
    print("DEBIAN PACKAGE INSTALLER")
    print("="*50)
    print("[1] Install Packages")
    print("[2] Settings")
    print("[q] Quit")
    print("="*50)
    
    choice = input("Enter your choice (1, 2, or q): ").strip()
    return choice

def show_package_menu():
    """Display package installation menu and get user choice"""
    print("\n" + "="*40)
    print("PACKAGE INSTALLATION")
    print("="*40)
    print("[0] Install basic development packages")
    print("[1] Install DWM dependencies and compile suckless programs")
    print("[2] Install Emacs from source")
    print("[3] Install GNU Stow from source")
    print("[4] Install basic utilities")
    print("[5] Install external packages")
    print("[b] Back to main menu")
    print("="*40)
    
    choice = input("Enter your choice (e.g., 0,3,5, 'all', or 'b'): ").strip()
    return choice

def show_external_packages_menu():
    """Display external packages menu and get user choice"""
    print("\n" + "="*40)
    print("EXTERNAL PACKAGES")
    print("="*40)
    print("[1] Install bluetuith (TUI bluetooth manager)")
    print("[2] Install ncpamixer (ncurses PulseAudio mixer)")
    print("[b] Back to package menu")
    print("="*40)
    
    choice = input("Enter your choice (1, 2, 'all', or 'b'): ").strip()
    return choice

def show_settings_menu():
    """Display settings menu with status indicators"""
    emacs_status = check_emacs_server_status()
    firefox_status = check_firefox_private_status()
    displayport_status = check_displayport_status()
    power_status = check_power_management_status()
    
    print("\n" + "="*60)
    print("SETTINGS")
    print("="*60)
    print(f"[1] Setup Emacs server as systemctl service [{emacs_status}]")
    print(f"[2] Create Firefox private dmenu item [{firefox_status}]")
    print(f"[3] Setup DisplayPort auto-switching [{displayport_status}]")
    print(f"[4] Setup Power Management (screen 3min/hibernate 15min) [{power_status}]")
    print("[all] Run all settings")
    print("[b] Back to main menu")
    print("="*60)
    print("Status: [O] Installed, [X] Not installed, [N] Not available")
    print("="*60)
    
    choice = input("Enter your choice (1, 2, 3, 4, 'all', or 'b'): ").strip()
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
    
    # Package installation function mapping
    package_functions = {
        '0': lambda packages: install_basic_packages(packages),
        '1': lambda packages: install_dwm_dependencies(packages),
        '2': lambda packages: install_emacs(packages),
        '3': lambda packages: install_stow(),
        '4': lambda packages: install_utils(packages),
        '5': lambda packages: handle_external_packages()
    }
    
    def handle_external_packages():
        """Handle external packages installation menu"""
        external_functions = {
            '1': lambda: install_bluetuith(),
            '2': lambda: install_ncpamixer()
        }
        
        while True:
            choice = show_external_packages_menu()
            
            if choice.lower() == 'b':
                return "BACK", ""  # Signal back navigation
            elif choice.lower() == 'all':
                selected = ['1', '2']
            else:
                selected = [x.strip() for x in choice.split(',')]
            
            for selection in selected:
                if selection in external_functions:
                    print(f"\n--- Installing external package {selection} ---")
                    success, error = external_functions[selection]()
                    if success:
                        print(f"✓ External package {selection} completed successfully")
                    else:
                        print(f"✗ External package {selection} failed: {error}")
                        break
                else:
                    print(f"Invalid option: {selection}")
            
            continue_choice = input("\nDo you want to install more external packages? (y/n): ").strip().lower()
            if continue_choice != 'y':
                break
        
        return True, ""
    
    # Settings function mapping
    settings_functions = {
        '1': lambda: setup_emacs_server(),
        '2': lambda: setup_firefox_private(),
        '3': lambda: setup_displayport_switching(),
        '4': lambda: setup_power_management()
    }
    
    while True:
        main_choice = show_main_menu()
        
        if main_choice.lower() == 'q':
            print("\nExiting...")
            break
        elif main_choice == '1':
            # Package installation menu
            while True:
                choice = show_package_menu()
                
                if choice.lower() == 'b':
                    break  # Go back to main menu
                elif choice.lower() == 'all':
                    selected = ['0', '1', '2', '3', '4', '5']
                else:
                    selected = [x.strip() for x in choice.split(',')]
                
                # Process selections
                any_failed = False
                for selection in selected:
                    if selection in package_functions:
                        print(f"\n--- Executing option {selection} ---")
                        success, error = package_functions[selection](packages)
                        if success == "BACK":
                            # User chose back in external packages menu
                            continue
                        elif success:
                            print(f"✓ Option {selection} completed successfully")
                        else:
                            print(f"✗ Option {selection} failed: {error}")
                            any_failed = True
                    else:
                        print(f"Invalid option: {selection}")
                        any_failed = True
                
                # Only ask to continue if there were errors or user wants to do more
                if any_failed:
                    continue_choice = input("\nContinue despite errors? (y/n): ").strip().lower()
                    if continue_choice != 'y':
                        break
                else:
                    input("\nPress Enter to continue...")
                    
        elif main_choice == '2':
            # Settings menu
            while True:
                choice = show_settings_menu()
                
                if choice.lower() == 'b':
                    break  # Go back to main menu
                elif choice.lower() == 'all':
                    selected = ['1', '2', '3', '4']
                elif choice in settings_functions:
                    selected = [choice]
                else:
                    print(f"Invalid option: {choice}")
                    continue
                
                # Process settings selections
                any_failed = False
                for selection in selected:
                    if selection in settings_functions:
                        print(f"\n--- Executing setting {selection} ---")
                        success, error = settings_functions[selection]()
                        if success:
                            print(f"✓ Setting {selection} completed successfully")
                        else:
                            print(f"✗ Setting {selection} failed: {error}")
                            any_failed = True
                    else:
                        print(f"Invalid option: {selection}")
                        any_failed = True
                
                # Only ask to continue if there were errors
                if any_failed:
                    continue_choice = input("\nContinue despite errors? (y/n): ").strip().lower()
                    if continue_choice != 'y':
                        break
                else:
                    input("\nPress Enter to continue...")
        else:
            print("Invalid option. Please choose 1, 2, or q.")

if __name__ == "__main__":
    main()
