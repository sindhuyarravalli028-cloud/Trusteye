import streamlit as st
import cv2
import numpy as np
from PIL import Image
 
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
 
st.subheader("Video Analysis (Beta)")
video_file = st.file_uploader("Choose a video", type=["mp4", "avi", "mov"], key="video_uploader")
 
if video_file is not None:
    with open("temp_video.mp4", "wb") as f:
        f.write(video_file.read())
 
    cap = cv2.VideoCapture("temp_video.mp4")
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    st.write(f"Total frames in video: {frame_count}")
 
    sample_interval = max(1, frame_count // 5)
    frame_num = 0
    shown = 0
 
    while cap.isOpened() and shown < 5:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_num % sample_interval == 0:
            st.write(f"Frame {frame_num}")
            ela_result = perform_ela(frame)
            st.image(ela_result)
            shown += 1
        frame_num += 1
 
    cap.release()
