import streamlit as st
import os
import openai
from uuid import uuid4
import base64

# Make sure folders exist
os.makedirs("images", exist_ok=True)
os.makedirs("damaged_images", exist_ok=True)
os.makedirs("restored_images", exist_ok=True)

# OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# System prompts
damage_client_sys_prompt_template = """
You are a highly realistic architectural image manipulation model.
Your task is to artificially apply **structural and cosmetic damage** to photographs of buildings, simulating different levels of destruction.

Use the following **damage scale** as a precise guide. Render each level with appropriate realism, respecting physics and existing context. Do not invent fantasy or unnatural effects. Maintain lighting and perspective.

Damage levels:

1. **Minor wear and tear:**  
   - Small surface cracks in walls or plaster.  
   - Slight discoloration or fading paint.  
   - Very light dirt streaks from rain or dust.  
   - No structural elements compromised, all windows intact.  
   - The building remains clearly well-maintained overall.

2. **Moderate damage:**  
   - Noticeable cracks running across sections of walls or near window edges.  
   - A few broken or missing window panes, maybe a shutter hanging loosely.  
   - Some chipped bricks, stone, or facade sections.  
   - Light debris scattered near the base (small bricks, tiles).  
   - Possibly minor buckling of metal fixtures (railings, signs).

3. **Heavy damage:**  
   - Large, deep cracks that compromise entire walls or corners.  
   - Several broken windows or window frames dislodged.  
   - Partial collapse of parapets, ledges, balconies, or roof tiles.  
   - Visible rebar or interior structure exposed in some places.  
   - Significant piles of debris near the building base.  
   - Some leaning or slight warping of the building shape.

4. **Severe damage:**  
   - Whole sections of wall collapsed or missing.  
   - Roof partially caved in or completely gone over certain spans.  
   - Support beams visibly fractured or splintered.  
   - Large piles of rubble around the foundation.  
   - Hanging cables, torn piping, or cracked support columns.  
   - The building looks highly unstable, close to total failure.

5. **Catastrophic destruction:**  
   - Most of the structure has collapsed into rubble.  
   - Only fragments of walls or partial frames still stand.  
   - Massive piles of bricks, steel, and broken concrete.  
   - Exposed interiors with furniture or internal walls jutting out awkwardly.  
   - Possible scorched marks, heavy dust clouds, bent metal beams twisted under the weight.  
   - The building is functionally destroyed and irreparable.

Damage level for this request: {damage_level}
"""

restore_client_sys_prompt = """
You are a highly accurate image restoration model. Your task is to remove visible damage from buildings in photographs without introducing speculative changes or fictional elements. Your restoration should be as close to realistic and historically accurate as possible, based on the undamaged parts of the structure and surrounding visual context.

Preserve all known architectural details. Reconstruct missing or damaged areas only if you can infer them confidently from visible, undamaged parts of the same building.

Do not invent new structures or features. Avoid adding decorations, signage, textures, or colors that aren’t clearly present or implied in the original image.

Stay consistent with the original materials, lighting, and perspective. Use surrounding details to guide the restoration (e.g. replicate intact windows to replace broken ones).

Clean up damage only where necessary. Remove debris, scorch marks, cracks, and shattered elements, but do not alter undamaged areas.

Maintain contextual realism. Do not remove people, trees, or other non-damaged elements unless they are clearly part of the destruction.

Be conservative. When in doubt, leave ambiguous areas neutral rather than guessing.
"""

# Helper to encode image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Functions to apply damage and restore
def apply_damage(image_path, damage_level):
    system_prompt = damage_client_sys_prompt_template.format(damage_level=damage_level)
    result = openai_client.images.edit(
        model="gpt-image-1",
        prompt=system_prompt,
        image=[open(image_path, "rb")]
    )
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)
    
    
    damaged_path = os.path.join("damaged_images", os.path.basename(image_path))
    with open(damaged_path, "wb") as f:
        f.write(image_bytes)
    return damaged_path


def restore_damage(image_path):
    # always save to restored_images with same filename
    filename = os.path.basename(image_path)
    restored_path = os.path.join("restored_images", filename)

    # ensure folder exists
    os.makedirs("restored_images", exist_ok=True)

    result = openai_client.images.edit(
        model="gpt-image-1",
        prompt=restore_client_sys_prompt,
        image=[open(image_path, "rb")]
    )
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)
    
    with open(restored_path, "wb") as f:
        f.write(image_bytes)
    return restored_path


# Streamlit app
st.title("Building Damage & Restoration Quality Tester")

uploaded_file = st.file_uploader("Upload a building photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    original_image_path = os.path.join("images", f"{uuid4()}.jpg")
    with open(original_image_path, "wb") as f:
        f.write(uploaded_file.read())
    st.image(original_image_path, caption="Uploaded Image", use_container_width=True)

    mode = st.selectbox("Is this image pre-damage (intact) or already post-damage?", ["Pre-damage", "Post-damage"])
    damage_level = st.slider("Select Damage Level to Test", min_value=1, max_value=5, value=3)

    if st.button("Run Full Cycle Test"):
        if mode == "Pre-damage":
            with st.spinner(f"Applying damage level {damage_level}..."):
                damaged_image_path = apply_damage(original_image_path, damage_level)
            with st.spinner("Restoring damaged image..."):
                restored_image_path = restore_damage(damaged_image_path)

            st.image(original_image_path, caption="Original Intact Image", use_container_width=True)
            st.image(damaged_image_path, caption=f"Damaged Image (Level {damage_level})", use_container_width=True)
            st.image(restored_image_path, caption="Restored Image from Damage", use_container_width=True)

        elif mode == "Post-damage":
            with st.spinner("Restoring damaged image..."):
                restored_image_path = restore_damage(original_image_path)
            with st.spinner(f"Applying damage level {damage_level}..."):
                damaged_restored_image = apply_damage(restored_image_path, damage_level)
            

            st.image(original_image_path, caption="Original Post-damage Image", use_container_width=True)
            st.image(restored_image_path, caption="Restored from Damage", use_container_width=True)
            st.image(damaged_restored_image, caption=f"Damaged Restored Image (Level {damage_level})", use_container_width=True)
