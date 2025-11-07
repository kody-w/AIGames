# App Icons

## Required Sizes

Generate the following icon sizes for the PWA:

- icon-72x72.png
- icon-96x96.png
- icon-128x128.png
- icon-144x144.png
- icon-152x152.png
- icon-192x192.png
- icon-384x384.png
- icon-512x512.png

## iOS-Specific

- apple-touch-icon.png (180x180)
- safari-pinned-tab.svg (vector)

## Additional

- badge-72x72.png (for notification badge)
- favicon.ico (16x16, 32x32, 48x48)

## Generation Script

Use ImageMagick to generate all sizes from a source logo:

```bash
# Install ImageMagick
brew install imagemagick  # macOS
apt-get install imagemagick  # Ubuntu

# Generate all sizes
for size in 72 96 128 144 152 192 384 512; do
  convert logo.png -resize ${size}x${size} icon-${size}x${size}.png
done

# Generate iOS icon
convert logo.png -resize 180x180 apple-touch-icon.png

# Generate favicon
convert logo.png -resize 32x32 favicon.ico
```

## Maskable Icons

For Android adaptive icons, icons should be "maskable" with safe area:

- Place important content in center 80% of icon
- Use transparent or solid background
- Test at: https://maskable.app/

## Design Guidelines

- Use simple, recognizable design
- High contrast works best
- Avoid fine details (hard to see at small sizes)
- Test on both light and dark backgrounds
- Follow platform guidelines:
  - iOS: Rounded square with no transparency
  - Android: Can use transparency and masks
