import subprocess
import os
import sys

def install_requirements():
    try:
        # Get the directory where this script is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Path to requirements.txt
        requirements_path = os.path.join(current_dir, 'requirements.txt')
        
        # Install requirements
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_path])
        
        print("Successfully installed AetherOnePySocial plugin dependencies")
        return True
    except Exception as e:
        print(f"Error installing requirements: {str(e)}")
        return False

if __name__ == '__main__':
    install_requirements() 