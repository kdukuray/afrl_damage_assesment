import streamlit as st
import requests
import os
import openai
from uuid import uuid4
import base64

image_client_sys_prompt = """You are a highly accurate image restoration model. Your task is to remove visible damage from buildings in photographs without introducing speculative changes or fictional elements. Your restoration should be as close to realistic and historically accurate as possible, based on the undamaged parts of the structure and surrounding visual context.

Follow these principles:

Preserve all known architectural details. Reconstruct missing or damaged areas only if you can infer them confidently from visible, undamaged parts of the same building.

Do not invent new structures or features. Avoid adding decorations, signage, textures, or colors that aren’t clearly present or implied in the original image.

Stay consistent with the original materials, lighting, and perspective. Use surrounding details to guide the restoration (e.g. replicate intact windows to replace broken ones).

Clean up damage only where necessary. Remove debris, scorch marks, cracks, and shattered elements, but do not alter undamaged areas.

Maintain contextual realism. Do not remove people, trees, or other non-damaged elements unless they are clearly part of the destruction.

Be conservative. When in doubt, leave ambiguous areas neutral rather than guessing.

The goal is to faithfully restore the image to what it likely looked like before the damage, without artistic reinterpretation."""

image_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

st.title("Street View Explorer")

location = st.text_input("Enter a location (e.g., Times Square, NYC):")

def restore_building(image_path: str) -> str:
    result = image_client.images.edit(
        model="gpt-image-1",
        prompt=image_client_sys_prompt, 
        image=[open(image_path, "rb")]
        )
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    restored_image_filename = os.path.join("restored_images", f"{uuid4()}.jpg")
    with open(restored_image_filename, "wb") as f:
        f.write(image_bytes)



def format_url(location: str) -> str:
    return f"https://maps.googleapis.com/maps/api/streetview?size=600x300&location={location}&heading=151.78&pitch=-0.76&key={google_maps_api_key}"

if location:
    response = requests.get(format_url(location=location))

    if response.status_code == 200:
        # Save and show image
        img_bytes = response.content
        filename = os.path.join("base_images", f"{uuid4()}.jpg")
        with open(filename, "wb") as f:
            f.write(img_bytes)
        
        st.image(filename, caption=f"Street View: {location}")
    else:
        st.error(f"Failed to fetch image. Status code: {response.status_code}")
