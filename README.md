# phantom-image-creator
Python script to create 'phantom' images that change based on background color.
'Phantom' images is a traditional twitter/X trick, see post:[2014-EG1](https://x.com/AaronFriedman/status/422693248675479552) [2025-EG2-NSFW](https://x.com/Mao80y/status/1981263718563627367).
Here is the script introduction text, formatted in Markdown, ready for you to copy and paste directly into your `README.md` file on GitHub.

-----

### Phantom Image Creator

This Python script creates a "phantom" or "chameleon" PNG image from two source images. The resulting transparent PNG will display `image1` when placed on a dark background (or the color specified by `--color1`) and `image2` when placed on a light background (or the color specified by `--color2`).

This script is a Python port of the core algorithm found in the JavaScript implementation at [kirie.xyz/pages/bw](https://kirie.xyz/pages/bw), converted to a command-line tool using the Pillow library.

#### Requirements

  * Python 3.x
  * Pillow: `pip install pillow`

#### How to Use

Run the script from your terminal, providing two input images. All other arguments are optional.

```bash
python create_image.py [image1_path] [image2_path] [OPTIONS]
```

**Required Arguments:**

  * `image1_path`: Path to the first image (visible on background 1).
  * `image2_path`: Path to the second image (visible on background 2).

**Optional Arguments:**

  * `-o, --output`: The output `.png` file name (default: `result.png`).
  * `-c1, --color1`: The first background color in hex format (default: `#000000` black).
  * `-c2, --color2`: The second background color in hex format (default: `#FFFFFF` white).
  * `-s, --size`: The maximum size (in pixels) for the longest edge of the input images. The script will resize them proportionally (default: `320`).

**Example 1: Basic Usage**

This will use the default colors (black/white) and size (320px).

```bash
python create_image.py "img_A.jpg" "img_B.jpg"
```

*Output: `result.png`*

**Example 2: Custom Usage**

This creates a larger image (1000px) designed for red and blue backgrounds.

```bash
python create_image.py "img_RED.png" "img_BLUE.png" --size 1000 --color1 "#FF0000" --color2 "#0000FF" --output "my_phantom_image.png"
```

*Output: `my_phantom_image.png`*
