"""Download a small, pinned public sample set for API smoke tests, not training."""

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import urlopen

from app.core.config import BASE_DIR

ROOT = BASE_DIR / "docs" / "predict-selection-audit"
PLANT_COMMIT = "5467f6012d78d1c446145d5f582da6096f852ae8"
SKIMAGE_COMMIT = "a160f384523ac70173d069954b7084bee79fb68e"
SAMPLES = [
    ("apple_healthy_1", "test/Apple leaf/20180511_090912-14gtw8a-e1526047952754.jpg", "Apple___healthy"),
    ("apple_healthy_2", "test/Apple leaf/20180511_091133-24l1vhg-e1526047988236.jpg", "Apple___healthy"),
    ("apple_scab_1", "test/Apple Scab Leaf/28-500x375.jpg", "Apple___Apple_scab"),
    ("apple_scab_2", "test/Apple Scab Leaf/816.jpg", "Apple___Apple_scab"),
    ("tomato_blight_1", "test/Tomato Early blight leaf/039b47d574bc4bb8a14259a1cd96a741.jpg", "Tomato___Early_blight"),
    ("tomato_blight_2", "test/Tomato Early blight leaf/100983448.jpg", "Tomato___Early_blight"),
    ("tomato_healthy_1", "test/Tomato leaf/1684.jpg", "Tomato___healthy"),
    ("tomato_healthy_2", "test/Tomato leaf/2013-08-20-06.jpg", "Tomato___healthy"),
    ("grape_rot_1", "test/grape leaf black rot/03gb.jpg", "Grape___Black_rot"),
    ("grape_rot_2", "test/grape leaf black rot/35589125035_662dd5b258_b.jpg", "Grape___Black_rot"),
]


def main() -> None:
    records: list[dict[str, Any]] = []
    for name, source_path, label in SAMPLES:
        records.append({"name": name, "expected_label": label, "group": "leaf",
                        "url": f"https://raw.githubusercontent.com/pratikkayal/PlantDoc-Dataset/{PLANT_COMMIT}/{quote(source_path, safe='/')}",
                        "source": "PlantDoc; repository CC BY 4.0; folder labels, not independently verified", "extension": ".jpg"})
    for name in ("astronaut", "coffee", "chelsea"):
        records.append({"name": name, "expected_label": None, "group": "non_leaf",
                        "url": f"https://raw.githubusercontent.com/scikit-image/scikit-image/{SKIMAGE_COMMIT}/skimage/data/{name}.png",
                        "source": "scikit-image sample data; see scikit-image data documentation for attribution", "extension": ".png"})
    images = ROOT / "images"
    images.mkdir(parents=True, exist_ok=True)
    for record in records:
        path = images / (record["name"] + record.pop("extension"))
        if path.exists():
            data = path.read_bytes()
        else:
            with urlopen(record["url"], timeout=30) as response:
                data = response.read(10 * 1024 * 1024 + 1)
            if len(data) > 10 * 1024 * 1024:
                raise ValueError("Sample exceeds size limit")
            with path.open("xb") as stream:
                stream.write(data)
        record["path"] = str(path.relative_to(ROOT)).replace("\\", "/")
        record["sha256"] = hashlib.sha256(data).hexdigest()
    manifest = ROOT / "samples.json"
    if manifest.exists():
        if json.loads(manifest.read_text(encoding="utf-8")) != records:
            raise ValueError("Existing manifest differs; refusing overwrite")
    else:
        with manifest.open("x", encoding="utf-8") as stream:
            json.dump(records, stream, ensure_ascii=False, indent=2)
    print(f"Verified {len(records)} downloaded samples: {manifest}")


if __name__ == "__main__":
    main()
