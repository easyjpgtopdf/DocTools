#!/usr/bin/env python3
"""
Deep Copyright Audit for AdSense & Legal Compliance
Comprehensive check for all potential copyright, legal, and AdSense policy issues
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Competitor/trademark names to check
COMPETITOR_NAMES = [
    'remove.bg', 'removebg', 'rembg', 'photopea', 'canva', 'photoshop', 'adobe',
    'unsplash', 'pixabay', 'pexels', 'shutterstock', 'getty', 'istock',
    'pdf24', 'ilovepdf', 'smallpdf', 'pdf2go', 'hipdf', 'pdfmerge', 'pdfsam',
    'online-pdf', 'pdfcandy', 'pdfescape', 'adobe acrobat'
]

# Third-party services requiring attribution
THIRD_PARTY_SERVICES = [
    'firebase', 'google', 'font awesome', 'jspdf', 'pdf.js', 'pdf-lib', 'mammoth',
    'tesseract', 'html2canvas', 'bootstrap', 'jquery', 'axios', 'chart.js',
    'webpack', 'babel', 'react', 'vue', 'angular', 'express', 'node.js'
]

# Copyright/trademark keywords
COPYRIGHT_KEYWORDS = [
    'copyright', '©', 'all rights reserved', 'proprietary', 'trademark', '®', 'TM',
    'patent', 'licensed', 'license', 'mit', 'gpl', 'apache', 'bsd'
]

# Legal disclaimer keywords
LEGAL_KEYWORDS = [
    'educational purposes', 'fair use', 'demo', 'example', 'sample', 'for reference',
    'not affiliated', 'no warranty', 'as-is', 'disclaimer'
]

# Potentially problematic content
PROBLEMATIC_PATTERNS = [
    r'copied from',
    r'taken from',
    r'stolen from',
    r'ripped off',
    r'plagiarized',
    r'credit.*original',
    r'original.*found at',
    r'source.*http',
]

# Files to exclude from audit
EXCLUDE_PATTERNS = [
    'node_modules', '__pycache__', '.git', 'venv', '.venv', 'dist', 'build',
    'backups', 'server/node_modules', 'bg-remover-backend/venv',
    'image-repair-backend/venv', 'excel-unlocker/venv'
]

# Extensions to check
CHECK_EXTENSIONS = ['.html', '.js', '.css', '.py', '.md', '.txt', '.json']

class CopyrightAuditor:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.issues = defaultdict(list)
        self.files_checked = 0
        self.total_files = 0
        
    def should_exclude(self, file_path):
        """Check if file should be excluded"""
        path_str = str(file_path)
        return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)
    
    def should_check(self, file_path):
        """Check if file extension should be audited"""
        return file_path.suffix.lower() in CHECK_EXTENSIONS
    
    def count_files(self):
        """Count total files to check"""
        for file_path in self.root_dir.rglob('*'):
            if file_path.is_file() and not self.should_exclude(file_path) and self.should_check(file_path):
                self.total_files += 1
    
    def check_competitor_references(self, content, file_path):
        """Check for competitor/trademark references"""
        issues = []
        content_lower = content.lower()
        
        for competitor in COMPETITOR_NAMES:
            pattern = re.compile(r'\b' + re.escape(competitor) + r'\b', re.IGNORECASE)
            matches = pattern.findall(content)
            
            if matches:
                # Check if it's in a comment (less problematic) or code/text
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if competitor.lower() in line.lower():
                        # Check if it's a comment
                        is_comment = False
                        if file_path.suffix in ['.js', '.py']:
                            is_comment = '//' in line or '#' in line
                        elif file_path.suffix == '.html':
                            is_comment = '<!--' in line or line.strip().startswith('//')
                        elif file_path.suffix == '.css':
                            is_comment = '/*' in line or '//' in line
                        
                        if not is_comment:
                            issues.append({
                                'type': 'competitor_reference',
                                'competitor': competitor,
                                'line': i,
                                'context': line.strip()[:100],
                                'severity': 'medium' if 'like' in line.lower() or 'similar' in line.lower() else 'high'
                            })
        
        return issues
    
    def check_missing_attributions(self, content, file_path):
        """Check for third-party services without proper attribution"""
        issues = []
        content_lower = content.lower()
        footer_found = 'footer' in content_lower or 'attribution' in content_lower
        
        services_found = []
        for service in THIRD_PARTY_SERVICES:
            pattern = re.compile(r'\b' + re.escape(service) + r'\b', re.IGNORECASE)
            if pattern.search(content):
                services_found.append(service)
        
        # Check if services are mentioned in footer/attributions
        if services_found and not footer_found:
            if file_path.name not in ['attributions.html', 'index.html']:
                # Check if attributions exist elsewhere
                attributions_mentioned = any(
                    service in content_lower and 'thanks' in content_lower or 'attribution' in content_lower
                    for service in services_found
                )
                
                if not attributions_mentioned:
                    issues.append({
                        'type': 'missing_attribution',
                        'services': services_found,
                        'severity': 'medium'
                    })
        
        return issues
    
    def check_copyright_notices(self, content, file_path):
        """Check for copyright notices"""
        issues = []
        content_lower = content.lower()
        
        # Check for copyright symbol or text
        has_copyright = '©' in content or 'copyright' in content_lower
        
        if not has_copyright:
            # Main pages should have copyright
            if file_path.name in ['index.html'] or file_path.name.endswith('.html'):
                if 'footer' not in content_lower:
                    issues.append({
                        'type': 'missing_copyright',
                        'severity': 'low'
                    })
        else:
            # Check if copyright is consistent
            copyright_matches = re.findall(r'(?:©|copyright|copyright\s*©)\s*(\d{4}[^\s]*|\w+[^\s]*)', content, re.IGNORECASE)
            if copyright_matches:
                issues.append({
                    'type': 'copyright_found',
                    'copyright': copyright_matches[0],
                    'severity': 'info'
                })
        
        return issues
    
    def check_problematic_patterns(self, content, file_path):
        """Check for problematic patterns"""
        issues = []
        
        for pattern in PROBLEMATIC_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append({
                            'type': 'problematic_pattern',
                            'pattern': pattern,
                            'line': i,
                            'context': line.strip()[:100],
                            'severity': 'high'
                        })
        
        return issues
    
    def check_license_compliance(self, file_path):
        """Check for license files"""
        issues = []
        
        # Check if LICENSE file exists
        license_files = list(self.root_dir.glob('LICENSE*')) + list(self.root_dir.glob('license*'))
        
        if not license_files:
            issues.append({
                'type': 'missing_license_file',
                'severity': 'medium'
            })
        
        # Check package.json for license
        package_json = self.root_dir / 'package.json'
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    if 'license' not in package_data:
                        issues.append({
                            'type': 'missing_package_license',
                            'severity': 'low'
                        })
            except:
                pass
        
        return issues
    
    def check_legal_disclaimers(self, content, file_path):
        """Check for legal disclaimers"""
        issues = []
        content_lower = content.lower()
        
        # Check for problematic disclaimers
        problematic_disclaimers = [
            'educational purposes only',
            'for demonstration only',
            'not for commercial use'
        ]
        
        for disclaimer in problematic_disclaimers:
            if disclaimer in content_lower:
                issues.append({
                    'type': 'problematic_disclaimer',
                    'disclaimer': disclaimer,
                    'severity': 'high',
                    'note': 'May affect AdSense approval'
                })
        
        return issues
    
    def audit_file(self, file_path):
        """Audit a single file"""
        try:
            # Try UTF-8 first
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try other encodings
                for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            content = f.read()
                        break
                    except:
                        continue
                else:
                    return  # Skip file if can't read
            
            relative_path = file_path.relative_to(self.root_dir)
            file_issues = []
            
            # Run all checks
            file_issues.extend(self.check_competitor_references(content, file_path))
            file_issues.extend(self.check_missing_attributions(content, file_path))
            file_issues.extend(self.check_copyright_notices(content, file_path))
            file_issues.extend(self.check_problematic_patterns(content, file_path))
            file_issues.extend(self.check_legal_disclaimers(content, file_path))
            
            if file_issues:
                self.issues[str(relative_path)] = file_issues
            
            self.files_checked += 1
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    def audit_all(self):
        """Audit all files"""
        print("🔍 Deep Copyright Audit Starting...\n")
        print("="*80)
        
        # Count files first
        print("📊 Counting files to audit...")
        self.count_files()
        print(f"   Found {self.total_files} files to check\n")
        
        # Audit files
        print("🔎 Auditing files...")
        for file_path in self.root_dir.rglob('*'):
            if file_path.is_file() and not self.should_exclude(file_path) and self.should_check(file_path):
                self.audit_file(file_path)
                
                if self.files_checked % 50 == 0:
                    print(f"   Checked {self.files_checked}/{self.total_files} files...")
        
        # Check license compliance
        print("\n📄 Checking license compliance...")
        license_issues = self.check_license_compliance(self.root_dir)
        if license_issues:
            self.issues['LICENSE_CHECK'] = license_issues
        
        print(f"\n✅ Audit complete! Checked {self.files_checked} files")
        print("="*80)
    
    def generate_report(self):
        """Generate comprehensive report"""
        report = []
        report.append("# DEEP COPYRIGHT AUDIT REPORT")
        report.append("=" * 80)
        report.append(f"\nDate: {Path(__file__).stat().st_mtime}")
        report.append(f"Files Checked: {self.files_checked}")
        report.append(f"Issues Found: {sum(len(issues) for issues in self.issues.values())}\n")
        
        # Group issues by type
        by_type = defaultdict(list)
        by_severity = defaultdict(list)
        
        for file_path, issues in self.issues.items():
            for issue in issues:
                by_type[issue['type']].append((file_path, issue))
                by_severity[issue['severity']].append((file_path, issue))
        
        # Summary
        report.append("## SUMMARY")
        report.append("-" * 80)
        report.append(f"\n**High Severity Issues:** {len(by_severity['high'])}")
        report.append(f"**Medium Severity Issues:** {len(by_severity['medium'])}")
        report.append(f"**Low Severity Issues:** {len(by_severity['low'])}")
        report.append(f"**Info:** {len(by_severity['info'])}\n")
        
        # High severity issues
        if by_severity['high']:
            report.append("\n## 🔴 HIGH SEVERITY ISSUES (Must Fix)")
            report.append("-" * 80)
            for file_path, issue in by_severity['high']:
                report.append(f"\n**File:** `{file_path}`")
                report.append(f"**Type:** {issue['type']}")
                if 'line' in issue:
                    report.append(f"**Line:** {issue['line']}")
                if 'context' in issue:
                    report.append(f"**Context:** `{issue['context']}`")
                if 'note' in issue:
                    report.append(f"**Note:** {issue['note']}")
                report.append("")
        
        # Medium severity issues
        if by_severity['medium']:
            report.append("\n## 🟡 MEDIUM SEVERITY ISSUES (Should Fix)")
            report.append("-" * 80)
            for file_path, issue in by_severity['medium']:
                report.append(f"\n**File:** `{file_path}`")
                report.append(f"**Type:** {issue['type']}")
                if 'competitor' in issue:
                    report.append(f"**Competitor:** {issue['competitor']}")
                if 'services' in issue:
                    report.append(f"**Services:** {', '.join(issue['services'])}")
                if 'line' in issue:
                    report.append(f"**Line:** {issue['line']}")
                report.append("")
        
        # Competitor references summary
        competitor_refs = [item for item in by_severity['high'] + by_severity['medium'] 
                          if item[1]['type'] == 'competitor_reference']
        
        if competitor_refs:
            report.append("\n## 🏢 COMPETITOR REFERENCES FOUND")
            report.append("-" * 80)
            by_competitor = defaultdict(list)
            for file_path, issue in competitor_refs:
                by_competitor[issue['competitor']].append((file_path, issue))
            
            for competitor, refs in sorted(by_competitor.items()):
                report.append(f"\n**{competitor.title()}:** {len(refs)} references")
                for file_path, issue in refs[:5]:  # Show first 5
                    report.append(f"  - `{file_path}` (line {issue.get('line', 'N/A')})")
                if len(refs) > 5:
                    report.append(f"  ... and {len(refs) - 5} more")
        
        # Recommendations
        report.append("\n## 📋 RECOMMENDATIONS")
        report.append("-" * 80)
        
        if by_severity['high']:
            report.append("\n1. **IMMEDIATE ACTION REQUIRED:**")
            report.append("   - Remove all competitor references from code")
            report.append("   - Remove problematic disclaimers (educational purposes, etc.)")
            report.append("   - Remove any copied/plagiarized content")
        
        if by_severity['medium']:
            report.append("\n2. **IMPORTANT:**")
            report.append("   - Add proper attributions for all third-party services")
            report.append("   - Ensure consistent copyright notices across all pages")
            report.append("   - Add LICENSE file if using open-source code")
        
        report.append("\n3. **ADVICE FOR ADSENSE APPROVAL:**")
        report.append("   - Remove ALL competitor names from comments and code")
        report.append("   - Ensure unique, original content")
        report.append("   - Add proper copyright notices")
        report.append("   - Include comprehensive attributions page")
        report.append("   - Add privacy policy and terms of service")
        
        report.append("\n4. **LEGAL PROTECTION:**")
        report.append("   - Ensure all third-party libraries are properly licensed")
        report.append("   - Add DMCA policy")
        report.append("   - Include proper disclaimers (NOT 'educational purposes')")
        report.append("   - Ensure no trademark violations")
        
        return "\n".join(report)

def main():
    """Main function"""
    root_dir = Path(__file__).parent
    auditor = CopyrightAuditor(root_dir)
    
    auditor.audit_all()
    
    # Generate report
    report = auditor.generate_report()
    
    # Save report
    report_file = root_dir / 'DEEP_COPYRIGHT_AUDIT_REPORT.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n" + "="*80)
    print("📄 REPORT GENERATED")
    print("="*80)
    print(f"\n✅ Report saved to: {report_file}")
    print(f"\n📊 Total Issues Found: {sum(len(issues) for issues in auditor.issues.values())}")
    
    # Print summary
    high = sum(1 for issues in auditor.issues.values() 
               for issue in issues if issue.get('severity') == 'high')
    medium = sum(1 for issues in auditor.issues.values() 
                 for issue in issues if issue.get('severity') == 'medium')
    
    if high > 0:
        print(f"\n🔴 HIGH SEVERITY: {high} issues - MUST FIX!")
    if medium > 0:
        print(f"🟡 MEDIUM SEVERITY: {medium} issues - Should fix")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()

