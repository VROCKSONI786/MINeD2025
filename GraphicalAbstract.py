import streamlit as st
import PyPDF2
import groq
import os
from streamlit.components.v1 import html
import re
import json
import textwrap

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
client = groq.Client(api_key=GROQ_API_KEY)

def extract_text_from_pdf(uploaded_file):
    """Extracts text from the uploaded PDF file with better section handling."""
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                # Remove excessive whitespace and normalize line breaks
                page_text = re.sub(r'\s+', ' ', page_text)
                text += page_text + "\n"
        
        # Extract abstract and methodology sections if present
        abstract_match = re.search(r'abstract[:\s]+(.*?)\n\s*(?:introduction|methods|methodology)', 
                                 text.lower(), re.DOTALL)
        methods_match = re.search(r'(?:methods|methodology)[:\s]+(.*?)\n\s*(?:results|discussion)', 
                                text.lower(), re.DOTALL)
        
        extracted_text = ""
        if abstract_match:
            extracted_text += "ABSTRACT:\n" + abstract_match.group(1) + "\n\n"
        if methods_match:
            extracted_text += "METHODOLOGY:\n" + methods_match.group(1)
        
        return extracted_text if extracted_text else text[:15000]
    except Exception as e:
        st.error(f"Error extracting PDF text: {str(e)}")
        return None

def extract_workflow(text):
    """Enhanced workflow extraction with better prompting."""
    try:
        prompt = f"""Analyze this research paper text and extract the exact workflow/methodology in a sequential format.
        
        Rules:
        1. Focus on the actual steps performed in the research
        2. Include only concrete actions, not theoretical concepts
        3. Maintain chronological order
        4. Use clear, concise descriptions
        5. Include 5-8 key steps maximum
        
        Format each step as:
        stepN[Action Description] --> stepN+1[Next Action]
        
        Example format:
        step1[Data Collection] --> step2[Preprocessing]
        step2[Preprocessing] --> step3[Model Training]
        
        Research Text:
        {text}"""

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a research methodology expert. Extract precise, actionable steps from research papers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        workflow = response.choices[0].message.content.strip()
        
        # Clean up the workflow format
        workflow = re.sub(r'Step\s*', 'step', workflow, flags=re.IGNORECASE)
        return workflow
    except Exception as e:
        st.error(f"Error extracting workflow: {str(e)}")
        return None

def generate_mermaid_diagram(workflow_text):
    """Enhanced Mermaid diagram generation with better styling."""
    try:
        mermaid_lines = ["""graph TD
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef highlight fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef important fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    """]
        
        # Process workflow steps
        steps = []
        for line in workflow_text.split('\n'):
            if '-->' in line:
                parts = line.split('-->')
                if len(parts) == 2:
                    source = parts[0].strip()
                    target = parts[1].strip()
                    
                    # Extract step numbers and labels
                    source_match = re.search(r'step(\d+)\[(.*?)\]', source, re.IGNORECASE)
                    target_match = re.search(r'step(\d+)\[(.*?)\]', target, re.IGNORECASE)
                    
                    if source_match and target_match:
                        source_num = source_match.group(1)
                        source_label = source_match.group(2)
                        target_num = target_match.group(1)
                        target_label = target_match.group(2)
                        
                        # Add nodes with proper formatting
                        steps.append(f'    step{source_num}["{source_label}"]:::highlight')
                        steps.append(f'    step{target_num}["{target_label}"]:::highlight')
                        steps.append(f'    step{source_num} --> step{target_num}')
        
        # Add unique steps to diagram
        unique_steps = list(dict.fromkeys(steps))
        mermaid_lines.extend(unique_steps)
        
        return "\n".join(mermaid_lines)
    except Exception as e:
        st.error(f"Error generating Mermaid diagram: {str(e)}")
        return None

def extract_paper_components(text):
    """Enhanced component extraction with better prompting and error handling."""
    try:
        prompt = f"""Analyze this research paper and extract key components. 
        Respond with ONLY valid JSON matching this exact structure:
        {{
            "title": "Clear, concise title",
            "methods": [
                "Key method 1 (concrete technique/approach)",
                "Key method 2",
                "Key method 3"
            ],
            "findings": [
                "Major finding 1 (specific result)",
                "Major finding 2",
                "Major finding 3"
            ],
            "applications": [
                "Practical application 1",
                "Practical application 2"
            ],
            "keywords": [
                "keyword1", "keyword2", "keyword3", "keyword4", "keyword5"
            ]
        }}

        Guidelines:
        - Title: Max 15 words
        - Methods: Focus on specific techniques used
        - Findings: Include concrete results/outcomes
        - Applications: Real-world use cases
        - Keywords: Technical terms from the paper

        Text: {text}"""

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a precise research paper analyzer that extracts key components and formats them as valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.2
        )
        
        # Clean and parse response
        response_text = response.choices[0].message.content.strip()
        
        # Remove any markdown code block markers
        response_text = re.sub(r'```json\s*|\s*```', '', response_text)
        
        # Remove any explanatory text before or after the JSON
        response_text = re.sub(r'^[^{]*', '', response_text)
        response_text = re.sub(r'[^}]*$', '', response_text)
        
        # Ensure the text is valid JSON
        if not response_text.startswith('{') or not response_text.endswith('}'):
            raise ValueError("Response is not valid JSON")
            
        components = json.loads(response_text)
        
        # Validate and clean components
        required_keys = ['title', 'methods', 'findings', 'applications', 'keywords']
        default_components = {
            "title": "Research Paper Analysis",
            "methods": ["Method 1", "Method 2"],
            "findings": ["Finding 1", "Finding 2"],
            "applications": ["Application 1"],
            "keywords": ["Keyword 1", "Keyword 2", "Keyword 3"]
        }
        
        # Check if all required keys exist and are of correct type
        for key in required_keys:
            if key not in components:
                components[key] = default_components[key]
            elif key == 'title':
                if not isinstance(components[key], str) or not components[key].strip():
                    components[key] = default_components[key]
            elif not isinstance(components[key], list) or not components[key]:
                components[key] = default_components[key]
            else:
                components[key] = [str(item).strip() for item in components[key] if str(item).strip()]
                if not components[key]:  # If all items were empty after cleaning
                    components[key] = default_components[key]
        
        return components
        
    except json.JSONDecodeError as e:
        st.error(f"Error parsing JSON response: {str(e)}")
        return default_components
    except Exception as e:
        st.error(f"Error in paper component extraction: {str(e)}")
        return default_components
    
def generate_graphical_abstract_svg(components):
    """Generates an enhanced SVG graphical abstract with better layout and responsiveness."""
    try:
        width = 1000  # Increased width
        height = 800  # Increased height
        center_x = width // 2
        center_y = height // 2
        
        def wrap_text(text, width=20):
            """Wrap text to fit within boxes."""
            return textwrap.fill(text, width=width)
        
        svg = f'''
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
            <defs>
                <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur in="SourceAlpha" stdDeviation="4"/>
                    <feOffset dx="3" dy="3"/>
                    <feComponentTransfer>
                        <feFuncA type="linear" slope="0.3"/>
                    </feComponentTransfer>
                    <feMerge>
                        <feMergeNode/>
                        <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                </filter>
                
                <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#2196F3;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#1976D2;stop-opacity:1" />
                </linearGradient>
                
                <linearGradient id="methodGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#E3F2FD;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#BBDEFB;stop-opacity:1" />
                </linearGradient>
                
                <linearGradient id="findingGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#E8F5E9;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#C8E6C9;stop-opacity:1" />
                </linearGradient>
                
                <linearGradient id="applicationGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#FFF3E0;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#FFE0B2;stop-opacity:1" />
                </linearGradient>
            </defs>
            
            <!-- Title -->
            <rect x="50" y="30" width="{width-100}" height="80" rx="15" 
                fill="url(#headerGrad)" filter="url(#shadow)"/>
            <text x="{center_x}" y="80" text-anchor="middle" 
                fill="white" font-size="24px" font-weight="bold">
                {components['title']}
            </text>
            
            <!-- Methods Section -->
            <g transform="translate(100, 150)">
                <rect x="0" y="0" width="300" height="200" rx="15" 
                    fill="url(#methodGrad)" filter="url(#shadow)"/>
                <text x="150" y="40" text-anchor="middle" font-weight="bold" 
                    fill="#1565C0" font-size="20px">Methods</text>
                {generate_list_items(components['methods'], 80, 40, width=300)}
            </g>
            
            <!-- Findings Section -->
            <g transform="translate({width-400}, 150)">
                <rect x="0" y="0" width="300" height="200" rx="15" 
                    fill="url(#findingGrad)" filter="url(#shadow)"/>
                <text x="150" y="40" text-anchor="middle" font-weight="bold" 
                    fill="#2E7D32" font-size="20px">Findings</text>
                {generate_list_items(components['findings'], 80, 40, width=300)}
            </g>
            
            <!-- Applications Section -->
            <g transform="translate({center_x-200}, 400)">
                <rect x="0" y="0" width="400" height="150" rx="15" 
                    fill="url(#applicationGrad)" filter="url(#shadow)"/>
                <text x="200" y="40" text-anchor="middle" font-weight="bold" 
                    fill="#E65100" font-size="20px">Applications</text>
                {generate_list_items(components['applications'], 80, 40, center=True, width=400)}
            </g>
            
            <!-- Keywords -->
            <g transform="translate(50, {height-100})">
                <text x="0" y="0" font-weight="bold" fill="#424242" font-size="18px">Keywords:</text>
                {generate_keywords(components['keywords'], 120, 0)}
            </g>
            
            <!-- Connecting Lines with Gradients -->
            <defs>
                <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#90CAF9;stop-opacity:0.6" />
                    <stop offset="100%" style="stop-color:#64B5F6;stop-opacity:0.6" />
                </linearGradient>
            </defs>
            <path d="M 400 250 Q {center_x} 250, {width-400} 250" 
                stroke="url(#lineGrad)" stroke-width="3" fill="none"/>
            <path d="M {center_x} 350 L {center_x} 400" 
                stroke="url(#lineGrad)" stroke-width="3"/>
        </svg>
        '''
        return svg
    except Exception as e:
        st.error(f"Error generating SVG: {str(e)}")
        return None

def generate_list_items(items, start_y, spacing, center=False, width=300):
    """Enhanced list item generation with text wrapping and better positioning."""
    svg_items = []
    for i, item in enumerate(items):
        y = start_y + (i * spacing)
        x = width/2 if center else 20
        anchor = "middle" if center else "start"
        
        # Wrap text if too long
        wrapped_lines = textwrap.wrap(item, width=40)
        for j, line in enumerate(wrapped_lines):
            line_y = y + (j * 20)
            svg_items.append(
                f'<text x="{x}" y="{line_y}" text-anchor="{anchor}" '
                f'fill="#37474F" font-size="16px">{line}</text>'
            )
    return "\n".join(svg_items)

def generate_keywords(keywords, start_x, start_y):
    """Enhanced keyword generation with better spacing and style."""
    svg_keywords = []
    x = start_x
    for keyword in keywords:
        svg_keywords.append(
            f'<text x="{x}" y="{start_y}" fill="#616161" '
            f'font-size="16px" font-style="italic">{keyword}</text>'
        )
        x += 180  # Increased spacing between keywords
    return "\n".join(svg_keywords)

def render_mermaid(mermaid_code):
    """Renders Mermaid.js diagram with enhanced styling."""
    try:
        mermaid_html = f"""
        <html>
            <head>
                <script src="https://cdn.jsdelivr.net/npm/mermaid@10.2.3/dist/mermaid.min.js"></script>
                <style>
                    .mermaid {{
                        font-family: Arial, sans-serif;
                        font-size: 16px;
                    }}
                </style>
            </head>
            <body>
                <div class="mermaid" style="max-width: 100%; margin: 0 auto;">
                    {mermaid_code}
                </div>
                <script>
                    var config = {{
                        startOnLoad: true,
                        theme: 'default',
                        securityLevel: 'loose',
                        flowchart: {{
                            useMaxWidth: true,
                            htmlLabels: true,
                            curve: 'basis',
                            rankSpacing: 70,
                            nodeSpacing: 70,
                            padding: 20
                        }},
                        themeVariables: {{
                            fontFamily: 'Arial',
                            fontSize: '16px'
                        }}
                    }};
                    mermaid.initialize(config);
                </script>
            </body>
        </html>
        """
        html(mermaid_html, height=800, scrolling=True)  # Increased height
    except Exception as e:
        st.error(f"Error rendering diagram: {str(e)}")

def render_svg(svg_code):
    """Renders SVG with proper sizing."""
    html(svg_code, height=800, width=1000)  # Increased dimensions

# Streamlit UI with enhanced styling
st.set_page_config(page_title="Research Paper Visualizer", layout="wide")

# Custom CSS
st.markdown("""
    <style>
        .stTitle {
            font-size: 2.5rem !important;
            color: #1976D2 !important;
            margin-bottom: 2rem !important;
        }
        .stSubheader {
            color: #424242 !important;
            font-size: 1.5rem !important;
        }
        .stButton>button {
            background-color: #1976D2;
            color: white;
            font-size: 1.1rem;
            padding: 0.5rem 2rem;
        }
        .stButton>button:hover {
            background-color: #1565C0;
        }
    </style>
""", unsafe_allow_html=True)

st.title("AI-Powered Research Paper Visualizer")

st.markdown("""
### Transform your research paper into interactive visualizations

This tool helps you:
- Extract and visualize the key workflow from your research
- Generate a comprehensive graphical abstract
- Identify and highlight main components of your paper
""")

uploaded_file = st.file_uploader("Upload your research paper (PDF)", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("📄 Extracting text from PDF..."):
        text = extract_text_from_pdf(uploaded_file)
        if text:
            st.success("✅ Text extracted successfully!")
            
            if st.button("🎨 Generate Visualizations"):
                with st.spinner("🔄 Analyzing paper and creating visualizations..."):
                    # Extract workflow
                    workflow_text = extract_workflow(text)
                    
                    # Extract components for graphical abstract
                    components = extract_paper_components(text)
                    
                    if workflow_text and components:
                        tab1, tab2 = st.tabs(["🔄 Workflow Diagram", "📊 Graphical Abstract"])
                        
                        with tab1:
                            st.markdown("### Research Workflow")
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.markdown("#### Extracted Steps")
                                st.text_area("", workflow_text, height=300)
                            with col2:
                                st.markdown("#### Interactive Diagram")
                                mermaid_code = generate_mermaid_diagram(workflow_text)
                                if mermaid_code:
                                    render_mermaid(mermaid_code)
                                    st.download_button(
                                        "💾 Download Mermaid Code",
                                        mermaid_code,
                                        file_name="workflow_diagram.mmd",
                                        mime="text/plain"
                                    )
                        
                        with tab2:
                            st.markdown("### Graphical Abstract")
                            svg_code = generate_graphical_abstract_svg(components)
                            if svg_code:
                                render_svg(svg_code)
                                st.download_button(
                                    "💾 Download SVG",
                                    svg_code,
                                    file_name="graphical_abstract.svg",
                                    mime="image/svg+xml"
                                )
                                
                                # Display extracted components in expandable section
                                with st.expander("📝 View Extracted Components"):
                                    st.json(components)