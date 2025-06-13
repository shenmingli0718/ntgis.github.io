// assets/window_size.js

function sendWindowSize() {
    const event = new CustomEvent("window-resize", {
        detail: {
            width: window.innerWidth
        }
    });
    window.dispatchEvent(event);
}

window.addEventListener("resize", sendWindowSize);
window.addEventListener("load", sendWindowSize);