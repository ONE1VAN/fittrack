import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THUMB_DIR = ROOT / "data" / "thumbnails"


def _try_ffpyplayer(src: Path, dst: Path) -> bool:
    player = None
    try:
        from ffpyplayer.player import MediaPlayer
        import time
        player = MediaPlayer(
            str(src),
            ff_opts={"sync": "video", "an": True, "out_fmt": "rgb24"},
        )
        frame = None
        deadline = time.time() + 3.0
        while time.time() < deadline:
            try:
                f, val = player.get_frame()
            except Exception:
                return False
            if val == "eof":
                break
            if f is not None:
                frame = f
                break
            time.sleep(0.03)
        if frame is None:
            return False
        img, _pts = frame
        try:
            w, h = img.get_size()
            data_planes = img.to_bytearray()
        except Exception:
            return False
        if not data_planes:
            return False
        raw = bytes(data_planes[0])


        expected = w * h * 3
        if len(raw) < expected:
            return False
        try:
            from PIL import Image as PILImage
            if len(raw) == expected:
                pil = PILImage.frombytes("RGB", (w, h), raw)
            else:
                stride = len(raw) // h
                pil = PILImage.frombuffer("RGB", (w, h), raw, "raw", "RGB", stride, 1)
            pil.thumbnail((720, 720))
            pil.save(str(dst), "JPEG", quality=82)
            return True
        except Exception:
            return False
    except Exception:
        return False
    finally:
        if player is not None:
            try:
                player.close_player()
            except Exception:
                pass


def _try_ffmpeg(src: Path, dst: Path) -> bool:
    if not shutil.which("ffmpeg"):
        return False
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-ss", "0.5", "-i", str(src),
             "-frames:v", "1", "-q:v", "3", str(dst)],
            check=True, capture_output=True, timeout=10,
        )
        return dst.exists() and dst.stat().st_size > 0
    except Exception:
        return False


def extract_first_frame(video_path: Path, video_id: int) -> str:
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    dst = THUMB_DIR / f"{video_id}.jpg"
    if dst.exists() and dst.stat().st_size > 0:
        return f"data/thumbnails/{dst.name}"
    ok = _try_ffpyplayer(video_path, dst) or _try_ffmpeg(video_path, dst)
    return f"data/thumbnails/{dst.name}" if ok else ""
