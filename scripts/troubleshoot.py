#!/usr/bin/env python3
"""
Troubleshooting helper for Weather DSS System
"""

import os
import sys
import subprocess
import json
from datetime import datetime

class TroubleshootHelper:
    def __init__(self):
        self.issues_found = []
    
    def check_environment_variables(self):
        """Check required environment variables"""
        print("🔍 Checking environment variables...")
        
        required_vars = [
            'OPENWEATHER_API_KEY',
            'KAFKA_BOOTSTRAP_SERVERS',
            'MONGODB_HOST',
            'POSTGRES_HOST'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.issues_found.append({
                'issue': 'Missing Environment Variables',
                'details': missing_vars,
                'solution': 'Create .env file with required variables'
            })
            print(f"❌ Missing variables: {missing_vars}")
        else:
            print("✅ All required environment variables are set")
    
    def check_api_key_validity(self):
        """Check if API key is valid"""
        print("🔍 Checking API key validity...")
        
        try:
            import requests
            from dotenv import load_dotenv
            
            load_dotenv()
            api_key = os.getenv('OPENWEATHER_API_KEY')
            
            if not api_key:
                print("❌ No API key found")
                return
            
            # Test API call to Hanoi
            url = f"http://api.openweathermap.org/data/2.5/weather?lat=21.0285&lon=105.8542&appid={api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print("✅ API key is valid")
            elif response.status_code == 401:
                self.issues_found.append({
                    'issue': 'Invalid API Key',
                    'details': 'API key is invalid or expired',
                    'solution': 'Get a new API key from https://openweathermap.org/api'
                })
                print("❌ API key is invalid")
            else:
                print(f"⚠️  API response: {response.status_code}")
                
        except Exception as e:
            print(f"❌ API check failed: {e}")
    
    def check_docker_setup(self):
        """Check Docker setup"""
        print("🔍 Checking Docker setup...")
        
        try:
            # Check if Docker is installed
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                self.issues_found.append({
                    'issue': 'Docker Not Installed',
                    'details': 'Docker is not installed or not in PATH',
                    'solution': 'Install Docker from https://docker.com'
                })
                print("❌ Docker not found")
                return
            
            print(f"✅ Docker version: {result.stdout.strip()}")
            
            # Check if Docker daemon is running
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if result.returncode != 0:
                self.issues_found.append({
                    'issue': 'Docker Daemon Not Running',
                    'details': 'Docker daemon is not running',
                    'solution': 'Start Docker daemon/service'
                })
                print("❌ Docker daemon not running")
            else:
                print("✅ Docker daemon is running")
                
        except FileNotFoundError:
            self.issues_found.append({
                'issue': 'Docker Not Found',
                'details': 'Docker command not found',
                'solution': 'Install Docker and add to PATH'
            })
            print("❌ Docker not found")
    
    def check_python_packages(self):
        """Check required Python packages"""
        print("🔍 Checking Python packages...")
        
        required_packages = [
            'requests', 'kafka-python', 'python-dotenv', 
            'schedule', 'pymongo', 'psycopg2', 'flask'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                if package == 'kafka-python':
                    __import__('kafka')
                elif package == 'python-dotenv':
                    __import__('dotenv')
                elif package == 'psycopg2':
                    __import__('psycopg2')
                else:
                    __import__(package)
                print(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package}")
        
        if missing_packages:
            self.issues_found.append({
                'issue': 'Missing Python Packages',
                'details': missing_packages,
                'solution': f'pip install {" ".join(missing_packages)}'
            })
    
    def check_file_permissions(self):
        """Check file permissions"""
        print("🔍 Checking file permissions...")
        
        script_files = [
            'quick_start.sh',
            'setup_project.sh',
            'scripts/start_services.sh'
        ]
        
        for script in script_files:
            if os.path.exists(script):
                if os.access(script, os.X_OK):
                    print(f"✅ {script} is executable")
                else:
                    print(f"⚠️  {script} is not executable")
                    print(f"   Fix: chmod +x {script}")
            else:
                print(f"⚠️  {script} not found")
    
    def check_port_conflicts(self):
        """Check for port conflicts"""
        print("🔍 Checking port conflicts...")
        
        required_ports = {
            9092: 'Kafka',
            2181: 'Zookeeper', 
            27017: 'MongoDB',
            5432: 'PostgreSQL',
            5000: 'Dashboard',
            8080: 'Spark Master'
        }
        
        try:
            import socket
            
            for port, service in required_ports.items():
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    print(f"⚠️  Port {port} ({service}) is in use")
                else:
                    print(f"✅ Port {port} ({service}) is available")
                
                sock.close()
                
        except Exception as e:
            print(f"❌ Port check failed: {e}")
    
    def check_disk_space(self):
        """Check available disk space"""
        print("🔍 Checking disk space...")
        
        try:
            import shutil
            
            # Check current directory space
            total, used, free = shutil.disk_usage('.')
            free_gb = free // (1024**3)
            
            if free_gb < 5:
                self.issues_found.append({
                    'issue': 'Low Disk Space',
                    'details': f'Only {free_gb}GB free',
                    'solution': 'Free up disk space or use different location'
                })
                print(f"⚠️  Low disk space: {free_gb}GB free")
            else:
                print(f"✅ Disk space: {free_gb}GB free")
                
        except Exception as e:
            print(f"❌ Disk space check failed: {e}")
    
    def generate_solutions(self):
        """Generate solutions for found issues"""
        if not self.issues_found:
            print("\n🎉 No issues found! System looks good.")
            return
        
        print("\n🔧 ISSUES FOUND AND SOLUTIONS:")
        print("=" * 50)
        
        for i, issue in enumerate(self.issues_found, 1):
            print(f"\n{i}. {issue['issue']}")
            print(f"   Problem: {issue['details']}")
            print(f"   Solution: {issue['solution']}")
        
        # Generate quick fix script
        self.generate_quick_fix_script()
    
    def generate_quick_fix_script(self):
        """Generate a quick fix script"""
        print("\n📝 Generating quick fix script...")
        
        script_content = "#!/bin/bash\n"
        script_content += "echo '🔧 Weather DSS Quick Fix Script'\n\n"
        
        for issue in self.issues_found:
            if 'Missing Python Packages' in issue['issue']:
                packages = ' '.join(issue['details'])
                script_content += f"echo 'Installing missing Python packages...'\n"
                script_content += f"pip install {packages}\n\n"
            
            elif 'Docker' in issue['issue']:
                script_content += "echo 'Please install Docker manually from https://docker.com'\n\n"
            
            elif 'API Key' in issue['issue']:
                script_content += "echo 'Please update your API key in .env file'\n\n"
        
        script_content += "echo 'Quick fixes completed!'\n"
        
        with open('quick_fix.sh', 'w') as f:
            f.write(script_content)
        
        os.chmod('quick_fix.sh', 0o755)
        print("✅ Quick fix script created: quick_fix.sh")
    
    def run_troubleshoot(self):
        """Run complete troubleshooting"""
        print("🩺 Weather DSS Troubleshooting")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        checks = [
            self.check_environment_variables,
            self.check_api_key_validity,
            self.check_docker_setup,
            self.check_python_packages,
            self.check_file_permissions,
            self.check_port_conflicts,
            self.check_disk_space
        ]
        
        for check in checks:
            try:
                check()
                print()
            except Exception as e:
                print(f"❌ Check failed: {e}\n")
        
        self.generate_solutions()

def main():
    """Main function"""
    troubleshooter = TroubleshootHelper()
    troubleshooter.run_troubleshoot()

if __name__ == "__main__":
    main()