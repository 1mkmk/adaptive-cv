from PIL import Image
import os

# Path to the logo
logo_path = os.path.join('public', 'adaptivecv-logo.jpg')
output_path = os.path.join('public', 'favicon.ico')

# Open the image
img = Image.open(logo_path)

# Resize to standard favicon sizes (16x16, 32x32, 48x48, 64x64)
favicon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
favicon_images = []

for size in favicon_sizes:
    # Create a square crop of the image
    min_dim = min(img.width, img.height)
    left = (img.width - min_dim) // 2
    top = (img.height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    cropped = img.crop((left, top, right, bottom))
    
    # Resize to the target favicon size
    resized = cropped.resize(size, Image.LANCZOS)
    favicon_images.append(resized)

# Save as ICO file with multiple sizes
favicon_images[0].save(
    output_path,
    format='ICO',
    sizes=[(img.width, img.height) for img in favicon_images],
    append_images=favicon_images[1:]
)

print(f"Favicon generated at: {output_path}")