"""
Download CIFAR-10 làm OOD dataset.

CIFAR-10: 60K ảnh 32x32, 10 class (không phải lá cây)
Dùng làm far OOD cho plant disease detection.

Cách dùng:
    python ml/src/download_ood_cifar.py --output-dir ml/data/ood_test/cifar10 --num-images 200
"""

import argparse
from pathlib import Path

import torch
import torchvision
from PIL import Image
from tqdm import tqdm


def download_cifar10(output_dir: Path, num_images: int = 200):
    """Download CIFAR-10 và lưu ảnh làm OOD dataset."""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Đang download CIFAR-10...")
    
    # Download CIFAR-10 test set
    test_set = torchvision.datasets.CIFAR10(
        root=str(output_dir.parent),
        train=False,
        download=True
    )
    
    print(f"Đã download {len(test_set)} ảnh")
    
    # Chọn random num_images ảnh
    import numpy as np
    indices = np.random.choice(len(test_set), min(num_images, len(test_set)), replace=False)
    
    print(f"Đang lưu {len(indices)} ảnh vào {output_dir}...")
    
    for idx in tqdm(indices):
        img, label = test_set[idx]
        
        # CIFAR-10 ảnh nhỏ (32x32), resize lên 224x224 để khớp với model
        img = img.resize((224, 224), Image.BICUBIC)
        
        # Lưu ảnh
        output_path = output_dir / f"cifar10_{idx:05d}_label{label}.png"
        img.save(output_path)
    
    print(f"Đã lưu {len(indices)} ảnh vào {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Download CIFAR-10 làm OOD dataset")
    parser.add_argument("--output-dir", type=str, default="ml/data/ood_test/cifar10",
                        help="Thư mục lưu ảnh OOD")
    parser.add_argument("--num-images", type=int, default=200,
                        help="Số ảnh cần lưu")
    args = parser.parse_args()
    
    download_cifar10(args.output_dir, args.num_images)


if __name__ == "__main__":
    main()
