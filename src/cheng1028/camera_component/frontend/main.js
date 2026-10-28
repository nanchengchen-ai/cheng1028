const video = document.querySelector("#camera");
const canvas = document.querySelector("#frame");
const button = document.querySelector("#toggle");
const status = document.querySelector("#status");
const placeholder = document.querySelector("#placeholder");
let stream = null;
let captureTimer = null;
let starting = false;

function setStatus(message, error = false) {
  status.textContent = message;
  status.dataset.error = String(error);
}

function captureFrame() {
  if (!stream || video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) return;
  canvas.width = 480;
  canvas.height = 360;
  canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
  Streamlit.setComponentValue(JSON.stringify({
    frame: canvas.toDataURL("image/jpeg", 0.65),
    id: Date.now(),
  }));
}

async function startCamera() {
  if (starting || stream) return;
  starting = true;
  button.disabled = true;
  button.textContent = "\u6b63\u5728\u555f\u52d5\u2026";
  setStatus("\u6b63\u5728\u958b\u555f\u651d\u5f71\u6a5f\u2026");
  try {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("\u700f\u89bd\u5668\u672a\u63d0\u4f9b\u651d\u5f71\u6a5f\u529f\u80fd\uff0c\u8acb\u4f7f\u7528 localhost \u958b\u555f\u3002");
    }
    stream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: { width: { ideal: 640 }, height: { ideal: 480 } },
    });
    video.srcObject = stream;
    await video.play();
    placeholder.hidden = true;
    button.textContent = "\u95dc\u9589\u651d\u5f71\u6a5f";
    setStatus("\u651d\u5f71\u6a5f\u5df2\u555f\u52d5\uff0c\u8acb\u5c07\u624b\u638c\u653e\u5728\u93e1\u982d\u524d\u5de6\u53f3\u79fb\u52d5");
    captureFrame();
    captureTimer = window.setInterval(captureFrame, 250);
  } catch (error) {
    stream?.getTracks().forEach((track) => track.stop());
    stream = null;
    placeholder.hidden = false;
    button.textContent = "\u91cd\u8a66\u958b\u555f\u651d\u5f71\u6a5f";
    setStatus(`\u7121\u6cd5\u958b\u555f\u651d\u5f71\u6a5f\uff1a${error.message || error}`, true);
  } finally {
    starting = false;
    button.disabled = false;
  }
}

function stopCamera() {
  if (captureTimer !== null) window.clearInterval(captureTimer);
  captureTimer = null;
  stream?.getTracks().forEach((track) => track.stop());
  stream = null;
  video.srcObject = null;
  placeholder.hidden = false;
  button.textContent = "\u958b\u555f\u651d\u5f71\u6a5f";
  setStatus("\u651d\u5f71\u6a5f\u5df2\u95dc\u9589");
  Streamlit.setComponentValue(null);
}

button.textContent = "\u958b\u555f\u651d\u5f71\u6a5f";
setStatus("\u651d\u5f71\u6a5f\u5c1a\u672a\u555f\u52d5");
button.addEventListener("click", () => stream ? stopCamera() : startCamera());
window.addEventListener("pagehide", () => stream?.getTracks().forEach((track) => track.stop()));
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, () => Streamlit.setFrameHeight(440));
Streamlit.setComponentReady();
