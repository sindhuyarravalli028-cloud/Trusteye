import streamlit as st
import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

st.title("TRUSTEYE - Image Authenticity Checker")
st.write("Upload a photo to check if it might be edited or manipulated.")

def perform_ela(image, quality=70, amplify=15):
    temp_path = "temp_original.jpg"
    resaved_path = "temp_resaved.jpg"
    cv2.imwrite(temp_path, image)
    cv2.imwrite(resaved_path, image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    resaved_img = cv2.imread(resaved_path)
    diff = cv2.absdiff(image, resaved_img)
    diff_amplified = cv2.convertScaleAbs(diff, alpha=amplify)
    return diff_amplified

def check_metadata(pil_image):
    exif_data = pil_image.getexif()
    findings = []
    software_suspicious = False

    if not exif_data:
        findings.append("No metadata found - could mean it was stripped (common on social media, but also common when hiding edit history).")
        return findings, software_suspicious

    software_found = False
    for tag_id, value in exif_data.items():
        tag_name = TAGS.get(tag_id, tag_id)
        if tag_name == "Software":
            software_found = True
            findings.append(f"Software field: '{value}'")
            if any(word in str(value).lower() for word in ["photoshop", "gimp", "lightroom", "canva"]):
                findings.append("This image was processed using photo editing software.")
                software_suspicious = True

    if not software_found:
        findings.append("No editing software detected in metadata.")

    return findings, software_suspicious

def check_video_metadata(video_path):
    findings = []
    software_suspicious = False
    metadata_missing = True

    try:
        parser = createParser(video_path)
        if parser:
            metadata = extractMetadata(parser)
            if metadata:
                metadata_missing = False
                text = metadata.exportPlaintext()
                for line in text:
                    clean_line = line.replace("- ", "")
                    findings.append(clean_line)
                    if any(word in clean_line.lower() for word in ["photoshop", "premiere", "capcut", "filmora", "davinci", "adobe"]):
                        software_suspicious = True
            parser.stream._input.close()
    except Exception:
        pass

    if not findings:
        findings.append("No detailed metadata could be extracted from this video.")

    return findings, software_suspicious, metadata_missing

def calculate_confidence(ela_result, metadata_suspicious=False, metadata_missing=False):
    ela_brightness = np.mean(ela_result)
    ela_score = min(ela_brightness * 2, 60)

    metadata_score = 0
    if metadata_suspicious:
        metadata_score += 30
    if metadata_missing:
        metadata_score += 10

    total_score = min(ela_score + metadata_score, 100)
    return round(total_score, 1)

def show_verdict(confidence):
    st.metric(label="Likelihood of editing/manipulation", value=f"{confidence}%")
    if confidence >= 60:
        st.error("Strong indicators of editing - high confidence based on available evidence, though not absolute proof.")
    elif confidence >= 30:
        st.warning("Possible editing detected - moderate evidence, but not conclusive. Manual review recommended.")
    else:
        st.success("Likely unedited - no strong signs of manipulation detected in the available evidence.")
    st.caption("Limitations: This score is based on ELA brightness and metadata only. It is not a definitive proof of manipulation and can be affected by compression, resizing, or re-uploading.")

uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    st.subheader("Original Image")
    st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    ela_result = perform_ela(img)

    st.subheader("ELA Analysis (Error Level Analysis)")
    st.image(ela_result)

    st.info("Bright/glowing patches in the ELA image may indicate edited or manipulated areas. Uniform darkness suggests the image is likely unedited.")

    st.subheader("Metadata Analysis")
    uploaded_file.seek(0)
    pil_img = Image.open(uploaded_file)
    metadata_findings, software_suspicious = check_metadata(pil_img)
    metadata_missing = "No metadata found" in metadata_findings[0]
    for finding in metadata_findings:
        st.write(finding)

    st.subheader("Overall Confidence Score")
    confidence = calculate_confidence(ela_result, software_suspicious, metadata_missing)
    show_verdict(confidence)

st.subheader("Video Analysis (Beta)")
video_file = st.file_uploader("Choose a video", type=["mp4", "avi", "mov"], key="video_uploader")

if video_file is not None:
    with open("temp_video.mp4", "wb") as f:
        f.write(video_file.read())

    cap = cv2.VideoCapture("temp_video.mp4")
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0

    st.subheader("Video Properties")
    st.write(f"Resolution: {width} x {height}")
    st.write(f"Frame rate: {fps:.2f} fps")
    st.write(f"Duration: {duration:.2f} seconds")
    st.write(f"Total frames: {frame_count}")

    st.subheader("Video Metadata Analysis")
    video_metadata_findings, video_software_suspicious, video_metadata_missing = check_video_metadata("temp_video.mp4")
    for finding in video_metadata_findings:
        st.write(finding)

    st.subheader("Frame-by-Frame ELA Analysis")
    sample_interval = max(1, frame_count // 5)
    frame_num = 0
    shown = 0
    frame_scores = []

    while cap.isOpened() and shown < 5:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_num % sample_interval == 0:
            st.write(f"Frame {frame_num}")
            ela_result = perform_ela(frame)
            st.image(ela_result)
            frame_scores.append(np.mean(ela_result))
            shown += 1
        frame_num += 1

    cap.release()

    if frame_scores:
        avg_ela = np.mean(frame_scores)
        st.subheader("Overall Confidence Score")
        video_confidence = calculate_confidence(np.full((10, 10), avg_ela), video_software_suspicious, video_metadata_missing)
        show_verdict(video_confidence)
