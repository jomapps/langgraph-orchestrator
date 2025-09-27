#!/usr/bin/env python3
"""
Basic test to verify brain service integration without external dependencies.
"""

import os
import sys
import urllib.request
import urllib.error
import json


def test_environment_variables():
    """Test that required environment variables are set"""
    print("Testing environment variables...")

    brain_service_url = os.getenv('BRAIN_SERVICE_BASE_URL', 'https://brain.ft.tc')
    print(f"BRAIN_SERVICE_BASE_URL: {brain_service_url}")

    # Check if Neo4j variables are removed
    neo4j_vars = ['NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD']
    neo4j_found = []

    for var in neo4j_vars:
        if os.getenv(var):
            neo4j_found.append(var)

    if neo4j_found:
        print(f"❌ Neo4j variables still present: {neo4j_found}")
        return False
    else:
        print("✅ Neo4j environment variables successfully removed")

    print("✅ Environment variables configured correctly")
    return True


def test_brain_service_reachability():
    """Test if brain service is reachable"""
    print("Testing brain service reachability...")

    brain_service_url = os.getenv('BRAIN_SERVICE_BASE_URL', 'https://brain.ft.tc')

    try:
        # Try to connect to the brain service
        req = urllib.request.Request(brain_service_url, method='GET')
        req.add_header('User-Agent', 'LangGraph-Orchestrator/1.0')

        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            print(f"✅ Brain service is reachable (HTTP {status_code})")
            return True

    except urllib.error.HTTPError as e:
        if e.code in [200, 404, 405]:  # Service exists but endpoint may not
            print(f"✅ Brain service is reachable (HTTP {e.code})")
            return True
        else:
            print(f"❌ Brain service HTTP error: {e.code}")
            return False
    except urllib.error.URLError as e:
        print(f"❌ Brain service not reachable: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Brain service connection failed: {str(e)}")
        return False


def test_file_modifications():
    """Test that configuration files have been properly modified"""
    print("Testing configuration file modifications...")

    files_to_check = [
        'coolify-env-variables.txt',
        '.env.local',
        '.env.production',
        '.coolify-with-neo4j.yml'
    ]

    all_clean = True

    for filename in files_to_check:
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    content = f.read()

                if 'NEO4J_URI' in content or 'NEO4J_USER' in content or 'NEO4J_PASSWORD' in content:
                    # Check if it's just a comment about removal
                    lines_with_neo4j = [line for line in content.split('\n')
                                       if 'NEO4J' in line and not line.strip().startswith('#')]
                    if lines_with_neo4j:
                        print(f"❌ {filename} still contains Neo4j configuration")
                        all_clean = False
                    else:
                        print(f"✅ {filename} Neo4j configuration properly removed/commented")
                else:
                    print(f"✅ {filename} clean of Neo4j configuration")
            except Exception as e:
                print(f"⚠️  Could not read {filename}: {str(e)}")
        else:
            print(f"ℹ️  {filename} not found (OK)")

    return all_clean


def test_brain_integration_files():
    """Test that brain integration files were created"""
    print("Testing brain integration files...")

    files_to_check = [
        ('src/clients/brain_client.py', 'Brain Client'),
        ('src/workflows/base_workflow.py', 'Base Workflow')
    ]

    all_present = True

    for filepath, description in files_to_check:
        if os.path.exists(filepath):
            print(f"✅ {description} created: {filepath}")

            # Check file content
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    if 'BrainServiceClient' in content or 'brain_client' in content:
                        print(f"   ✅ {description} contains brain service integration code")
                    else:
                        print(f"   ⚠️  {description} may not have complete integration")
            except Exception as e:
                print(f"   ⚠️  Could not verify {description} content: {str(e)}")
        else:
            print(f"❌ {description} not found: {filepath}")
            all_present = False

    return all_present


def main():
    """Run all tests"""
    print("🧠 Brain Service Integration Verification")
    print("=" * 50)

    tests = [
        ("Environment Variables", test_environment_variables),
        ("Configuration File Cleanup", test_file_modifications),
        ("Brain Integration Files", test_brain_integration_files),
        ("Brain Service Reachability", test_brain_service_reachability)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            success = test_func()
            if success:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {str(e)}")

    print(f"\n📊 Final Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 SUCCESS! Neo4j removal and brain service integration completed!")
        print("✅ All configuration files cleaned")
        print("✅ Brain service integration implemented")
        print("✅ Brain service is reachable")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed. Review the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)