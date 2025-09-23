#!/usr/bin/env python3
"""
Comprehensive analysis of tkinter dependencies for safe removal.
"""

import os
import ast
import re
from pathlib import Path

def analyze_file_dependencies(file_path):
    """Analyze a Python file for tkinter and pygame dependencies."""
    
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse AST to find imports
        tree = ast.parse(content)
        
        imports = {
            'tkinter': [],
            'pygame': [],
            'display_manager': [],
            'pygame_display_manager': []
        }
        
        # Find import statements
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if 'tkinter' in alias.name:
                        imports['tkinter'].append(f"import {alias.name}")
                    elif 'pygame' in alias.name:
                        imports['pygame'].append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if 'tkinter' in node.module:
                        for alias in node.names:
                            imports['tkinter'].append(f"from {node.module} import {alias.name}")
                    elif 'pygame' in node.module:
                        for alias in node.names:
                            imports['pygame'].append(f"from {node.module} import {alias.name}")
                    elif node.module == 'display_manager':
                        for alias in node.names:
                            imports['display_manager'].append(f"from {node.module} import {alias.name}")
                    elif node.module == 'pygame_display_manager':
                        for alias in node.names:
                            imports['pygame_display_manager'].append(f"from {node.module} import {alias.name}")
        
        # Find string references to tkinter/pygame
        tkinter_refs = len(re.findall(r'tkinter|Tkinter', content, re.IGNORECASE))
        pygame_refs = len(re.findall(r'pygame', content, re.IGNORECASE))
        
        # Find method calls that might be tkinter-specific
        tkinter_methods = []
        pygame_methods = []
        
        # Look for common tkinter patterns
        tkinter_patterns = [
            r'\.after\(',
            r'\.mainloop\(',
            r'\.root\.',
            r'\.keysym',
            r'PhotoImage',
            r'\.withdraw\(',
            r'\.deiconify\('
        ]
        
        for pattern in tkinter_patterns:
            matches = re.findall(pattern, content)
            if matches:
                tkinter_methods.extend(matches)
        
        # Look for pygame patterns
        pygame_patterns = [
            r'pygame\.',
            r'\.get_ticks\(',
            r'\.flip\(',
            r'\.update\(',
            r'pygame\.event',
            r'pygame\.display'
        ]
        
        for pattern in pygame_patterns:
            matches = re.findall(pattern, content)
            if matches:
                pygame_methods.extend(matches)
        
        return {
            'file': file_path,
            'imports': imports,
            'tkinter_refs': tkinter_refs,
            'pygame_refs': pygame_refs,
            'tkinter_methods': tkinter_methods,
            'pygame_methods': pygame_methods,
            'size': len(content.split('\n'))
        }
        
    except Exception as e:
        return {'file': file_path, 'error': str(e)}

def find_cross_references():
    """Find which files reference display_manager vs pygame_display_manager."""
    
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', 'venv', 'slideshow_env']):
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    results = {}
    
    for file_path in python_files:
        analysis = analyze_file_dependencies(file_path)
        if analysis and 'error' not in analysis:
            results[file_path] = analysis
    
    return results

def generate_removal_plan(analysis_results):
    """Generate a safe removal plan based on analysis."""
    
    print("🎯 TKINTER REMOVAL SAFETY ANALYSIS")
    print("=" * 50)
    
    # Files that import tkinter
    tkinter_files = []
    # Files that import pygame  
    pygame_files = []
    # Files that import display_manager (tkinter version)
    display_mgr_files = []
    # Files that import pygame_display_manager
    pygame_mgr_files = []
    
    for file_path, data in analysis_results.items():
        if data.get('imports', {}).get('tkinter'):
            tkinter_files.append(file_path)
        if data.get('imports', {}).get('pygame'):
            pygame_files.append(file_path)
        if data.get('imports', {}).get('display_manager'):
            display_mgr_files.append(file_path)
        if data.get('imports', {}).get('pygame_display_manager'):
            pygame_mgr_files.append(file_path)
    
    print(f"\n📋 DIRECT TKINTER IMPORTS ({len(tkinter_files)} files):")
    for file_path in tkinter_files:
        data = analysis_results[file_path]
        print(f"  📄 {file_path}")
        for imp in data['imports']['tkinter']:
            print(f"    - {imp}")
        print(f"    📊 {data['tkinter_refs']} tkinter references, {len(data['tkinter_methods'])} method calls")
    
    print(f"\n📋 DISPLAY_MANAGER IMPORTS ({len(display_mgr_files)} files):")
    for file_path in display_mgr_files:
        data = analysis_results[file_path]
        print(f"  📄 {file_path}")
        for imp in data['imports']['display_manager']:
            print(f"    - {imp}")
    
    print(f"\n📋 PYGAME_DISPLAY_MANAGER IMPORTS ({len(pygame_mgr_files)} files):")
    for file_path in pygame_mgr_files:
        data = analysis_results[file_path]
        print(f"  📄 {file_path}")
        for imp in data['imports']['pygame_display_manager']:
            print(f"    - {imp}")
    
    print(f"\n🎮 PYGAME FILES ({len(pygame_files)} files):")
    for file_path in pygame_files:
        print(f"  📄 {file_path}")
    
    # Safety recommendations
    print(f"\n🛡️ SAFETY RECOMMENDATIONS:")
    
    if './display_manager.py' in analysis_results:
        dm_data = analysis_results['./display_manager.py']
        print(f"  📄 display_manager.py: {dm_data['size']} lines")
        print(f"    - ⚠️ CONTAINS TKINTER CODE - Safe to remove if no other files import it")
    
    if './main.py' in analysis_results:
        main_data = analysis_results['./main.py']
        print(f"  📄 main.py: {main_data['size']} lines")
        if main_data.get('imports', {}).get('display_manager'):
            print(f"    - ⚠️ IMPORTS display_manager - Safe to remove (tkinter version)")
        else:
            print(f"    - ✅ No display_manager import")
    
    if './main_pygame.py' in analysis_results:
        pygame_main_data = analysis_results['./main_pygame.py']
        print(f"  📄 main_pygame.py: {pygame_main_data['size']} lines")
        print(f"    - ✅ PYGAME VERSION - Keep this file")
    
    # Files that are safe to remove
    safe_to_remove = []
    must_keep = []
    
    for file_path in tkinter_files:
        if file_path == './display_manager.py':
            if not any('./display_manager' in str(data.get('imports', {}).get('display_manager', [])) 
                      for fp, data in analysis_results.items() if fp != file_path):
                safe_to_remove.append(file_path)
        elif file_path == './main.py':
            # Check if it's the tkinter version
            data = analysis_results[file_path]
            if data.get('imports', {}).get('display_manager'):
                safe_to_remove.append(file_path)
    
    for file_path in pygame_files:
        if 'main_pygame.py' in file_path or 'pygame_display_manager.py' in file_path:
            must_keep.append(file_path)
    
    print(f"\n✅ SAFE TO REMOVE ({len(safe_to_remove)} files):")
    for file_path in safe_to_remove:
        print(f"  📄 {file_path} - No dependencies found")
    
    print(f"\n🔒 MUST KEEP ({len(must_keep)} files):")
    for file_path in must_keep:
        print(f"  📄 {file_path} - Required for pygame functionality")
    
    return {
        'safe_to_remove': safe_to_remove,
        'must_keep': must_keep,
        'tkinter_files': tkinter_files,
        'pygame_files': pygame_files
    }

if __name__ == "__main__":
    print("🔍 Analyzing tkinter dependencies for safe removal...")
    
    # Analyze all Python files
    results = find_cross_references()
    
    # Generate removal plan
    plan = generate_removal_plan(results)
    
    print(f"\n🎯 REMOVAL PLAN SUMMARY:")
    print(f"  ✅ Safe to remove: {len(plan['safe_to_remove'])} files")
    print(f"  🔒 Must keep: {len(plan['must_keep'])} files")
    print(f"  ⚠️ Total tkinter files: {len(plan['tkinter_files'])} files")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"  1. Remove files marked as 'safe to remove'")
    print(f"  2. Update run_slideshow.sh to use main_pygame.py")
    print(f"  3. Test functionality after each removal")
    print(f"  4. Keep pygame files untouched")
