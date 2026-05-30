from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIDEOS_DIR = ROOT / "data" / "videos"


def ensure_videos() -> None:
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    ensure_videos()
