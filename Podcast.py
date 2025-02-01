import fitz  # PyMuPDF
import os
import google.generativeai as genai
import re
import requests
import json
from pydub import AudioSegment
import streamlit as st

# Murf AI API Endpoint
API_URL = "https://api.murf.ai/v1/speech/generate"
#API_KEY = "ap2_30ce88ef-190b-4d44-b710-71d5ee0a2679"
API_KEY="ap2_fcf7d39f-da99-444e-b8ab-eea43dcc019b"

# Assign different voices
VOICES = {
    "Host": "en-IN-arohi",  # Choose a natural-sounding voice for the host
    "Guest": "en-IN-aarav"  # Choose an Indian male voice for Ishaan
}

# Function to generate speech for each line
def generate_speech(speaker, text, index):
    payload = {
        "voiceId": VOICES[speaker],
        "style": "Conversational",
        "text": text,
        "rate": 11,
        "pitch": 0,
        "sampleRate": 48000,
        "format": "MP3",
        "channelType": "MONO",
        "pronunciationDictionary": {},
        "encodeAsBase64": False,
        "variation": 1,
        "audioDuration": 0,
        "modelVersion": "GEN2",
        "multiNativeLocale": "en-IN"
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'api-key': API_KEY
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        response_data = response.json()
        if "audioFile" in response_data:
            audio_url = response_data["audioFile"]
            audio_response = requests.get(audio_url)
            if audio_response.status_code == 200:
                filename = f"segment_{index}_{speaker}.mp3"
                with open(filename, "wb") as f:
                    f.write(audio_response.content)
                print(f"Downloaded: {filename}")
                return filename
    print(f"Error generating speech for {speaker}")
    return None

def audio_generation(script,progress_bar):
    # Process each line
    audio_files = []
    for index, (speaker, text) in enumerate(script):
        progress_bar.progress((index + 1) / len(script))
        audio_file = generate_speech(speaker, text, index)
        if audio_file:
            audio_files.append(audio_file)

    # Merge all audio files into one
    final_podcast = AudioSegment.empty()
    for file in audio_files:
        segment = AudioSegment.from_mp3(file)
        final_podcast += segment + AudioSegment.silent(duration=500)  # Adding small pauses

    # Save final podcast
    final_podcast.export("final_podcast.mp3", format="mp3")
    print("Podcast created successfully: final_podcast.mp3")
    
    for file in audio_files:
        os.remove(file)
    return "final_podcast.mp3"


def extract_text_pypdf2(pdf_path):
    try:
        import PyPDF2
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            for i in range(num_pages):
                page = reader.pages[i]
                text += page.extract_text()
        return text
    except ImportError:
        return "PyPDF2 not installed. Please install it using: pip install PyPDF2"
    except Exception as e:
        return f"An error occurred with PyPDF2: {e}"


def extract_text_pymupdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        return f"An error occurred with PyMuPDF: {e}"

def clean_text(text):
    match = re.search(r'REFERENCES', text, re.IGNORECASE)
    return text[:match.start()] if match else text

def generate_podcast_script(extracted_text,user_remark):


    genai.configure(api_key="AIzaSyDtljffa-NkSXbL6mY9konUG_y56_MsFPI")

    # Create the model
    generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
    )

    chat_session = model.start_chat()
    response = chat_session.send_message("This is the text extracted from a research paper:"+extracted_text+"Convert this into an interesting conversation between 2 people just like a podcast. The podcast should only contain dialogues and no extra lines relating to intro and outro music. The first speaker should always be Host. The format of dialogues should be Host:<dialogue> SpeakerName:<dialogue>. please do not include any extra formatting or text other than the dialogues."+user_remark)
    #print(response.text)
    return response.text

# def format_script_for_murf(script):
#     murf_script = []
#     lines = script.split("\n")

#     for line in lines:
#         if line.startswith("Host:"):
#             murf_script.append(("Host", line.replace("Host:", "").strip()))
#         else:
#             murf_script.append(("Ishaan", line.replace("Ishaan:", "").strip()))

#     print(murf_script)
def format_script_for_murf(script):
    murf_script = []
    lines = script.split("\n")

    speaker_names = {}  # To store detected speaker names
    detected_speakers = []  # Keep track of detected speaker order

    for line in lines:
        match = re.match(r"^(\w+):\s*(.+)", line)  # Match "Speaker: Dialogue"
        if match:
            speaker, dialogue = match.groups()

            # If a new speaker appears, store their role dynamically
            if speaker not in speaker_names:
                if not speaker_names:  # First speaker is always "Host"
                    speaker_names[speaker] = "Host"
                else:  # Second speaker gets the name "Guest"
                    speaker_names[speaker] = "Guest"

            # Append formatted script with standardized speaker names
            murf_script.append((speaker_names[speaker], dialogue.strip()))

    print(murf_script)
    return murf_script

# def main():
#     pdf_file = input("Enter the path to your PDF file: ")  # Get file path from user

#     # Choose which library to use or try both
#     # extracted_text = extract_text_pypdf2(pdf_file)
#     extracted_text = extract_text_pymupdf(pdf_file) # Often more robust

#     if "error" not in extracted_text.lower() and "not installed" not in extracted_text.lower():
#         output_file = input("Enter the path to save the extracted text (e.g., output.txt): ")
#         try:
#             with open(output_file, 'w', encoding='utf-8') as outfile:  # Handle encoding
#                 outfile.write(extracted_text)
#             print(f"Text successfully extracted and saved to {output_file}")
#             print(extracted_text)  # Print the error message
#             cleaned_text=clean_text(extracted_text)
#             podcast_script=generate_podcast_script(cleaned_text)
#             print(podcast_script)
#             final_script=format_script_for_murf(podcast_script)
#             audio_generation(final_script)
#         except Exception as e:
#             print(f"Error saving to file: {e}")
#     else:
#         print(extracted_text)  # Print the error message
#         cleaned_text=clean_text(extracted_text)
#         podcast_script=generate_podcast_script(cleaned_text)
#         print(podcast_script)
#         format_script_for_murf(podcast_script)


# if __name__ == "__main__":
#     main()

# Streamlit UI
st.title("📜➡️🎙️ AI-Powered Research Paper Podcast Generator")

uploaded_file = st.file_uploader("Upload a Research Paper (PDF)", type=["pdf"])

if uploaded_file:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success("PDF uploaded successfully! Extracting text...")

    extracted_text = extract_text_pymupdf("temp.pdf")
    cleaned_text = clean_text(extracted_text)
    
    # Add a text box for the user to enter customization remarks
    user_remark = st.text_area("Add customization remarks for the podcast script", 
                               placeholder="Example: Make it more humorous, Use a formal tone, Add an expert's opinion, etc.")
    
    st.info("Generating podcast script...")
    podcast_script = generate_podcast_script(cleaned_text,user_remark)
    
    st.text_area("Generated Podcast Script", podcast_script, height=300)

    final_script = format_script_for_murf(podcast_script)

    st.info("Generating audio files...")
    progress_bar = st.progress(0)
    audio_file_path= audio_generation(final_script, progress_bar)

    # Check if the file exists before trying to read it
    if os.path.exists(audio_file_path):
        with open(audio_file_path, "rb") as file:
            audio_bytes = file.read()

        # Optional: Allow users to listen to the podcast before downloading
        st.audio(audio_bytes, format="audio/mp3")
        # Display the download button
        st.download_button("📥 Download Podcast", audio_bytes, file_name="podcast.mp3", mime="audio/mpeg")
        
    else:
        st.error("❌ Podcast file not found! Please generate the podcast first.")
