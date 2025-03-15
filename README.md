# Research Paper to PowerPoint and Podcast Generator

## Problem Statement
This project takes a **research paper** as input and generates:
1. **A formal PowerPoint presentation** for academic or professional use.
2. **A podcast** with customizable styles, such as short and funny or technically focused.

## Live Demo
We gave a bone metastatis prediction research paper as the input and it gave the following output after we prompted it to create a casual, fun and short podcast. 
Here's the paper link: https://ieeexplore.ieee.org/document/10441154
- **Podcast Output:** https://drive.google.com/file/d/1je8cUZz-zE2lIluTEBp4rSykJlDX5ZwY/view?usp=sharing
- For presentations, we try to generate a formal presentation that summarises the key highlights of the paper.
- The papers used for this are as follows:
- paper 1: https://ieeexplore.ieee.org/document/10570111
- paper 2: Cannot be made public as it is yet to be published.
- paper 3:   https://ieeexplore.ieee.org/document/10441154
- **Presentation Samples:** https://drive.google.com/drive/folders/1DDVNbbD7j5vykoHW_PfsznG2ZrRLMz2Y?usp=sharing

---

## **Podcast Generation Approach**
For podcast generation, we utilize the **Murf API** for text-to-speech conversion.

### **Pipeline**
1. **Upload PDF**: The research paper is uploaded.
2. **Text Extraction**: The text is extracted from the PDF.
3. **User Input**: The user provides customization preferences (e.g., tone, style).
4. **Script Generation**: Extracted text and customization remarks are fed into **Gemini** with a structured prompt to generate a podcast script.
5. **Script Formatting**: The script is formatted and prepared for speech synthesis.
6. **Audio Generation**:
   - The **Murf API** is used to generate speech for different speakers (e.g., host and guest voices).
   - The audio files are combined to produce a final podcast.

---

## **PowerPoint Generation Approach**

### **1. Setup and Dependencies**
- Install required packages for image extraction (**unstructured**)
- Set up **sentence-transformers** with **CLIP model**
- Install **FAISS** for similarity search
- Install **python-pptx** for presentation generation

### **2. Image Processing Pipeline**
#### **Image Extraction**
1. Use the **unstructured** library to partition the PDF and extract images.
2. Process extracted images using **CLIP** from **sentence-transformers**.
3. Generate **image embeddings**.
4. Store embeddings in a **FAISS index** along with image paths.

#### **Image Retrieval**
1. Create a **FAISS index** for similarity search.
2. Store image embeddings and corresponding file paths.
3. Implement a **query-based image retrieval system** to find the most relevant image for each section.

### **3. Text Processing Pipeline**
#### **Text Extraction and Sectioning**
1. Extract text from the PDF.
2. Use **regular expressions** to split the text into sections:
   - Identify heading patterns.
   - Default to "Introduction" if no headings are found.

#### **Section Embedding and Retrieval**
1. Use **Hugging Face sentence-transformers (MiniLM model)**.
2. Generate **embeddings** for each section.
3. Store section embeddings in a **FAISS index**.
4. Implement retrieval to find the **top 4 relevant sections**.
5. Generate **contextual summaries** based on retrieved sections.

### **4. Slide Generation**
#### **Content Processing**
1. Extract slide components:
   - **Slide titles**
   - **Bullet points**
2. Preprocess text:
   - Remove unnecessary characters (e.g., asterisks `*`, brackets `<>`, escape sequences).
   - Format bold text correctly.

#### **Presentation Creation**
1. Use **python-pptx** to create presentation templates:
   - **Light Theme** (Professional)
   - **Dark Theme** (High contrast)
   - **Fun Theme** (Creative layout)
2. Define placeholders for text and images.

#### **Slide Assembly**
1. Initialize the presentation with the selected template (fallback to light theme if unavailable).
2. Process query and generate slides dynamically.
3. For each content slide:
   - Truncate text to **77 tokens** (CLIP maximum for image-text matching).
   - Retrieve **relevant images** (top-k=1 for best match).
   - Use placeholder images if no match is found.
4. Alternate image placement:
   - **Even slides**: Image on the left.
   - **Odd slides**: Image on the right.


### **5. Future Improvements**
- **More dynamic layouts** for PowerPoint slides.
- **Better text-image alignment** using advanced embedding techniques.
- **Support for more voice customization** in podcasts.

---

## **Installation & Usage**
### **Requirements**
- Python 3.8+
- Install dependencies:
  ```bash
  pip install unstructured sentence-transformers faiss-cpu python-pptx murf-api
  ```



## **The team**
- Arhaan Godhrawala: https://github.com/Mephisto2412
- Diya Shah: https://github.com/diyashah28
- Drishya Shah: https://github.com/DrishyaShah
- Parth Thakker:https://github.com/Parth-Thakker-2004
- Vrutik Soni: https://github.com/VROCKSONI786

### **License**
MIT License


