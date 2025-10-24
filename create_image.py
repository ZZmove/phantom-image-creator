import sys
import argparse
from PIL import Image, ImageColor, ImageChops

def hex_to_rgb(hex_str):
    """
    Converts a hex color string (e.g., "#FF0000") into an RGB tuple (e.g., (255, 0, 0)).
    This replaces the JS 'convertColor' and regex logic.
    """
    try:
        # ImageColor.getrgb handles both "#FFF" and "#FFFFFF" formats
        return ImageColor.getrgb(hex_str)
    except ValueError:
        print(f"Error: Invalid color string '{hex_str}'. Please use #RRGGBB or #RGB format.")
        sys.exit(1)

def interpolate(x, bc1, bc2):
    """
    Linearly interpolates between two background colors (bc1, bc2) by a factor of x (0.0 to 1.0).
    This is a direct Python translation of the 'interpolate' function from the JS code.
    """
    # bc1 and bc2 are already (r, g, b) tuples
    r = bc1[0] + (bc2[0] - bc1[0]) * x
    g = bc1[1] + (bc2[1] - bc1[1]) * x
    b = bc1[2] + (bc2[2] - bc1[2]) * x
    # Return a tuple of rounded integers
    return (int(round(r)), int(round(g)), int(round(b)))

def load_and_prepare_image(image_path, size):
    """
    Loads an image, handles transparency, converts it to grayscale, and resizes it proportionally.
    This replaces the core logic of the 'loadImage' function from the JS code.
    """
    try:
        img = Image.open(image_path)
    except FileNotFoundError:
        print(f"Error: File not found '{image_path}'.")
        sys.exit(1)
    except Exception as e:
        print(f"Error opening image '{image_path}': {e}")
        sys.exit(1)

    # 1. Create a white background to handle transparency in the input image.
    #    This corresponds to the JS .composite(..., BLEND_DESTINATION_OVER) and .opaque()
    bg = Image.new("RGB", img.size, (255, 255, 255))
    try:
        # Paste using the alpha channel as a mask
        bg.paste(img, (0, 0), img)
    except ValueError:
        # If the image has no alpha channel, paste it directly
        bg.paste(img, (0, 0))
    
    img = bg

    # 2. Convert to grayscale (corresponds to JS .greyscale())
    img = img.convert('L')

    # 3. Resize proportionally (corresponds to JS .resize(..., Jimp.RESIZE_BICUBIC))
    #    Image.thumbnail maintains the aspect ratio, limiting the longest edge to 'size'.
    #    LANCZOS is a high-quality filter, similar to BICUBIC.
    img.thumbnail((size, size), Image.Resampling.LANCZOS)

    return img

def composite_images(args):
    """
    Executes the core image compositing algorithm.
    This replaces the 'composite' function from the JS code.
    """
    print("Starting image processing...")

    # 1. Load and prepare images
    print(f"Loading image 1: {args.image1}")
    img1 = load_and_prepare_image(args.image1, args.size)
    print(f"Loading image 2: {args.image2}")
    img2 = load_and_prepare_image(args.image2, args.size)

    # 2. Convert background colors
    bc1 = hex_to_rgb(args.color1)
    bc2 = hex_to_rgb(args.color2)
    print(f"Background color 1: {bc1}")
    print(f"Background color 2: {bc2}")

    # 3. Determine final canvas size (JS: resultWidth, resultHeight)
    result_width = max(img1.width, img2.width)
    result_height = max(img1.height, img2.height)
    print(f"Creating canvas with size: {result_width}x{result_height}")

    # 4. Paste images centered onto black/white backgrounds
    #    (JS: new Jimp(..., "#000000") / "#FFFFFF")
    base1 = Image.new('L', (result_width, result_height), 0)   # Black
    base2 = Image.new('L', (result_width, result_height), 255) # White

    offset1 = (int(round((result_width - img1.width) / 2)), int(round((result_height - img1.height) / 2)))
    offset2 = (int(round((result_width - img2.width) / 2)), int(round((result_height - img2.height) / 2)))

    base1.paste(img1, offset1)
    base2.paste(img2, offset2)
    
    # base1 (image1) and base2 (image2) are now grayscale images at the final size
    
    # 5. Simulate the JS channel blend
    #    JS: image1(G=-255) + image2(R=-255)
    #    Result: R = image1, G = image2
    #    We merge the two grayscale images directly into the R and G channels.
    print("Merging image channels...")
    # We only need R and G. The B channel can be ignored (set to 0).
    blue_channel = Image.new('L', (result_width, result_height), 0)
    merged_rg = Image.merge('RGB', (base1, base2, blue_channel))
    
    # 6. Prepare the output image and pixel access
    result_image = Image.new('RGBA', (result_width, result_height))
    
    # Load pixel data for fast read/write access
    try:
        merged_pixels = merged_rg.load()
        result_pixels = result_image.load()
    except Exception as e:
        print(f"Error accessing pixel data: {e}")
        return

    print("Executing core algorithm (pixel scan)...")
    
    # 7. Iterate over all pixels (JS: .scan() function)
    for y in range(result_height):
        for x in range(result_width):
            # r_val is from image1, g_val is from image2
            r_val, g_val, _ = merged_pixels[x, y]
            
            # --- This is the core of the JS algorithm ---
            b1 = float(r_val) / 2.0
            b2 = float(g_val) / 2.0 + 127.5
            
            a = 255.0 - b2 + b1
            
            b = 0.0
            if a > 0:
                # Avoid division by zero
                b = b1 / a
            
            # Calculate final RGB via interpolation
            rgb_tuple = interpolate(b, bc1, bc2)
            
            # Round alpha and clamp it to the 0-255 range
            final_alpha = int(round(a))
            final_alpha = max(0, min(255, final_alpha)) # Clamp
            
            # Set the final RGBA pixel
            result_pixels[x, y] = (rgb_tuple[0], rgb_tuple[1], rgb_tuple[2], final_alpha)
            # --- End of algorithm ---

    print("Algorithm complete.")

    # 7b. *** Add 1px transparent border ***
    print("Adding 1px transparent border...")
    new_width = result_image.width + 2
    new_height = result_image.height + 2
    
    # Create a canvas that is (0, 0, 0, 0) = R,G,B,Alpha (fully transparent)
    bordered_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
    
    # Paste the original image into the center of the new canvas (at offset 1, 1)
    bordered_image.paste(result_image, (1, 1))
    
    # 8. Save the final image
    print("Saving file...")
    try:
        # Save the image with the border
        bordered_image.save(args.output)
        print(f"\nSuccess! Image saved to: {args.output}")
    except Exception as e:
        print(f"Error saving image: {e}")

def main():
    """
    Sets up and parses the command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Creates a 'phantom' transparent image from two input images.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Required positional arguments
    parser.add_argument(
        "image1",
        help="Path to the first image (visible on background 1)"
    )
    parser.add_argument(
        "image2",
        help="Path to the second image (visible on background 2)"
    )
    
    # Optional arguments
    parser.add_argument(
        "-o", "--output",
        default="result.png",
        help="The output .png file name.\n(default: result.png)"
    )
    parser.add_argument(
        "-c1", "--color1",
        default="#000000",
        help="The first background color (hex format).\n(default: #000000 black)"
    )
    parser.add_argument(
        "-c2", "--color2",
        default="#FFFFFF",
        help="The second background color (hex format).\n(default: #FFFFFF white)"
    )
    parser.add_argument(
        "-s", "--size",
        type=int,
        default=320,
        help="The maximum size (pixels) for the longest edge of the image.\n(default: 320)"
    )
    
    args = parser.parse_args()
    
    # Run the main program
    composite_images(args)

if __name__ == "__main__":
    main()