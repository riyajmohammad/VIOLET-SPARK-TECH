#!/usr/bin/env python3
"""Fast image compression for web performance."""
from pathlib import Path
import io
import tempfile
from PIL import Image, ImageFile

ImageFile.MAXBLOCK = 2**20  # 1MB chunks

def compress_images():
    root = Path(__file__).parent
    images = sorted(
        [p for p in root.rglob('*') if p.suffix.lower() in {'.jpg', '.jpeg', '.png'}],
        key=lambda x: x.stat().st_size, reverse=True
    )
    
    print(f"Found {len(images)} images to optimize\n")
    total_orig = 0
    total_new = 0
    
    for p in images:
        try:
            orig_size = p.stat().st_size
            total_orig += orig_size
            
            # Skip very small files
            if orig_size < 10000:
                print(f"⊘ {p.name:40} {orig_size:>10,} (too small)")
                continue
            
            with Image.open(p) as img:
                img.load()
                
                # Resize if too large
                if max(img.size) > 1400:
                    ratio = 1400 / max(img.size)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                
                # Convert to RGB if needed
                if img.mode not in ('RGB', 'L', 'RGBA'):
                    img = img.convert('RGB')
                
                # Compress based on format
                buffer = io.BytesIO()
                if p.suffix.lower() in {'.jpg', '.jpeg'}:
                    img.save(buffer, format='JPEG', quality=75, optimize=True, progressive=True)
                else:
                    # PNG: simple optimization only
                    img.save(buffer, format='PNG', optimize=True)
                
                buffer.seek(0)
                new_data = buffer.read()
            
            # Replace if smaller
            if len(new_data) < orig_size:
                with tempfile.NamedTemporaryFile(delete=False, dir=p.parent, suffix=p.suffix) as f:
                    f.write(new_data)
                    tmp_path = Path(f.name)
                
                tmp_path.replace(p)
                new_size = p.stat().st_size
                total_new += new_size
                reduction = ((orig_size - new_size) / orig_size) * 100
                print(f"✓ {p.name:40} {orig_size:>10,} → {new_size:>10,} ({reduction:>5.1f}%)")
            else:
                total_new += orig_size
                print(f"• {p.name:40} {orig_size:>10,} (already optimal)")
                
        except Exception as e:
            print(f"✗ {p.name:40} ERROR: {type(e).__name__}")
    
    print(f"\n{'='*70}")
    print(f"Total: {total_orig:,} → {total_new:,} bytes")
    print(f"Saved: {total_orig - total_new:,} bytes ({((total_orig-total_new)/total_orig)*100:.1f}%)")
    print(f"{'='*70}")

if __name__ == '__main__':
    compress_images()
