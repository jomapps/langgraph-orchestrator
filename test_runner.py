#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for LangGraph Orchestrator

This script provides a unified interface to run all test categories with various options,
including parallel execution, coverage reporting, and detailed reporting.
"""

import argparse
import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import tempfile


class TestRunner:
    """Comprehensive test runner for the LangGraph Orchestrator project."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / "tests"
        self.results_dir = project_root / "test_results"
        self.coverage_dir = project_root / "coverage"
        self.results_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)
        
        # Test categories and their configurations
        self.test_categories = {
            "contract": {
                "path": "tests/contract",
                "markers": ["contract"],
                "description": "API contract tests",
                "parallel": False,  # Contract tests should run sequentially
                "timeout": 300
            },
            "integration": {
                "path": "tests/integration",
                "markers": ["integration"],
                "description": "Integration tests",
                "parallel": False,  # Integration tests should run sequentially
                "timeout": 600
            },
            "performance": {
                "path": "tests/performance",
                "markers": ["performance"],
                "description": "Performance tests",
                "parallel": False,  # Performance tests should run sequentially
                "timeout": 900
            },
            "unit": {
                "path": "tests/unit",
                "markers": ["unit"],
                "description": "Unit tests",
                "parallel": True,   # Unit tests can run in parallel
                "timeout": 300
            },
            "redis": {
                "path": "tests/redis",
                "markers": ["redis"],
                "description": "Redis-specific tests",
                "parallel": False,  # Redis tests should run sequentially
                "timeout": 300
            }
        }
    
    def run_command(self, cmd: List[str], timeout: int = 300, capture_output: bool = True) -> Dict[str, Any]:
        """Run a command and return results."""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "command": " ".join(cmd)
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": " ".join(cmd)
            }
    
    def build_pytest_command(self, category: str, options: Dict[str, Any]) -> List[str]:
        """Build pytest command for a specific test category."""
        config = self.test_categories[category]
        cmd = ["python", "-m", "pytest"]
        
        # Add test path
        cmd.append(config["path"])
        
        # Add markers
        if config["markers"]:
            marker_expr = " or ".join(config["markers"])
            cmd.extend(["-m", marker_expr])
        
        # Add output options
        cmd.extend([
            "-v",  # Verbose output
            "--tb=short",  # Short traceback
            "--strict-markers",  # Strict marker usage
        ])
        
        # Add coverage options if enabled
        if options.get("coverage", False):
            cmd.extend([
                f"--cov=src",
                f"--cov-report=html:{self.coverage_dir}/{category}",
                f"--cov-report=term-missing",
                f"--cov-branch"
            ])
        
        # Add parallel execution if enabled and supported
        if options.get("parallel", False) and config["parallel"]:
            cmd.extend(["-n", "auto"])
        
        # Add JUnit XML output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        xml_file = self.results_dir / f"{category}_results_{timestamp}.xml"
        cmd.extend(["--junitxml", str(xml_file)])
        
        # Add HTML report
        html_file = self.results_dir / f"{category}_report_{timestamp}.html"
        cmd.extend(["--html", str(html_file), "--self-contained-html"])
        
        return cmd
    
    def parse_junit_results(self, xml_file: Path) -> Dict[str, Any]:
        """Parse JUnit XML results file."""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            results = {
                "tests": int(root.get("tests", 0)),
                "failures": int(root.get("failures", 0)),
                "errors": int(root.get("errors", 0)),
                "skipped": int(root.get("skipped", 0)),
                "time": float(root.get("time", 0.0))
            }
            
            # Calculate success rate
            total_tests = results["tests"]
            failed_tests = results["failures"] + results["errors"]
            results["passed"] = total_tests - failed_tests - results["skipped"]
            results["success_rate"] = (results["passed"] / total_tests * 100) if total_tests > 0 else 0
            
            return results
        except Exception as e:
            return {
                "tests": 0,
                "failures": 0,
                "errors": 0,
                "skipped": 0,
                "passed": 0,
                "success_rate": 0,
                "time": 0.0,
                "error": str(e)
            }
    
    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive test summary report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
# LangGraph Orchestrator Test Suite Report
Generated: {timestamp}

## Summary
"""
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_time = 0
        
        for category, result in results.items():
            if result["success"]:
                junit_results = result.get("junit_results", {})
                tests = junit_results.get("tests", 0)
                passed = junit_results.get("passed", 0)
                failed = junit_results.get("failures", 0) + junit_results.get("errors", 0)
                time = junit_results.get("time", 0)
                success_rate = junit_results.get("success_rate", 0)
                
                total_tests += tests
                total_passed += passed
                total_failed += failed
                total_time += time
                
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                
                report += f"""
### {category.title()} Tests {status}
- Tests: {tests}
- Passed: {passed}
- Failed: {failed}
- Success Rate: {success_rate:.1f}%
- Execution Time: {time:.2f}s
"""
            else:
                report += f"""
### {category.title()} Tests ❌ FAIL
- Error: {result.get('error', 'Unknown error')}
"""
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        report += f"""
## Overall Results
- Total Tests: {total_tests}
- Total Passed: {total_passed}
- Total Failed: {total_failed}
- Overall Success Rate: {overall_success_rate:.1f}%
- Total Execution Time: {total_time:.2f}s

## Test Categories
"""
        
        for category, config in self.test_categories.items():
            report += f"- **{category.title()}**: {config['description']}\n"
        
        report += f"""
## Recommendations
"""
        
        if overall_success_rate < 80:
            report += "- 🚨 **CRITICAL**: Overall success rate is below 80%. Immediate attention required.\n"
        elif overall_success_rate < 90:
            report += "- ⚠️ **WARNING**: Overall success rate is below 90%. Review failing tests.\n"
        else:
            report += "- ✅ **GOOD**: Overall success rate is above 90%.\n"
        
        if total_failed > 0:
            report += f"- 🔍 **INVESTIGATE**: {total_failed} tests failed. Check detailed logs for root causes.\n"
        
        report += """
- 📊 **COVERAGE**: Consider running with --coverage flag for detailed coverage analysis
- 🔄 **REGRESSION**: Monitor test trends over time to catch regressions early
- ⚡ **PERFORMANCE**: Review performance test results for any degradation
"""
        
        return report
    
    def run_category_tests(self, category: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Run tests for a specific category."""
        config = self.test_categories[category]
        print(f"\n{'='*60}")
        print(f"Running {category.title()} Tests")
        print(f"Description: {config['description']}")
        print(f"Path: {config['path']}")
        print(f"Timeout: {config['timeout']}s")
        print(f"{'='*60}\n")
        
        # Build and run command
        cmd = self.build_pytest_command(category, options)
        result = self.run_command(cmd, timeout=config["timeout"])
        
        # Parse JUnit results if XML file was created
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        xml_file = self.results_dir / f"{category}_results_{timestamp}.xml"
        
        if xml_file.exists():
            result["junit_results"] = self.parse_junit_results(xml_file)
        
        # Print summary
        if result["success"]:
            print(f"✅ {category.title()} tests completed successfully")
            if "junit_results" in result:
                junit = result["junit_results"]
                print(f"   Tests: {junit.get('tests', 0)}, Passed: {junit.get('passed', 0)}, "
                      f"Failed: {junit.get('failures', 0) + junit.get('errors', 0)}")
        else:
            print(f"❌ {category.title()} tests failed")
            if result.get("stderr"):
                print(f"   Error: {result['stderr']}")
        
        return result
    
    def run_all_tests(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Run all test categories."""
        results = {}
        start_time = time.time()
        
        print("🚀 Starting comprehensive test suite execution")
        print(f"Project Root: {self.project_root}")
        print(f"Results Directory: {self.results_dir}")
        print(f"Coverage Directory: {self.coverage_dir}")
        print(f"Options: {json.dumps(options, indent=2)}\n")
        
        # Determine which categories to run
        categories_to_run = options.get("categories", list(self.test_categories.keys()))
        
        for category in categories_to_run:
            if category not in self.test_categories:
                print(f"⚠️  Unknown test category: {category}")
                continue
            
            results[category] = self.run_category_tests(category, options)
        
        total_time = time.time() - start_time
        
        # Generate summary report
        summary_report = self.generate_summary_report(results)
        summary_file = self.results_dir / f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(summary_file, "w") as f:
            f.write(summary_report)
        
        print(f"\n{'='*60}")
        print("Test Suite Execution Complete")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Summary Report: {summary_file}")
        print(f"{'='*60}")
        
        return {
            "results": results,
            "total_time": total_time,
            "summary_report": summary_report,
            "summary_file": str(summary_file)
        }
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available."""
        required_commands = ["python", "pytest", "redis-server"]
        missing = []
        
        for cmd in required_commands:
            result = self.run_command(["which", cmd], capture_output=True)
            if not result["success"]:
                missing.append(cmd)
        
        if missing:
            print(f"❌ Missing required dependencies: {', '.join(missing)}")
            print("Please install missing dependencies before running tests.")
            return False
        
        print("✅ All required dependencies are available")
        return True
    
    def check_redis_connection(self) -> bool:
        """Check if Redis server is running and accessible."""
        try:
            import redis
            client = redis.Redis(host="localhost", port=6379, decode_responses=True)
            result = client.ping()
            if result:
                print("✅ Redis server is running and accessible")
                return True
            else:
                print("❌ Redis server ping failed")
                return False
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            print("Please ensure Redis server is running on localhost:6379")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test suite runner for LangGraph Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python test_runner.py
  
  # Run specific categories
  python test_runner.py --categories unit contract
  
  # Run with coverage
  python test_runner.py --coverage
  
  # Run with parallel execution for supported categories
  python test_runner.py --parallel
  
  # Run specific categories with coverage
  python test_runner.py --categories unit integration --coverage
  
  # Quick test run (skip performance tests)
  python test_runner.py --categories unit contract integration
        """
    )
    
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["contract", "integration", "performance", "unit", "redis"],
        help="Test categories to run (default: all)"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage reports"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel execution for supported categories"
    )
    
    parser.add_argument(
        "--no-deps-check",
        action="store_true",
        help="Skip dependency checks"
    )
    
    parser.add_argument(
        "--no-redis-check",
        action="store_true",
        help="Skip Redis connection check"
    )
    
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner(args.project_root)
    
    # Check dependencies
    if not args.no_deps_check:
        if not runner.check_dependencies():
            sys.exit(1)
    
    # Check Redis connection
    if not args.no_redis_check:
        if not runner.check_redis_connection():
            print("\n⚠️  Redis check failed. Redis tests will be skipped.")
            if not args.categories:
                args.categories = ["unit", "contract", "integration", "performance"]
    
    # Build options
    options = {
        "coverage": args.coverage,
        "parallel": args.parallel,
        "categories": args.categories or list(runner.test_categories.keys())
    }
    
    # Run tests
    try:
        results = runner.run_all_tests(options)
        
        # Print summary
        print("\n" + "="*80)
        print("FINAL TEST SUITE SUMMARY")
        print("="*80)
        print(results["summary_report"])
        
        # Check overall success
        overall_success = all(
            result["success"] for result in results["results"].values()
        )
        
        sys.exit(0 if overall_success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()