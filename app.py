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