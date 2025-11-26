# Extension Icons

Place extension icons in this directory:

- `icon.png` - Extension icon (128x128 recommended)
- `logo.png` - Logo for marketplace (200x200 recommended)

## Icon Requirements

For VSCode marketplace:
- Format: PNG
- Size: 128x128 pixels (icon.png)
- Transparent background recommended
- Simple, recognizable design

## Temporary Placeholder

The extension currently uses no icon. To add one:

1. Create/obtain a 128x128 PNG icon
2. Place it in this directory as `icon.png`
3. Update `package.json`:
   ```json
   {
     "icon": "images/icon.png"
   }
   ```
