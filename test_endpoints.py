import requests
import json
import subprocess
import sys

class CurlTester:
    def __init__(self):
        self.token = None
        self.base_url = "https://icapp-backend.onrender.com"
        # self.base_url = "http://localhost:5000"  # Use this for local testing
        
    def check_login(self):
        """Login and get token"""
        email = input("📧 Enter email: ")
        password = input("🔐 Enter password: ")
        
        your_curl_command = f'''curl -X POST {self.base_url}/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{{"email": "{email}", "password": "{password}"}}\''''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        
        try:
            result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
            response = result.stdout
            print(f"📤 Response: {response}")
            
            # Try to extract token
            try:
                data = json.loads(response)
                if 'token' in data:
                    self.token = data['token']
                    print(f"✅ Login successful! Token saved: {self.token[:20]}...")
                    return True
                else:
                    print("❌ Login failed - no token in response")
                    return False
            except json.JSONDecodeError:
                print("❌ Invalid JSON response")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def check_auth_me(self):
        """Test /api/auth/me endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        your_curl_command = f'''curl -X GET {self.base_url}/api/auth/me \
  -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_auth_profile(self):
        """Test /api/auth/profile endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        your_curl_command = f'''curl -X GET {self.base_url}/api/auth/profile \
  -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_projects_health(self):
        """Test /api/projects/health endpoint"""
        your_curl_command = f'''curl -X GET {self.base_url}/api/projects/health'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_projects_test(self):
        """Test /api/projects/test endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        your_curl_command = f'''curl -X GET {self.base_url}/api/projects/test \
  -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_projects_browse(self):
        """Test /api/projects/browse endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        your_curl_command = f'''curl -X GET "{self.base_url}/api/projects/browse?search=Machine&type=apprenticeship" \
  -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_projects_my(self):
        """Test /api/projects/my endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        your_curl_command = f'''curl -X GET {self.base_url}/api/projects/my \
  -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_projects_sponsored(self):
        """Test /api/projects/sponsored endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        your_curl_command = f'''curl -X GET {self.base_url}/api/projects/sponsored \
  -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_create_project(self):
        """Test POST /api/projects endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        # FILL IN YOUR CURL COMMAND HERE
        your_curl_command = f'''curl -X POST {self.base_url}/api/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {self.token}" \
  -d '{{
    "title": "Test Project from Curl Tester",
    "description": "Test description",
    "requirements": "Test requirements",
    "outcomes": "Test outcomes",
    "domains": ["AI", "ML"],
    "skills": ["Python", "TensorFlow"],
    "type": "apprenticeship",
    "browse": true,
    "open": true
  }}\''''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_update_project(self):
        """Test PUT /api/projects/<id> endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        project_id = input("🆔 Enter project ID to update: ")
        
        # FILL IN YOUR CURL COMMAND HERE
        your_curl_command = f'''curl -X PUT {self.base_url}/api/projects/{project_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {self.token}" \
  -d '{{
    "title": "Updated Test Project",
    "description": "Updated description"
  }}\''''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_delete_project(self):
        """Test DELETE /api/projects/<id> endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        project_id = input("🆔 Enter project ID to delete: ")
        
        # FILL IN YOUR CURL COMMAND HERE
        your_curl_command = f'''curl -X DELETE {self.base_url}/api/projects/{project_id} \
  -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_sponsor_project(self):
        """Test POST /api/projects/<id>/sponsor endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        project_id = input("🆔 Enter project ID to sponsor: ")
        
        # FILL IN YOUR CURL COMMAND HERE
        your_curl_command = f'''curl -X POST {self.base_url}/api/projects/{project_id}/sponsor \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {self.token}" \
  -d '{{
    "amount": 1000.0,
    "message": "Great project!"
  }}\''''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_update_sponsorship(self):
        """Test PUT /api/projects/<id>/sponsor endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        project_id = input("🆔 Enter project ID to update sponsorship: ")
        
        # FILL IN YOUR CURL COMMAND HERE
        your_curl_command = f'''curl -X PUT {self.base_url}/api/projects/{project_id}/sponsor \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {self.token}" \
  -d '{{
    "amount": 1500.0,
    "message": "Updated sponsorship amount"
  }}\''''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_remove_sponsorship(self):
        """Test DELETE /api/projects/<id>/sponsor endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        project_id = input("🆔 Enter project ID to remove sponsorship: ")
        
        # FILL IN YOUR CURL COMMAND HERE
        your_curl_command = f'''curl -X DELETE {self.base_url}/api/projects/{project_id}/sponsor \
  -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_company_details(self):
        """Test /api/sponsors/company endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        # FILL IN YOUR CURL COMMAND HERE
        your_curl_command = f'''curl -X GET {self.base_url}/api/sponsors/company \
  -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_logout(self):
        """Test /api/auth/logout endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        # FILL IN YOUR CURL COMMAND HERE
        your_curl_command = f'''curl -X POST {self.base_url}/api/auth/logout \
  -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")
        
        # Clear token after logout
        self.token = None
        print("🗑️ Token cleared")

    def check_company_details(self):
        """Test /api/sponsors/company endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        your_curl_command = f'''curl -X GET {self.base_url}/api/sponsors/company \
        -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_company_display_name(self):
        """Test /api/sponsors/company/display-name endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        your_curl_command = f'''curl -X GET {self.base_url}/api/sponsors/company/display-name \
        -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_company_logo(self):
        """Test /api/sponsors/company/logo endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        your_curl_command = f'''curl -X GET {self.base_url}/api/sponsors/company/logo \
        -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_company_website(self):
        """Test /api/sponsors/company/website endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        your_curl_command = f'''curl -X GET {self.base_url}/api/sponsors/company/website \
    -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_company_basic_info(self):
        """Test /api/sponsors/company/basic-info endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        your_curl_command = f'''curl -X GET {self.base_url}/api/sponsors/company/basic-info \
    -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_company_name_with_fallback(self):
        """Test /api/sponsors/company/name-with-fallback endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        your_curl_command = f'''curl -X GET {self.base_url}/api/sponsors/company/name-with-fallback \
    -H "Authorization: Bearer {self.token}"'''
        
        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_sponsor_dashboard(self):
        """Test sponsor dashboard endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return

        default_path = "/api/sponsors/dashboard"
        endpoint_path = input(f"🧭 Enter dashboard path [{default_path}]: ").strip() or default_path

        your_curl_command = f'''curl -X GET {self.base_url}{endpoint_path} \
    -H "Authorization: Bearer {self.token}"'''

        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_server_status(self):
        """Check if server is running"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Server is running! Response: {response.json()}")
                return True
            else:
                print(f"❌ Server responded with {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Server is not running! Please start it with: python app.py")
            return False
        except Exception as e:
            print(f"❌ Error checking server: {e}")
            return False



    def check_runtime_info(self):
        """Test /api/auth/internal/runtime-info endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return

        your_curl_command = f'''curl -X GET {self.base_url}/api/auth/internal/runtime-info \
  -H "Authorization: Bearer {self.token}"'''

        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")

    def check_projects_analytics_demo(self):
        """Test /api/projects/analytics-demo endpoint"""
        if not self.token:
            print("❌ Please login first!")
            return

        your_curl_command = f'''curl -X GET {self.base_url}/api/projects/analytics-demo \
  -H "Authorization: Bearer {self.token}"'''

        print(f"\n🔥 Executing: {your_curl_command}")
        result = subprocess.run(your_curl_command, shell=True, capture_output=True, text=True)
        print(f"📤 Response: {result.stdout}")







































def main():
    tester = CurlTester()
    
    # Menu options
    test_functions = {
        "1": ("Login", tester.check_login),
        "2": ("Auth - Me", tester.check_auth_me),
        "3": ("Auth - Profile", tester.check_auth_profile),
        "4": ("Projects - Health", tester.check_projects_health),
        "5": ("Projects - Test", tester.check_projects_test),
        "6": ("Projects - Browse", tester.check_projects_browse),
        "7": ("Projects - My Created", tester.check_projects_my),
        "8": ("Projects - My Sponsored", tester.check_projects_sponsored),
        "9": ("Create Project", tester.check_create_project),
        "10": ("Update Project", tester.check_update_project),
        "11": ("Delete Project", tester.check_delete_project),
        "12": ("Sponsor Project", tester.check_sponsor_project),
        "13": ("Update Sponsorship", tester.check_update_sponsorship),
        "14": ("Remove Sponsorship", tester.check_remove_sponsorship),
        "15": ("Company Details", tester.check_company_details),
        "16": ("Logout", tester.check_logout),
        "17": ("Company Logo", tester.check_company_logo),
        "18": ("Company Website", tester.check_company_website),
        "19": ("Company Basic Info", tester.check_company_basic_info),
        "20": ("Company Name with Fallback", tester.check_company_name_with_fallback),
        "21":("Company Display Name", tester.check_company_display_name),
        "22":("Company Details", tester.check_company_details),
        "23": ("logout", tester.check_logout),
        "24": ("Sponsor Dashboard", tester.check_sponsor_dashboard),
        "25": ("Runtime Info", tester.check_runtime_info),
        "26": ("Projects Analytics Demo", tester.check_projects_analytics_demo),
    }
    
    while True:
        print("\n" + "="*60)
        print("🚀 CURL COMMAND TESTER")
        print("="*60)
        
        # Show current token status
        if tester.token:
            print(f"🔑 Logged in - Token: {tester.token[:20]}...")
        else:
            print("🔑 Not logged in")
        
        print()
        
        # Show menu
        for key, (name, _) in test_functions.items():
            print(f"{key:2}. {name}")
        
        print("\nq.  Quit")
        
        choice = input("\n👉 Enter your choice: ").strip()
        
        if choice.lower() == 'q':
            print("👋 Goodbye!")
            break
        elif choice in test_functions:
            name, func = test_functions[choice]
            print(f"\n🧪 Testing: {name}")
            func()
            input("\n⏸️  Press Enter to continue...")
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()