#!/usr/bin/env python3
"""
Convert FastAPI templates to static HTML files for Netlify deployment
"""

import os
import re
from pathlib import Path

def convert_template_to_static(template_path, output_path):
    """Convert a FastAPI template to static HTML"""
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace FastAPI template variables and URLs
    replacements = {
        # Fix static file paths
        'href="/static/': 'href="./static/',
        'src="/static/': 'src="./static/',
        
        # Remove FastAPI template syntax
        '{{ request }}': '',
        '{% block content %}': '',
        '{% endblock %}': '',
        
        # Fix navigation links to work as static files
        'href="/docs"': 'href="https://cardiology-ai-agent.netlify.app/.netlify/functions/api/docs"',
        'href="/hospital"': 'href="./hospital.html"',
        'href="/patient"': 'href="./patient.html"',
        'href="/doctor"': 'href="./doctor.html"',
        'href="/emergency"': 'href="./emergency.html"',
        
        # Update API endpoints to use Netlify functions
        'fetch("/api/': 'fetch("/.netlify/functions/api/',
        'action="/api/': 'action="/.netlify/functions/api/',
        
        # Add note about backend functionality
        '<body class="': '<body class="'
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Add a notice about demo mode for static deployment
    demo_notice = '''
    <!-- Demo Mode Notice -->
    <div id="demo-notice" class="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4">
        <div class="flex">
            <div class="flex-shrink-0">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="ml-3">
                <p class="text-sm">
                    <strong>Demo Mode:</strong> This is a static demo. For full functionality including AI processing, 
                    please visit the <a href="https://github.com/sanjibani/cardiology-ai-agent" class="underline">GitHub repository</a> 
                    to set up the complete system with API keys.
                </p>
            </div>
        </div>
    </div>
    '''
    
    # Insert demo notice after the nav
    content = content.replace('</nav>', f'</nav>\n    {demo_notice}')
    
    # Write the converted file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Converted: {template_path} -> {output_path}")

def main():
    """Convert all templates to static HTML"""
    
    template_dir = Path("templates")
    output_dir = Path("dist")
    
    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)
    
    # Template to filename mapping
    conversions = {
        "index.html": "index.html",
        "hospital_dashboard.html": "hospital.html", 
        "patient_portal.html": "patient.html",
        "doctor_interface.html": "doctor.html",
        "emergency_triage.html": "emergency.html"
    }
    
    for template_file, output_file in conversions.items():
        template_path = template_dir / template_file
        output_path = output_dir / output_file
        
        if template_path.exists():
            convert_template_to_static(template_path, output_path)
        else:
            print(f"Warning: Template {template_path} not found")
    
    print("\n✅ Static HTML conversion complete!")
    print("📁 Files ready for Netlify deployment in ./dist/")

if __name__ == "__main__":
    main()