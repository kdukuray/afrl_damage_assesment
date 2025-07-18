import streamlit as st
import os
import openai
from uuid import uuid4
import base64

# Ensure folders exist
os.makedirs("images", exist_ok=True)
os.makedirs("damaged_images", exist_ok=True)

# Set up OpenAI client (make sure OPENAI_API_KEY is in your environment)
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# System prompt template for applying damage
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

# helper to encode image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# function to apply damage
def apply_damage(image_path: str, damage_level: int) -> str:
    system_prompt = damage_client_sys_prompt_template.format(damage_level=damage_level)
    base64_image = encode_image(image_path)

    # Simulate damage via OpenAI image edit API
    result = openai_client.images.edit(
        model="gpt-image-1",
        prompt=system_prompt,
        image=[open(image_path, "rb")]
    )

    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    damaged_image_path = image_path.replace("images", "damaged_images")
    with open(damaged_image_path, "wb") as f:
        f.write(image_bytes)

    return damaged_image_path

# Streamlit app UI
st.title("Building Damage Simulator")

uploaded_file = st.file_uploader("Upload a building photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    original_image_path = os.path.join("images", f"{uuid4()}.jpg")
    with open(original_image_path, "wb") as f:
        f.write(uploaded_file.read())
    st.image(original_image_path, caption="Original Building Image", use_container_width=True)

    damage_level = st.slider("Select Damage Level (1 = Minor wear, 5 = Catastrophic destruction)", min_value=1, max_value=5, value=1)

    if st.button("Apply Damage"):
        with st.spinner(f"Applying level {damage_level} damage..."):
            damaged_image_path = apply_damage(original_image_path, damage_level)
        st.image(damaged_image_path, caption=f"Damaged Image (Level {damage_level})", use_container_width=True)
