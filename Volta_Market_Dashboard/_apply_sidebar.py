#!/usr/bin/env python3
"""
Script to apply the standardized collapsible sidebar to all admin dashboard pages.
Excludes login, password reset, and error pages.
"""

import os
import re
from pathlib import Path

# Files to exclude from sidebar application
EXCLUDED_FILES = [
    'admin_login_page.html',
    'admin_reset_password_page.html',
    'admin_forgot_password_page.html',
    'admin_two_factor_verification_page.html',
    'admin_404_page.html',
    'access_denied_(403)_page.html',
    'session_expired_page_2.html',
    'maintenance_mode_page.html',
    '_status_page.html',
    '_admin_sidebar_template.html',
    '_apply_sidebar.py'
]

def read_sidebar_template():
    """Read the sidebar template file."""
    template_path = Path('_admin_sidebar_template.html')
    if not template_path.exists():
        print(f"[ERROR] Template file not found: {template_path}")
        return None
    return template_path.read_text(encoding='utf-8')

def find_sidebar_in_file(content):
    """Find the sidebar section in a file."""
    # Look for the sidebar opening tag
    patterns = [
        r'<aside[^>]*class="[^"]*sidebar[^"]*"[^>]*>.*?</aside>',
        r'<aside[^>]*>.*?</aside>',
        r'<!--.*?Standardized.*?Sidebar.*?-->.*?</aside>',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.start(), match.end()
    
    # Also check for nav elements that might be sidebars
    nav_pattern = r'<nav[^>]*class="[^"]*sidebar[^"]*"[^>]*>.*?</nav>'
    match = re.search(nav_pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.start(), match.end()
    
    return None, None

def find_sidebar_script(content):
    """Find the sidebar JavaScript section."""
    # Look for the collapsible menu script
    script_pattern = r'<!--\s*Collapsible\s+Menu\s+JavaScript\s*-->.*?</script>'
    match = re.search(script_pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.start(), match.end()
    return None, None

def inject_sidebar(content, sidebar_html):
    """Inject the sidebar into the file content."""
    # Find existing sidebar
    sidebar_start, sidebar_end = find_sidebar_in_file(content)
    script_start, script_end = find_sidebar_script(content)
    
    if sidebar_start is not None and sidebar_end is not None:
        # Replace existing sidebar
        before_sidebar = content[:sidebar_start]
        after_sidebar = content[sidebar_end:]
        
        # Remove script if it exists separately
        if script_start is not None and script_end is not None:
            # Check if script is after sidebar
            if script_start > sidebar_end:
                after_sidebar = content[sidebar_end:script_start] + content[script_end:]
        
        # Extract sidebar HTML and script
        sidebar_parts = sidebar_html.split('</aside>')
        sidebar_content = sidebar_parts[0] + '</aside>'
        script_content = sidebar_parts[1] if len(sidebar_parts) > 1 else ''
        
        # Find where to insert (look for </body> or end of file)
        body_end = after_sidebar.find('</body>')
        if body_end != -1:
            # Insert script before </body>
            new_content = before_sidebar + sidebar_content + after_sidebar[:body_end] + script_content + after_sidebar[body_end:]
        else:
            # Append at end
            new_content = before_sidebar + sidebar_content + after_sidebar + script_content
        
        return new_content
    else:
        # No existing sidebar found, try to insert after opening body tag
        body_match = re.search(r'<body[^>]*>', content, re.IGNORECASE)
        if body_match:
            insert_pos = body_match.end()
            sidebar_parts = sidebar_html.split('</aside>')
            sidebar_content = sidebar_parts[0] + '</aside>'
            script_content = sidebar_parts[1] if len(sidebar_parts) > 1 else ''
            
            # Find </body> for script insertion
            body_end = content.find('</body>')
            if body_end != -1:
                new_content = content[:insert_pos] + '\n' + sidebar_content + '\n' + content[insert_pos:body_end] + script_content + '\n' + content[body_end:]
            else:
                new_content = content[:insert_pos] + '\n' + sidebar_content + '\n' + content[insert_pos:] + script_content
            return new_content
    
    return None

def process_file(file_path, sidebar_html):
    """Process a single HTML file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        new_content = inject_sidebar(content, sidebar_html)
        
        if new_content and new_content != content:
            file_path.write_text(new_content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"[ERROR] Failed to process {file_path.name}: {e}")
        return False

def main():
    """Main function to process all HTML files."""
    dashboard_dir = Path('.')
    sidebar_html = read_sidebar_template()
    
    if not sidebar_html:
        return
    
    html_files = list(dashboard_dir.glob('*.html'))
    processed = 0
    updated = 0
    skipped = 0
    
    for html_file in html_files:
        if html_file.name in EXCLUDED_FILES:
            skipped += 1
            continue
        
        processed += 1
        if process_file(html_file, sidebar_html):
            updated += 1
            print(f"[OK] Updated sidebar in {html_file.name}")
        else:
            print(f"[SKIP] No changes needed in {html_file.name}")
    
    print(f"\nDone! Processed {processed} files, updated {updated}, skipped {skipped} excluded files.")

if __name__ == '__main__':
    main()
