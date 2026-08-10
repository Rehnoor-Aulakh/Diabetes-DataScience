"""
Markdown Converter — Converts HTML/XML to structured Markdown.

Uses markdownify to convert the extracted content into clean Markdown.
Adds a YAML-style frontmatter header with metadata.
"""

import markdownify
from scraper.logger import get_logger

def convert_to_markdown(html_content: str, metadata_header: dict = None) -> str:
    """
    Convert HTML/XML to Markdown and prepend a metadata header.
    """
    logger = get_logger()
    
    if not html_content:
        return ""
        
    try:
        # Configure markdownify to generate clean markdown
        # It handles the XML output from trafilatura reasonably well
        markdown_text = markdownify.markdownify(
            html_content,
            heading_style="ATX",  # Use # instead of ===
            bullets="-"
        )
        
        # Clean up excessive newlines
        lines = markdown_text.split('\n')
        cleaned_lines = []
        consecutive_newlines = 0
        
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
                consecutive_newlines = 0
            else:
                if consecutive_newlines < 1:  # Allow max 1 blank line
                    cleaned_lines.append("")
                consecutive_newlines += 1
                
        markdown_text = '\n'.join(cleaned_lines).strip()
        
        # Add metadata header if provided
        if metadata_header:
            header_lines = ["---"]
            for key, value in metadata_header.items():
                header_lines.append(f"{key}: {value}")
            header_lines.append("---\n\n")
            
            markdown_text = '\n'.join(header_lines) + markdown_text
            
        return markdown_text
        
    except Exception as e:
        logger.error("Markdown conversion error: %s", str(e))
        return ""
