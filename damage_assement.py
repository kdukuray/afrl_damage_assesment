import streamlit as st
import os
import openai
from uuid import uuid4
import base64
from typing import Tuple

# Make sure these folders exist
os.makedirs("images", exist_ok=True)
os.makedirs("restored_images", exist_ok=True)

# Global Variables
image_client_sys_prompt = """You are a highly accurate image restoration model. Your task is to remove visible damage from buildings in photographs without introducing speculative changes or fictional elements. Your restoration should be as close to realistic and historically accurate as possible, based on the undamaged parts of the structure and surrounding visual context.

Follow these principles:

Preserve all known architectural details. Reconstruct missing or damaged areas only if you can infer them confidently from visible, undamaged parts of the same building.

Do not invent new structures or features. Avoid adding decorations, signage, textures, or colors that aren’t clearly present or implied in the original image.

Stay consistent with the original materials, lighting, and perspective. Use surrounding details to guide the restoration (e.g. replicate intact windows to replace broken ones).

Clean up damage only where necessary. Remove debris, scorch marks, cracks, and shattered elements, but do not alter undamaged areas.

Maintain contextual realism. Do not remove people, trees, or other non-damaged elements unless they are clearly part of the destruction.

Be conservative. When in doubt, leave ambiguous areas neutral rather than guessing.

The goal is to faithfully restore the image to what it likely looked like before the damage, without artistic reinterpretation."""

assessment_client_sys_prompt = """
You are a damage assessment model tasked with analyzing and comparing two images of the **same building**: one taken **before restoration (damaged)** and one **after restoration (repaired)**. Your goal is to perform a precise visual assessment of the **damage present in the 'before' image**, using the 'after' image as reference for what the undamaged state should look like.

You must:
1. Compare the **structural and cosmetic features** of the damaged image against the restored one.
2. Identify and describe the **type and extent of damage** present in the building before restoration.
3. Strictly classify the damage using the provided five-level scale.
4. Return your assessment as a **JSON object** with the exact structure:
```json
{
  "damage_description": "<concise summary of the visual damage>",
  "damage_level": <integer from 1 to 5>
}
"""

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# functions 
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def asses_damage(original_image_path, restored_image_path) -> Tuple[str, int]:
    base64_original_image = encode_image(original_image_path)
    base64_restored_image = encode_image(restored_image_path)

    messages = [
        {"role": "user", "content": [
            {
                "type": "text", 
                "text": assessment_client_sys_prompt
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_original_image}"
                }
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_restored_image}"
                }
            }
        ]}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4.1", 
        messages=messages,
        temperature=0
    )

    output_text = response.choices[0].message.content.strip()
    return output_text

def restore_building(image_path: str) -> str:
    result = openai_client.images.edit(
        model="gpt-image-1",
        prompt=image_client_sys_prompt,
        image=[open(image_path, "rb")]
    )
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    restored_image_filename = original_image_path.replace("images", "restored_images")
    with open(restored_image_filename, "wb") as f:
        f.write(image_bytes)

    return restored_image_filename

    
# streamlit app
st.title("Building Damage Restoration")

uploaded_file = st.file_uploader("Upload a damaged building photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    original_image_path = os.path.join("images", f"{uuid4()}.jpg")
    
    # save the uploaded image
    with open(original_image_path, "wb") as f:
        f.write(uploaded_file.read())

    st.image(original_image_path, caption="Original Damaged Image", use_container_width=True)

    # restore image using OpenAI
    with st.spinner("Restoring image..."):
        # Restored image and original image have same file name, just located in different  folers
        restored_image_path = restore_building(original_image_path) 

    st.image(restored_image_path, caption="Restored Image", use_container_width=True)

    with st.spinner("Assessing Damage"):
        output = asses_damage(original_image_path, restored_image_path)
    st.write(output)
       


