from typing import Literal
import streamlit as st
from streamlit.components.v1 import html

OPAQUE_CONTAINER_CSS = """
:root {{
    --background-color: #ffffff;
}}

div[data-testid="stVerticalBlockBorderWrapper"]:has(div.opaque-container-{id}):not(:has(div.not-opaque-container)) div[data-testid="stVerticalBlock"]:has(div.opaque-container-{id}):not(:has(div.not-opaque-container)) > div[data-testid="stVerticalBlockBorderWrapper"] {{
    background-color: var(--background-color);
    width: 100%;
    margin-top: -50px !important;
}}

div[data-testid="stVerticalBlockBorderWrapper"]:has(div.opaque-container-{id}):not(:has(div.not-opaque-container)) div[data-testid="stVerticalBlock"]:has(div.opaque-container-{id}):not(:has(div.not-opaque-container)) > div[data-testid="element-container"] {{
    display: none;
}}

div[data-testid="stVerticalBlockBorderWrapper"]:has(div.not-opaque-container):not(:has(div[class^='opaque-container-'])) {{
    display: none;
}}
"""

OPAQUE_CONTAINER_JS = """
const root = parent.document.querySelector('.stApp');
let lastBackgroundColor = null;

function updateContainerBackground(currentBackground) {
    parent.document.documentElement.style.setProperty('--background-color', currentBackground);
}

function checkForBackgroundColorChange() {
    const style = window.getComputedStyle(root);
    const currentBackgroundColor = style.backgroundColor;
    if (currentBackgroundColor !== lastBackgroundColor) {
        lastBackgroundColor = currentBackgroundColor;
        updateContainerBackground(lastBackgroundColor);
    }
}

const observerCallback = (mutationsList, observer) => {
    for(let mutation of mutationsList) {
        if (mutation.type === 'attributes' && (mutation.attributeName === 'class' || mutation.attributeName === 'style')) {
            checkForBackgroundColorChange();
        }
    }
};

const main = () => {
    checkForBackgroundColorChange();
    const observer = new MutationObserver(observerCallback);
    observer.observe(root, { attributes: true, childList: false, subtree: false });
}

document.addEventListener("DOMContentLoaded", main);
"""

FIXED_CONTAINER_CSS = """
/* Base fixed container styles with proper nesting control */
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.fixed-container-{id}):not(:has(div.not-fixed-container)) {{
    background-color: var(--background-color);
    position: {mode};
    top: -30px;
    width: inherit;
    {position}: {margin};
    z-index: 999999 !important;
    margin-top: -10px !important;
}}

/* Target the vertical block that contains logo */
.st-emotion-cache-d4gr1w {{
    gap: 0 !important;
}}

/* Control main heading block */
div[data-testid="stVerticalBlock"] > .stHeading {{
    margin-top: 0 !important;
}}

/* Target element containers */
.st-emotion-cache-d40hk9 {{
    padding-bottom: 0 !important;
    margin-bottom: 0 !important;
}}

/* Control nested block wrappers */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    margin-top: 0 !important;
}}

/* Original container rules */
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.fixed-container-{id}):not(:has(div.not-fixed-container)) div[data-testid="stVerticalBlock"]:has(div.fixed-container-{id}):not(:has(div.not-fixed-container)) > div[data-testid="element-container"] {{
    display: none;
}}

div[data-testid="stVerticalBlockBorderWrapper"]:has(div.not-fixed-container):not(:has(div[class^='fixed-container-'])) {{
    display: none;
}}

/* Control main block layout */
.st-emotion-cache-1wmy9hl {{
    padding-top: 0 !important;
}}
"""


# Rest of your original code stays exactly the same
def st_opaque_container(
    *,
    height: int | None = None,
    border: bool | None = None,
    key: str | None = None,
):
    opaque_container = st.container()
    non_opaque_container = st.container()
    css = OPAQUE_CONTAINER_CSS.format(id=key)

    with opaque_container:
        html(f"<script>{OPAQUE_CONTAINER_JS}</script>", scrolling=False, height=0)
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='opaque-container-{key}'></div>",
            unsafe_allow_html=True,
        )
    with non_opaque_container:
        st.markdown(
            "<div class='not-opaque-container'></div>",
            unsafe_allow_html=True,
        )

    return opaque_container.container(height=height, border=border)


def st_fixed_container(
    *,
    height: int | None = None,
    border: bool | None = None,
    mode: Literal["fixed", "sticky"] = "fixed",
    position: Literal["top", "bottom"] = "top",
    margin: str = "0",
    transparent: bool = False,
    key: str | None = None,
):
    fixed_container = st.container()

    css = FIXED_CONTAINER_CSS.format(id=key, mode=mode, position=position, margin=margin)

    with fixed_container:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='fixed-container-{key}'></div>",
            unsafe_allow_html=True,
        )

    with fixed_container:
        return st_opaque_container(height=height, border=border, key=f"opaque_{key}")
