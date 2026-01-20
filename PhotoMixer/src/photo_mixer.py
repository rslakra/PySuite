#!/usr/bin/env python3
"""
Photo Mixer - Combines a background image with a foreground photo
"""

import os
from PIL import Image
import sys
import argparse
import numpy as np
from scipy import ndimage


def get_image_path(prompt):
    """Prompt user for an image path and validate it exists."""
    while True:
        path = input(prompt).strip()

        # Remove quotes if present
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        elif path.startswith("'") and path.endswith("'"):
            path = path[1:-1]

        if os.path.exists(path):
            return path
        else:
            print(f"Error: File '{path}' not found. Please try again.")


def blend_with_alpha(background, foreground, position):
    """Blend foreground onto background using proper alpha compositing."""
    # Convert to numpy arrays for pixel-level operations
    bg_array = np.array(background.convert("RGB"))
    fg_array = np.array(foreground.convert("RGBA"))

    x, y = position
    fg_height, fg_width = fg_array.shape[:2]
    bg_height, bg_width = bg_array.shape[:2]

    # Calculate the region to blend
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(bg_width, x + fg_width)
    y2 = min(bg_height, y + fg_height)

    # Calculate offsets in foreground image
    fg_x1 = x1 - x
    fg_y1 = y1 - y
    fg_x2 = fg_x1 + (x2 - x1)
    fg_y2 = fg_y1 + (y2 - y1)

    # Extract the regions
    bg_region = bg_array[y1:y2, x1:x2].copy().astype(np.float32)
    fg_region = fg_array[fg_y1:fg_y2, fg_x1:fg_x2].astype(np.float32)

    # Extract alpha channel and normalize to 0-1
    alpha = fg_region[:, :, 3:4] / 255.0
    fg_rgb = fg_region[:, :, :3]

    # Alpha compositing: result = foreground * alpha + background * (1 - alpha)
    blended = (fg_rgb * alpha + bg_region * (1 - alpha)).astype(np.uint8)

    # Paste the blended region back
    bg_array[y1:y2, x1:x2] = blended

    return Image.fromarray(bg_array, "RGB")


def blend_mode_multiply(background, foreground, position):
    """Multiply blend mode with proper alpha handling."""
    bg_array = np.array(background.convert("RGB")).astype(np.float32)
    fg_array = np.array(foreground.convert("RGBA")).astype(np.float32)

    x, y = position
    fg_height, fg_width = fg_array.shape[:2]
    bg_height, bg_width = bg_array.shape[:2]

    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(bg_width, x + fg_width), min(bg_height, y + fg_height)
    fg_x1, fg_y1 = x1 - x, y1 - y
    fg_x2, fg_y2 = fg_x1 + (x2 - x1), fg_y1 + (y2 - y1)

    bg_region = bg_array[y1:y2, x1:x2]
    fg_region = fg_array[fg_y1:fg_y2, fg_x1:fg_x2]

    alpha = fg_region[:, :, 3:4] / 255.0
    fg_rgb = fg_region[:, :, :3]

    # Multiply: A * B / 255
    multiplied = bg_region * fg_rgb / 255.0
    # Blend with alpha
    blended = (multiplied * alpha + bg_region * (1 - alpha)).astype(np.uint8)

    bg_array[y1:y2, x1:x2] = blended
    return Image.fromarray(bg_array, "RGB")


def blend_mode_screen(background, foreground, position):
    """Screen blend mode with proper alpha handling."""
    bg_array = np.array(background.convert("RGB")).astype(np.float32)
    fg_array = np.array(foreground.convert("RGBA")).astype(np.float32)

    x, y = position
    fg_height, fg_width = fg_array.shape[:2]
    bg_height, bg_width = bg_array.shape[:2]

    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(bg_width, x + fg_width), min(bg_height, y + fg_height)
    fg_x1, fg_y1 = x1 - x, y1 - y
    fg_x2, fg_y2 = fg_x1 + (x2 - x1), fg_y1 + (y2 - y1)

    bg_region = bg_array[y1:y2, x1:x2]
    fg_region = fg_array[fg_y1:fg_y2, fg_x1:fg_x2]

    alpha = fg_region[:, :, 3:4] / 255.0
    fg_rgb = fg_region[:, :, :3]

    # Screen: 255 - (255 - A) * (255 - B) / 255
    screened = 255.0 - ((255.0 - bg_region) * (255.0 - fg_rgb) / 255.0)
    # Blend with alpha
    blended = (screened * alpha + bg_region * (1 - alpha)).astype(np.uint8)

    bg_array[y1:y2, x1:x2] = blended
    return Image.fromarray(bg_array, "RGB")


def blend_mode_overlay(background, foreground, position):
    """Overlay blend mode with proper alpha handling."""
    bg_array = np.array(background.convert("RGB")).astype(np.float32)
    fg_array = np.array(foreground.convert("RGBA")).astype(np.float32)

    x, y = position
    fg_height, fg_width = fg_array.shape[:2]
    bg_height, bg_width = bg_array.shape[:2]

    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(bg_width, x + fg_width), min(bg_height, y + fg_height)
    fg_x1, fg_y1 = x1 - x, y1 - y
    fg_x2, fg_y2 = fg_x1 + (x2 - x1), fg_y1 + (y2 - y1)

    bg_region = bg_array[y1:y2, x1:x2]
    fg_region = fg_array[fg_y1:fg_y2, fg_x1:fg_x2]

    alpha = fg_region[:, :, 3:4] / 255.0
    fg_rgb = fg_region[:, :, :3]

    # Overlay: multiply if base < 128, screen if base >= 128
    mask = bg_region < 128.0
    multiplied = 2.0 * bg_region * fg_rgb / 255.0
    screened = 255.0 - 2.0 * (255.0 - bg_region) * (255.0 - fg_rgb) / 255.0
    overlaid = np.where(mask, multiplied, screened)

    # Blend with alpha
    blended = (overlaid * alpha + bg_region * (1 - alpha)).astype(np.uint8)

    bg_array[y1:y2, x1:x2] = blended
    return Image.fromarray(bg_array, "RGB")


def remove_background(image, threshold=30, corner_samples=10):
    """
    Aggressively remove background from image, keeping only the subject.
    Uses multiple aggressive detection methods.

    Args:
        image: PIL Image (will be converted to RGBA)
        threshold: Color difference threshold for background detection (0-255)
        corner_samples: Number of pixels to sample from corners for background color
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    img_array = np.array(image).astype(np.float32)
    height, width = img_array.shape[:2]
    img_rgb = img_array[:, :, :3]

    # Calculate lightness and saturation for all pixels
    lightness = np.mean(img_rgb, axis=2)
    saturation = np.std(img_rgb, axis=2)

    # AGGRESSIVE METHOD: Remove all light/gray areas (common office backgrounds)
    # 1. Remove very light areas (lightness > 180) - these are almost certainly background
    very_light_mask = lightness > (
        200 - threshold * 0.5
    )  # More aggressive with lower threshold

    # 2. Remove low saturation areas (grayish backgrounds) that are also light
    gray_background = (saturation < 25) & (lightness > 160)

    # 3. Sample edges to find background color
    edge_width = max(10, min(30, width // 8, height // 8))
    edge_pixels = []

    # Sample all edges more aggressively
    if edge_width > 0:
        edge_pixels.extend(img_array[0:edge_width, :].reshape(-1, 4)[:, :3])
        edge_pixels.extend(
            img_array[height - edge_width : height, :].reshape(-1, 4)[:, :3]
        )
        edge_pixels.extend(img_array[:, 0:edge_width].reshape(-1, 4)[:, :3])
        edge_pixels.extend(
            img_array[:, width - edge_width : width].reshape(-1, 4)[:, :3]
        )

    if len(edge_pixels) > 0:
        edge_pixels = np.array(edge_pixels)
        bg_color = np.median(edge_pixels, axis=0)

        # Calculate color difference from background
        color_diff = np.sqrt(np.sum((img_rgb - bg_color) ** 2, axis=2))
        color_similar = color_diff < threshold

        # Combine: background is similar to edge color OR very light OR gray
        background_mask = color_similar | very_light_mask | gray_background
    else:
        # Fallback: just use lightness and saturation
        background_mask = very_light_mask | gray_background
        color_diff = np.zeros((height, width))

    # FIRST: Identify and protect subject areas BEFORE removing background
    # Subject typically has: medium to dark colors, some saturation, different from edges
    subject_criteria = (
        (lightness < 220)  # Not too light (but allow some light skin tones)
        & (saturation > 10)  # Has some color (not pure gray)
    )

    # If we have background color, subject should be different from it
    if len(edge_pixels) > 0:
        subject_criteria = subject_criteria & (color_diff > threshold * 0.5)

    # Additional protection: very dark or very colorful areas are definitely subject
    very_dark = lightness < 120
    very_colorful = saturation > 25
    definitely_subject = very_dark | very_colorful

    # Combine subject protection
    subject_mask = subject_criteria | definitely_subject

    # Start with all background as transparent, but PROTECT subject
    final_alpha = np.where(background_mask & ~subject_mask, 0.0, 1.0)

    # Make sure subject areas stay fully opaque
    final_alpha = np.where(subject_mask, 1.0, final_alpha)

    # Remove everything near edges that looks like background, BUT protect subject
    edge_distance = np.minimum(
        np.minimum(np.arange(height)[:, None], np.arange(width)[None, :]),
        np.minimum(
            height - 1 - np.arange(height)[:, None],
            width - 1 - np.arange(width)[None, :],
        ),
    )
    near_edge = edge_distance < max(10, min(width, height) // 15)
    # Near edges, remove light/gray areas ONLY if they're NOT subject
    edge_background = near_edge & (very_light_mask | gray_background) & ~subject_mask
    final_alpha = np.where(edge_background, 0.0, final_alpha)

    # Smooth edges only for subject (not background)
    # Only smooth areas that are partially transparent but might be subject
    uncertain = (final_alpha > 0.1) & (final_alpha < 0.9)
    if len(edge_pixels) > 0:
        smooth_mask = np.clip((color_diff - threshold * 0.5) / (threshold * 1.5), 0, 1)
        final_alpha = np.where(
            uncertain, np.maximum(final_alpha, smooth_mask * 0.8), final_alpha
        )

    # Cleanup pass: Remove small background particles BUT protect subject
    # Only clean up areas that are NOT clearly subject
    uncertain_areas = ~subject_mask

    # Remove small isolated background particles ONLY in uncertain areas
    kernel_size = 2  # Smaller kernel to be less aggressive
    if np.any(uncertain_areas):
        binary_mask = final_alpha > 0.5
        # Only process uncertain areas - don't touch subject
        uncertain_mask = binary_mask & uncertain_areas
        if np.any(uncertain_mask):
            uncertain_cleaned = ndimage.binary_opening(
                uncertain_mask, structure=np.ones((kernel_size, kernel_size))
            )
            # Apply only to uncertain areas, keep subject intact
            final_alpha = np.where(
                uncertain_areas & ~uncertain_cleaned & (final_alpha < 0.5),
                0.0,
                final_alpha,
            )

    # Fill small holes in subject (closing operation) - but be very careful
    # Only close in areas that are mostly subject
    if np.any(subject_mask):
        subject_alpha = final_alpha > 0.7  # Only close in mostly-opaque areas
        closed = ndimage.binary_closing(
            subject_alpha,
            structure=np.ones((2, 2)),  # Very small kernel
        )
        # Only fill tiny holes (areas that were subject but had small gaps)
        small_holes = (
            closed & ~subject_alpha & (final_alpha > 0.1) & (final_alpha < 0.5)
        )
        final_alpha = np.where(small_holes, 0.6, final_alpha)

    # Additional cleanup: Remove light/gray particles ONLY if they're NOT subject
    light_particles = (final_alpha < 0.3) & very_light_mask & ~subject_mask
    gray_particles = (final_alpha < 0.3) & gray_background & ~subject_mask
    final_alpha = np.where(light_particles | gray_particles, 0.0, final_alpha)

    # Final pass: Remove pixels too similar to background, BUT protect subject
    if len(edge_pixels) > 0:
        too_similar = (
            (color_diff < threshold * 0.7)
            & (final_alpha < 0.8)
            & ~subject_mask  # Don't remove if it's subject
        )
        final_alpha = np.where(too_similar, 0.0, final_alpha)

    # Final protection: Ensure all subject areas are fully opaque
    final_alpha = np.where(subject_mask, 1.0, final_alpha)

    # Update alpha channel
    img_array[:, :, 3] = (final_alpha * 255.0).astype(np.uint8)

    return Image.fromarray(img_array.astype(np.uint8), "RGBA")


def resize_to_fit(foreground, background):
    """Resize foreground image to fit within background while maintaining aspect ratio."""
    bg_width, bg_height = background.size
    fg_width, fg_height = foreground.size

    # Calculate scaling factor to fit within background
    scale_width = bg_width / fg_width
    scale_height = bg_height / fg_height
    scale = min(scale_width, scale_height) * 0.8  # 80% of background size

    new_width = int(fg_width * scale)
    new_height = int(fg_height * scale)

    return foreground.resize((new_width, new_height), Image.Resampling.LANCZOS)


def mix_photos(
    background_path,
    foreground_path,
    output_path,
    blend_mode="normal",
    opacity=0.8,
    bg_threshold=30,
):
    """
    Mix a background and foreground photo.

    Args:
        background_path: Path to background image
        foreground_path: Path to foreground image to overlay
        output_path: Path to save the mixed image
        blend_mode: Blending mode ('normal', 'multiply', 'screen', 'overlay')
        opacity: Opacity of foreground image (0.0 to 1.0)
    """
    try:
        # Load images
        print(f"Loading background image: {background_path}")
        background = Image.open(background_path).convert("RGB")

        print(f"Loading foreground image: {foreground_path}")
        foreground = Image.open(foreground_path)

        # Step 1: Remove background from foreground image completely
        print(
            f"Step 1: Removing background from foreground image (threshold: {bg_threshold})..."
        )
        foreground = remove_background(foreground, threshold=bg_threshold)
        print("  ✓ Background removed, subject isolated")

        # Step 2: Resize foreground to fit nicely on background
        print("Step 2: Resizing foreground image to fit background...")
        foreground = resize_to_fit(foreground, background)
        print("  ✓ Foreground resized")

        # Ensure RGBA mode
        if foreground.mode != "RGBA":
            foreground = foreground.convert("RGBA")

        # Step 3: Adjust opacity if needed (only affects the subject, not removed background)
        if opacity < 1.0:
            alpha = foreground.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            foreground.putalpha(alpha)
            print(f"  ✓ Opacity adjusted to {opacity}")

        # Calculate position to center foreground on background
        bg_width, bg_height = background.size
        fg_width, fg_height = foreground.size
        position = ((bg_width - fg_width) // 2, (bg_height - fg_height) // 2)

        # Create output image starting with background
        output = background.copy()

        # Blend modes with proper alpha compositing
        if blend_mode == "normal":
            # Proper alpha compositing with better blending
            output = blend_with_alpha(output, foreground, position)
        elif blend_mode == "multiply":
            # Multiply blend mode with alpha
            output = blend_mode_multiply(output, foreground, position)
        elif blend_mode == "screen":
            # Screen blend mode (lighter) with alpha
            output = blend_mode_screen(output, foreground, position)
        elif blend_mode == "overlay":
            # Overlay blend mode with alpha
            output = blend_mode_overlay(output, foreground, position)
        else:
            # Default to normal
            output = blend_with_alpha(output, foreground, position)

        # Save the result
        print(f"Saving mixed image to: {output_path}")
        output.save(output_path, quality=95)
        print(f"✓ Successfully created mixed image!")

        return output

    except Exception as e:
        print(f"Error mixing photos: {str(e)}")
        sys.exit(1)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Photo Mixer - Combine Background and Foreground Images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/photo_mixer.py --background bg.jpg --foreground fg.jpg
  python src/photo_mixer.py --background bg.jpg --foreground fg.jpg --blend-mode multiply --opacity 0.9
  python src/photo_mixer.py --background bg.jpg --foreground fg.jpg --output result.jpg
        """,
    )

    parser.add_argument(
        "--background",
        "-b",
        type=str,
        required=True,
        help="Path to the background image (base/larger image that stays full size)",
    )
    parser.add_argument(
        "--foreground",
        "-f",
        type=str,
        required=True,
        help="Path to the foreground image (will be overlaid and resized on background)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output path for the mixed image (default: images/mixed/mixed_<bg>_<fg>.jpg)",
    )
    parser.add_argument(
        "--blend-mode",
        "-m",
        type=str,
        choices=["normal", "multiply", "screen", "overlay"],
        default="normal",
        help="Blending mode: normal (default), multiply, screen, or overlay",
    )
    parser.add_argument(
        "--opacity",
        "-p",
        type=float,
        default=0.8,
        help="Foreground opacity (0.0 to 1.0, default: 0.8)",
    )
    parser.add_argument(
        "--bg-threshold",
        "-t",
        type=int,
        default=30,
        help="Background removal threshold (0-100, lower=more aggressive, default: 30)",
    )

    return parser.parse_args()


def resolve_image_path(path):
    """Resolve image path, checking images/original/ if not found."""
    if os.path.exists(path):
        return path

    # Check in images/original/ directory
    possible_path = os.path.join("images", "original", os.path.basename(path))
    if os.path.exists(possible_path):
        return possible_path

    return None


def validate_paths(background_path, foreground_path):
    """Validate that image paths exist and resolve them if needed."""
    # Resolve background path
    resolved_bg = resolve_image_path(background_path)
    if resolved_bg is None:
        print(f"Error: Background image not found: {background_path}")
        print(f"  Checked: {background_path}")
        print(
            f"  Checked: {os.path.join('images', 'original', os.path.basename(background_path))}"
        )
        sys.exit(1)

    # Resolve foreground path
    resolved_fg = resolve_image_path(foreground_path)
    if resolved_fg is None:
        print(f"Error: Foreground image not found: {foreground_path}")
        print(f"  Checked: {foreground_path}")
        print(
            f"  Checked: {os.path.join('images', 'original', os.path.basename(foreground_path))}"
        )
        sys.exit(1)

    return resolved_bg, resolved_fg


def main():
    """Main function to run the photo mixer."""
    args = parse_arguments()

    # Validate and resolve paths
    background_path, foreground_path = validate_paths(args.background, args.foreground)

    # Validate opacity
    opacity = max(0.0, min(1.0, args.opacity))

    # Determine output path - always save to images/mixed folder
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "images", "mixed"
    )
    os.makedirs(output_dir, exist_ok=True)

    if args.output:
        # If output is specified, use it but ensure it's in images/mixed
        # Handle case where "output=filename" might be passed
        output_value = args.output
        if output_value.startswith("output="):
            output_value = output_value[7:]  # Remove "output=" prefix

        output_filename = os.path.basename(output_value)
        # If it's already a full path, extract just the filename
        if os.path.dirname(output_value):
            output_filename = os.path.basename(output_value)
        output_path = os.path.join(output_dir, output_filename)
    else:
        # Generate output filename
        bg_name = os.path.splitext(os.path.basename(background_path))[0]
        fg_name = os.path.splitext(os.path.basename(foreground_path))[0]
        output_filename = f"mixed_{bg_name}_{fg_name}.jpg"
        output_path = os.path.join(output_dir, output_filename)

    # Display information
    print("=" * 60)
    print("Photo Mixer - Combine Background and Foreground Images")
    print("=" * 60)
    print()
    print("Selected images:")
    print(f"  Background: {background_path}")
    print(f"  Foreground: {foreground_path}")
    print(f"  Blend mode: {args.blend_mode}")
    print(f"  Opacity: {opacity}")
    print(f"  Output: {output_path}")
    print()
    print("-" * 60)

    # Mix the photos
    bg_threshold = max(0, min(100, args.bg_threshold))  # Clamp between 0 and 100
    mix_photos(
        background_path,
        foreground_path,
        output_path,
        args.blend_mode,
        opacity,
        bg_threshold,
    )

    print("-" * 60)
    print(f"✓ Output saved to: {output_path}")


if __name__ == "__main__":
    main()
