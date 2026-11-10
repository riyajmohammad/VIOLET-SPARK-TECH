from pathlib import Path
import io
import tempfile
from PIL import Image, ImageFile

ImageFile.MAXBLOCK = max(ImageFile.MAXBLOCK, 1024 * 1024)
root = Path(__file__).parent
images = [p for p in root.rglob('*') if p.suffix.lower() in {'.jpg', '.jpeg', '.png'}]

print(f"Found {len(images)} images to process...\n")
total_saved = 0

for p in sorted(images, key=lambda x: x.stat().st_size, reverse=True):
    orig = p.stat().st_size
    try:
        with Image.open(p) as img:
            img.load()
            if max(img.size) > 1400:
                ratio = 1400 / max(img.size)
                img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
            
            if p.suffix.lower() in {'.jpg', '.jpeg'}:
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=72, optimize=True, progressive=True)
            else:
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGBA')
                buffer = io.BytesIO()
                img.save(buffer, format='PNG', optimize=True)
            
            buffer.seek(0)
        
        with tempfile.NamedTemporaryFile(delete=False, dir=p.parent, suffix=p.suffix) as tmp_file:
            tmp_file.write(buffer.read())
            tmp_path = Path(tmp_file.name)
        
        if tmp_path.stat().st_size < orig:
            tmp_path.replace(p)
            new = p.stat().st_size
            saved = orig - new
            total_saved += saved
            reduction = (saved / orig) * 100
            print(f'✓ {p.relative_to(root)}: {orig:,} → {new:,} bytes (saved {saved:,} | {reduction:.1f}%)')
        else:
            tmp_path.unlink()
            print(f'- {p.relative_to(root)}: {orig:,} bytes (kept original)')
    except KeyboardInterrupt:
        print("\nCompression interrupted by user")
        break
    except Exception as e:
        print(f'✗ {p.relative_to(root)}: ERROR - {e}')
        continue

print(f"\n{'='*70}")
print(f"Total space saved: {total_saved:,} bytes ({total_saved/(1024*1024):.2f} MB)")
print(f"{'='*70}")
