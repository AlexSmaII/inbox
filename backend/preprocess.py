from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image
from pypdfium2 import PdfImage

# DATA_DIR = Path(__file__).parent / "data"
# SAMPLES_DIR = DATA_DIR / "sample"
# OUT_DIR = DATA_DIR / "tmp"

def extract_pod_image(path : Path) -> Image:
    # OUT_DIR.mkdir(exist_ok=True, parents=True)

    if not path.is_file():
        raise FileNotFoundError(f"PDF does not exist: {path}")
    if not path.suffix == ".pdf":
        raise ValueError(f"Not a PDF: {path}")

    out = []
    i = 1
    pdf = pdfium.PdfDocument(path)
    for page in pdf:
        for obj in page.get_objects():
            if isinstance(obj, PdfImage):
                img = obj.get_bitmap().to_pil()
                out.append(img)
                # out_path = OUT_DIR / f"{path.stem}_{i}.png"
                # img.save(out_path)
                # out.append(out_path)
                i += 1
    
    if len(out) > 1:
        raise ValueError(f"Docket PDF contained more than one image: {path}")
    
    return out[0]

# if __name__ == "__main__":
#     samples = [f for f in SAMPLES_DIR.iterdir()]
#     print(extract_pod_images(samples[0]))