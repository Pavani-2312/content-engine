import streamlit as st
import time
from text_gen import generate_tagline, generate_blog_intro, generate_social_post
from image_gen import build_image_prompt, generate_image
from video_gen import build_motion_prompt, generate_video

st.set_page_config(page_title="AI Content Engine", layout="wide")

def safe_call(fn, *, fallback, errors: list, step: str):
    try:
        return fn()
    except Exception as e:
        time.sleep(2)
        try:
            return fn()
        except Exception as e2:
            errors.append({"step": step, "error": str(e2)})
            return fallback

def run_pipeline(brief: dict) -> dict:
    errors = []
    
    tagline = safe_call(
        lambda: generate_tagline(brief["product"], brief["audience"], brief["tone"]),
        fallback="", errors=errors, step="tagline"
    )
    
    blog_intro = safe_call(
        lambda: generate_blog_intro(brief["product"], brief["audience"], brief["tone"], tagline),
        fallback="", errors=errors, step="blog_intro"
    )
    
    social = safe_call(
        lambda: generate_social_post(brief["product"], brief["tone"]),
        fallback={}, errors=errors, step="social"
    )
    
    image_prompt = build_image_prompt(brief["product"], tagline, brief["tone"])
    image_url = safe_call(
        lambda: generate_image(image_prompt),
        fallback=None, errors=errors, step="image"
    )
    
    video_url = None
    if image_url:
        motion_prompt = build_motion_prompt()
        video_url = safe_call(
            lambda: generate_video(image_url, motion_prompt),
            fallback=None, errors=errors, step="video"
        )
    
    return {
        "tagline": tagline,
        "blog_intro": blog_intro,
        "social": social,
        "image_url": image_url,
        "video_url": video_url,
        "meta": {**brief, "errors": errors},
    }

st.title("🎨 AI Content Engine")

with st.sidebar:
    st.header("Product Brief")
    product = st.text_input("Product Name", placeholder="AquaPure Bottle")
    audience = st.text_area("Target Audience", placeholder="Eco-conscious urban commuters, age 25-40")
    tone = st.selectbox("Brand Tone", ["playful", "premium", "eco"])
    
    generate_btn = st.button("🚀 Generate Campaign", type="primary", use_container_width=True)

if generate_btn and product and audience:
    brief = {"product": product, "audience": audience, "tone": tone}
    
    with st.status("Generating campaign assets...", expanded=True) as status:
        st.write("⏳ Generating tagline...")
        suite = {"tagline": "", "blog_intro": "", "social": {}, "image_url": None, "video_url": None}
        
        st.session_state["suite"] = run_pipeline(brief)
        status.update(label="✅ Campaign complete!", state="complete")

if "suite" in st.session_state:
    suite = st.session_state["suite"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Text Assets")
        
        with st.container(border=True):
            st.caption("**Few-shot prompting**")
            st.markdown(f"### {suite['tagline']}")
        
        with st.expander("Blog Introduction — Role-based prompting", expanded=True):
            st.markdown(suite["blog_intro"])
        
        with st.container(border=True):
            st.caption("**Structured output**")
            st.subheader("Social Media Posts")
            if suite["social"]:
                tab1, tab2, tab3 = st.tabs(["Twitter", "Instagram", "LinkedIn"])
                with tab1:
                    st.write(suite["social"].get("twitter", ""))
                with tab2:
                    st.write(suite["social"].get("instagram", ""))
                with tab3:
                    st.write(suite["social"].get("linkedin", ""))
    
    with col2:
        st.subheader("🎨 Visual Assets")
        
        if suite["image_url"]:
            with st.container(border=True):
                st.caption("**Image prompt formula**")
                st.image(suite["image_url"], use_container_width=True)
        else:
            st.error("Image generation failed")
        
        if suite["video_url"]:
            with st.container(border=True):
                st.caption("**OpenRouter image-to-video**")
                st.video(suite["video_url"])
        else:
            st.info("Video generation skipped or failed")
    
    if suite["meta"]["errors"]:
        with st.expander("⚠️ Errors encountered"):
            for err in suite["meta"]["errors"]:
                st.error(f"{err['step']}: {err['error']}")
elif generate_btn:
    st.warning("Please fill in Product Name and Target Audience")
