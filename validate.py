#!/usr/bin/env python3
"""
AI Ambassador Platform - Production Readiness Validation

Automated validation of production readiness checklist items.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# ANSI colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

class ValidationCheck:
    """Represents a validation check"""
    def __init__(self, category: str, name: str, check_func, critical: bool = False):
        self.category = category
        self.name = name
        self.check_func = check_func
        self.critical = critical
        self.passed = False
        self.message = ""

class ProductionValidator:
    """Validates production readiness"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.checks = []
        self.results = {}

    def add_check(self, category: str, name: str, check_func, critical: bool = False):
        """Add a validation check"""
        check = ValidationCheck(category, name, check_func, critical)
        self.checks.append(check)

    def run_all_checks(self):
        """Run all validation checks"""
        print(f"\n{Colors.BLUE}{Colors.BOLD}AI Ambassador Platform - Production Readiness Validation{Colors.ENDC}\n")

        categories = {}
        for check in self.checks:
            if check.category not in categories:
                categories[check.category] = []
            categories[check.category].append(check)

        for category, checks in categories.items():
            print(f"\n{Colors.BOLD}{category}{Colors.ENDC}")
            print("=" * 60)

            passed = 0
            failed = 0

            for check in checks:
                try:
                    result, message = check.check_func()
                    check.passed = result
                    check.message = message

                    if result:
                        print(f"{Colors.GREEN}✓{Colors.ENDC} {check.name}")
                        passed += 1
                    else:
                        critical_marker = " (CRITICAL)" if check.critical else ""
                        color = Colors.RED if check.critical else Colors.YELLOW
                        print(f"{color}✗{Colors.ENDC} {check.name}{critical_marker}")
                        if message:
                            print(f"  → {message}")
                        failed += 1
                except Exception as e:
                    check.passed = False
                    check.message = str(e)
                    print(f"{Colors.RED}✗{Colors.ENDC} {check.name} (Error: {str(e)})")
                    failed += 1

            self.results[category] = {"passed": passed, "failed": failed, "total": len(checks)}

    def print_summary(self):
        """Print validation summary"""
        print(f"\n{Colors.BOLD}Validation Summary{Colors.ENDC}")
        print("=" * 60)

        total_passed = 0
        total_failed = 0
        critical_failed = 0

        for category, results in self.results.items():
            passed = results['passed']
            failed = results['failed']
            total = results['total']

            total_passed += passed
            total_failed += failed

            status_color = Colors.GREEN if failed == 0 else Colors.YELLOW
            print(f"{status_color}{category}: {passed}/{total} passed{Colors.ENDC}")

        # Check critical failures
        for check in self.checks:
            if check.critical and not check.passed:
                critical_failed += 1

        print(f"\n{Colors.BOLD}Overall:{Colors.ENDC}")
        total_checks = total_passed + total_failed
        score = int((total_passed / total_checks * 100)) if total_checks > 0 else 0

        print(f"Total checks: {total_checks}")
        print(f"Passed: {Colors.GREEN}{total_passed}{Colors.ENDC}")
        print(f"Failed: {Colors.RED}{total_failed}{Colors.ENDC}")

        if critical_failed > 0:
            print(f"Critical failures: {Colors.RED}{critical_failed}{Colors.ENDC}")

        print(f"\n{Colors.BOLD}Production Readiness Score: {score}/100{Colors.ENDC}")

        if score >= 90:
            print(f"{Colors.GREEN}✓ Production ready! 🚀{Colors.ENDC}")
            return 0
        elif score >= 80:
            print(f"{Colors.YELLOW}⚠ Almost there! Complete remaining critical items{Colors.ENDC}")
            return 1 if critical_failed > 0 else 0
        elif score >= 70:
            print(f"{Colors.YELLOW}⚠ Significant work needed, focus on Security and Monitoring{Colors.ENDC}")
            return 1
        else:
            print(f"{Colors.RED}✗ Not ready for production{Colors.ENDC}")
            return 1

# Validation check functions

def check_local_settings_exists():
    """Check if local.settings.json exists"""
    path = Path(__file__).parent / "Copilot-Agent-365-main" / "local.settings.json"
    if path.exists():
        return True, ""
    return False, "Run configure.py to generate local.settings.json"

def check_env_file_exists():
    """Check if .env file exists"""
    path = Path(__file__).parent / ".env"
    if path.exists():
        return True, ""
    return False, "Run configure.py to generate .env file"

def check_gitignore_has_secrets():
    """Check if .gitignore excludes secret files"""
    gitignore = Path(__file__).parent / ".gitignore"
    if not gitignore.exists():
        return False, ".gitignore not found"

    content = gitignore.read_text()
    required = ['local.settings.json', '.env', '*.key']

    missing = []
    for item in required:
        if item not in content:
            missing.append(item)

    if missing:
        return False, f"Add to .gitignore: {', '.join(missing)}"

    return True, ""

def check_python_version():
    """Check if Python 3.11 is available"""
    try:
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        if '3.11' in version:
            return True, version
        return False, f"Python 3.11 recommended (found: {version})"
    except:
        return False, "Python 3 not found"

def check_azure_cli():
    """Check if Azure CLI is installed"""
    try:
        result = subprocess.run(['az', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            return True, "Azure CLI installed"
        return False, "Azure CLI not responding"
    except:
        return False, "Install from https://docs.microsoft.com/cli/azure/install-azure-cli"

def check_function_core_tools():
    """Check if Azure Functions Core Tools is installed"""
    try:
        result = subprocess.run(['func', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            return True, f"Version: {result.stdout.strip()}"
        return False, "func command not responding"
    except:
        return False, "Install from https://docs.microsoft.com/azure/azure-functions/functions-run-local"

def check_documentation_files():
    """Check if key documentation files exist"""
    required_docs = [
        'README.md',
        'DEPLOYMENT_GUIDE.md',
        'PRODUCTION_CHECKLIST.md',
        'COST_OPTIMIZATION.md',
        'SCALING_GUIDE.md'
    ]

    missing = []
    for doc in required_docs:
        if not (Path(__file__).parent / doc).exists():
            missing.append(doc)

    if missing:
        return False, f"Missing: {', '.join(missing)}"

    return True, ""

def check_infrastructure_files():
    """Check if infrastructure files exist"""
    infra_dir = Path(__file__).parent / "infrastructure"

    if not infra_dir.exists():
        return False, "infrastructure/ directory not found"

    required = [
        'infrastructure/bicep',
        'infrastructure/parameters',
    ]

    missing = []
    for item in required:
        if not (Path(__file__).parent / item).exists():
            missing.append(item)

    if missing:
        return False, f"Missing: {', '.join(missing)}"

    return True, ""

def check_deployment_script():
    """Check if deployment script exists and is executable"""
    script = Path(__file__).parent / "scripts" / "deploy-to-azure.sh"

    if not script.exists():
        return False, "scripts/deploy-to-azure.sh not found"

    if not os.access(script, os.X_OK):
        return False, "Make executable: chmod +x scripts/deploy-to-azure.sh"

    return True, ""

def check_examples_directory():
    """Check if examples directory exists"""
    examples = Path(__file__).parent / "examples"

    if not examples.exists():
        return False, "examples/ directory not found"

    return True, ""

def check_cli_tool():
    """Check if CLI tool exists and is executable"""
    cli = Path(__file__).parent / "cli.py"

    if not cli.exists():
        return False, "cli.py not found"

    if not os.access(cli, os.X_OK):
        return False, "Make executable: chmod +x cli.py"

    return True, ""

def main():
    """Main validation entry point"""
    validator = ProductionValidator()

    # Security checks
    validator.add_check("Security", "local.settings.json not in git", check_gitignore_has_secrets, critical=True)

    # Configuration checks
    validator.add_check("Configuration", "local.settings.json exists", check_local_settings_exists, critical=True)
    validator.add_check("Configuration", ".env file exists", check_env_file_exists, critical=True)

    # Prerequisites checks
    validator.add_check("Prerequisites", "Python 3.11 available", check_python_version)
    validator.add_check("Prerequisites", "Azure CLI installed", check_azure_cli, critical=True)
    validator.add_check("Prerequisites", "Azure Functions Core Tools installed", check_function_core_tools)

    # Documentation checks
    validator.add_check("Documentation", "Key documentation files exist", check_documentation_files)

    # Infrastructure checks
    validator.add_check("Infrastructure", "Infrastructure files exist", check_infrastructure_files)
    validator.add_check("Infrastructure", "Deployment script ready", check_deployment_script)

    # Tools checks
    validator.add_check("Tools", "CLI tool ready", check_cli_tool)
    validator.add_check("Tools", "Examples directory exists", check_examples_directory)

    # Run all checks
    validator.run_all_checks()

    # Print summary
    return validator.print_summary()

if __name__ == "__main__":
    sys.exit(main())
