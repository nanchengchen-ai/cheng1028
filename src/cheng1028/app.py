from __future__ import annotations

import base64
import json
import time
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
import streamlit.components.v1 as components


ROOT = Path(__file__).resolve().parents[2]
IMAGE_DIR = ROOT / "assets" / "images"
SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
camera_component = components.declare_component(
    "gesture_camera_v4",
    path=str(Path(__file__).parent / "camera_component" / "frontend"),
)


def get_images() -> list[Path]:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(
        (
            path
            for path in IMAGE_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGES
        ),
        key=lambda path: path.name.casefold(),
    )


def apply_gesture(gesture: str, image_count: int) -> None:
    if image_count <= 0:
        return

    if gesture == "first":
        st.session_state.photo_index = 0
    elif gesture == "last":
        st.session_state.photo_index = image_count - 1
    elif gesture == "previous":
        st.session_state.photo_index = (st.session_state.photo_index - 1) % image_count
    elif gesture == "next":
        st.session_state.photo_index = (st.session_state.photo_index + 1) % image_count


def detect_hand_center(frame: np.ndarray) -> float | None:
    """Estimate a hand's horizontal position using local skin-color segmentation."""
    height, width = frame.shape[:2]
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    ycrcb_mask = cv2.inRange(ycrcb, np.array([25, 125, 65]), np.array([255, 185, 140]))
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv_mask = cv2.inRange(hsv, np.array([0, 25, 45]), np.array([28, 255, 255]))
    red_mask = cv2.inRange(hsv, np.array([165, 25, 45]), np.array([180, 255, 255]))
    mask = cv2.bitwise_or(ycrcb_mask, cv2.bitwise_or(hsv_mask, red_mask))
    mask[: int(height * 0.20), :] = 0
    kernel = np.ones((5, 5), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = width * height * 0.003
    max_area = width * height * 0.45
    candidates = [contour for contour in contours if min_area <= cv2.contourArea(contour) <= max_area]
    if not candidates:
        return None
    contour = max(candidates, key=cv2.contourArea)
    moments = cv2.moments(contour)
    if moments["m00"] == 0:
        return None
    return (moments["m10"] / moments["m00"]) / width


def main() -> None:
    st.set_page_config(
        page_title="\u624b\u52e2\u76f8\u7c3f", page_icon="\U0001f590\ufe0f", layout="wide"
    )
    st.title("\U0001f590\ufe0f \u624b\u52e2\u76f8\u7c3f")
    st.caption("\u5141\u8a31\u700f\u89bd\u5668\u4f7f\u7528\u651d\u5f71\u6a5f\uff0c\u4ee5\u624b\u52e2\u5207\u63db\u5716\u7247\uff1b\u4e5f\u53ef\u4ee5\u4f7f\u7528\u6309\u9215\u63a7\u5236\u3002")

    images = get_images()
    uploaded_images = st.file_uploader(
        "\u52a0\u5165\u76f8\u7c3f\u5716\u7247",
        type=["jpg", "jpeg", "png", "webp", "bmp"],
        accept_multiple_files=True,
        help="\u53ef\u9078\u53d6\u591a\u5f35\u5716\u7247\uff0c\u5716\u7247\u6703\u4fdd\u7559\u5728\u76ee\u524d\u700f\u89bd\u5668\u5de5\u4f5c\u968e\u6bb5\u3002",
    )
    photos = [(path.name, str(path)) for path in images]
    photos.extend((image.name, image) for image in uploaded_images)
    if "photo_index" not in st.session_state:
        st.session_state.photo_index = 0
    if "last_camera_command_id" not in st.session_state:
        st.session_state.last_camera_command_id = None
    if "camera_frame_count" not in st.session_state:
        st.session_state.camera_frame_count = 0
    if "recognition_status" not in st.session_state:
        st.session_state.recognition_status = "\u5c1a\u672a\u6536\u5230\u651d\u5f71\u6a5f\u5f71\u683c"

    st.session_state.photo_index %= max(len(photos), 1)
    left, right = st.columns([1, 1.25], gap="large")

    with left:
        st.subheader("\u651d\u5f71\u6a5f")
        if len(photos) < 2:
            st.info(
                f"\u76ee\u524d\u76f8\u7c3f\u6709 {len(photos)} \u5f35\u7167\u7247\u3002"
                "\u8acb\u5148\u5728\u9801\u9762\u4e0a\u65b9\u52a0\u5165\u81f3\u5c11\u5169\u5f35\u7167\u7247\uff0c"
                "\u624b\u638c\u5de6\u53f3\u79fb\u52d5\u624d\u80fd\u5207\u63db\u5716\u7247\u3002"
            )
        st.markdown(
            "**\u624b\u52e2\u6307\u4ee4**\n\n"
            "- \u624b\u638c\u5411\u5de6\uff1a\u4e0a\u4e00\u5f35\n"
            "- \u624b\u638c\u5411\u53f3\uff1a\u4e0b\u4e00\u5f35"
        )
        command = camera_component(default=None, key="gesture_camera_v4")
        if isinstance(command, str):
            try:
                command = json.loads(command)
            except json.JSONDecodeError:
                command = None
        if isinstance(command, dict) and command.get("id") != st.session_state.last_camera_command_id:
            st.session_state.last_camera_command_id = command.get("id")
            st.session_state.camera_frame_count += 1
            frame_data = command.get("frame", "")
            try:
                frame_bytes = base64.b64decode(frame_data.partition(",")[2])
                frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                hand_x = detect_hand_center(frame) if frame is not None else None
            except (ValueError, cv2.error):
                hand_x = None

            if hand_x is None:
                st.session_state.last_hand_x = None
                st.session_state.recognition_status = "\u672a\u5075\u6e2c\u5230\u624b\u90e8\uff1b\u8acb\u5c07\u624b\u638c\u653e\u5165\u93e1\u982d\u4e0b\u534a\u90e8"
            else:
                st.session_state.recognition_status = (
                    "\u5df2\u5075\u6e2c\u5230\u624b\u90e8\uff0c\u4f4d\u7f6e "
                    f"{hand_x:.0%}\uff1b\u5de6\u53f3\u79fb\u52d5\u5207\u5716"
                )
                anchor_x = st.session_state.get("last_hand_x")
                now = time.monotonic()
                cooldown_complete = now - st.session_state.get("last_gesture_time", 0.0) >= 0.7
                if anchor_x is not None and cooldown_complete:
                    delta = hand_x - anchor_x
                    if delta >= 0.08:
                        apply_gesture("next", len(photos))
                        st.session_state.last_gesture_time = now
                        st.session_state.last_hand_x = hand_x
                        st.session_state.last_camera_command = "next"
                        st.session_state.recognition_status = "\u6307\u4ee4\uff1a\u4e0b\u4e00\u5f35"
                    elif delta <= -0.08:
                        apply_gesture("previous", len(photos))
                        st.session_state.last_gesture_time = now
                        st.session_state.last_hand_x = hand_x
                        st.session_state.last_camera_command = "previous"
                        st.session_state.recognition_status = "\u6307\u4ee4\uff1a\u4e0a\u4e00\u5f35"
                elif anchor_x is None:
                    st.session_state.last_hand_x = hand_x
        st.caption(
            f"\u8fa8\u8b58\u72c0\u614b\uff1a{st.session_state.recognition_status}"
            f"\uff08\u5f71\u683c {st.session_state.camera_frame_count}\uff09"
        )
        if st.session_state.get("last_camera_command"):
            gesture_labels = {
                "first": "\u7b2c\u4e00\u5f35",
                "last": "\u6700\u5f8c\u4e00\u5f35",
                "previous": "\u4e0a\u4e00\u5f35",
                "next": "\u4e0b\u4e00\u5f35",
            }
            st.success(
                "\u6700\u8fd1\u624b\u52e2\u6307\u4ee4\uff1a"
                f"{gesture_labels[st.session_state.last_camera_command]}"
            )

    with right:
        st.subheader("\u5716\u7247\u5c55\u793a")
        if photos:
            index = st.session_state.photo_index
            selected_name, selected_image = photos[index]
            st.image(selected_image, use_container_width=True)
            st.caption(
                f"\u7b2c {index + 1} \u5f35\uff0c\u5171 {len(photos)} \u5f35\u3000\uff5c\u3000{selected_name}"
            )
        else:
            st.info(
                "\u76f8\u7c3f\u76ee\u524d\u662f\u7a7a\u7684\u3002\u8acb\u5728\u4e0a\u65b9\u52a0\u5165\u5716\u7247\uff0c\u6216\u5c07\u5716\u7247\u653e\u5165 assets/images/\u3002"
            )

        previous, first, next_button, last = st.columns(4)
        disabled = not photos
        if previous.button("\u2190 \u4e0a\u4e00\u5f35", use_container_width=True, disabled=disabled):
            apply_gesture("previous", len(photos))
            st.rerun()
        if first.button("|\u2190 \u7b2c\u4e00\u5f35", use_container_width=True, disabled=disabled):
            apply_gesture("first", len(photos))
            st.rerun()
        if next_button.button("\u4e0b\u4e00\u5f35 \u2192", use_container_width=True, disabled=disabled):
            apply_gesture("next", len(photos))
            st.rerun()
        if last.button("\u6700\u5f8c\u4e00\u5f35 \u2192|", use_container_width=True, disabled=disabled):
            apply_gesture("last", len(photos))
            st.rerun()


if __name__ == "__main__":
    main()
