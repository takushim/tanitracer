# tanitracer

A python toolbox for reconstructing and analyzing super-resolution images

## Introduction

**tanitracer** is a set of python scripts that accepts time-lapse multipage (or single-page) TIFF files and MetaMorph stack files acquired by single-molecule microscopy. Scripts can detect fluorescent spots and reconstruct super-resolved images using the centroids of detected spots.

Fluorescent spots are detected by Gaussian fitting with subpixel correction after applying Gaussian-Laplacian (LoG) filter to enhance the contours of spots. Spots can be tracked by *k*-nearest neighbor algorithm if necessary. It should be noted that this algorithm is not suitable when spots move long distances between frames. However, we assume that it should be enough for most super-resolution usages. Sample drift can be detected by phase only correlation (POC) or A-KAZE feature matching, which were tested with bright-field reference images. Super-resolved images are reconstructed by histogram binning method (plotting centroids on a blank image of magnified size).

tanitracer was named after **Daisuke Taniguchi**, who provided the core scripts implementing Gaussian fitting with subpixel correction, several candidate algorithms for spot tracking, and A-KAZE feature matching.

Usually, images are processed by the following scripts:
* `tanilacian.py` - test of LoG filter (optional)
* `tanifit.py` - determining parameters to detect fluorescent spots
* `tanitrace.py` - detection and tracking of fluorescent spots
* `tanipoc.py` or `tanialign.py` - calculation of sample drift (optional)
* `taniplot.py` - reconstruction of super-resolved images

Other scripts listed below help to process or analyze images:
* `tanimark.py` - drawing markers for detected spots (helper for figures)
* `frcplot.py` - making two divided super-resolved images for FRC analysis
* `firecalc.py` - calculates FRC curves and FIRE values from two images
* `fireheat.py` - making heat-maps of local FIRE values from two images

Algorithms are capsuled in the module files in `taniclass` and `taniext` folders, which include:
* `gaussian8.py` - Gaussian fitting of fluorescent spots
* `nnchaser.py` - spot tracking by *k*-nearest neighbor algorithm
* `spotplotter.py` - reconstruction of super-resolved images
* `spotfilter.py` - filtering and sorting of detected spots
* `spotmarker.py` - drawing markers for detected spots
* `akaze.py` - drift calculation by A-KAZE feature matching
* `poc.py` - drift calculation by POC (*)
* `firefrc.py` - calculation of FRC curves and FIRE values (**)

(*) originally implemented by [Daisuke Kobayashi](https://github.com/daisukekobayashi/phase-only-correlation)

(**) implemented by the author, but referred to the codes by [Sajid Ari](https://github.com/s-sajid-ali/FRC)

## Getting Started

### Requirements

**tanitracer** works on Python 3.6 (or later) and several libraries for numerical calculation and image processing. Installing **[Anaconda](https://www.anaconda.com/) (Python 3.6 version, 64-bit)** is a good choice since it prepares almost all requirements except for `OpenCV3-Python`.

* `Python 3.6 or later (64-bit recommended)`
* `argparse`
* `numpy`
* `pandas`
* `scipy`
* `scikit-image`
* `scikit-learn`
* `Pillow (PIL)`
* `matplotlib`
* `OpenCv3-Python` - required for A-KAZE feature matching
* `statmodels` - required for calculating FRC curves and FIRE values

Even with Anaconda, you have to install `OpenCv3-Python`. Recent Anaconda accepts the following command (often after many messages and long time):
```
conda install opencv
```

### Installation

Download the zip file from my [GitHub repository](https://github.com/takushim/tanitracer) and place all the files in an appropriate folder, for example, `C:\Users\[username]\tanitracer`. It is recommended to add the installed folder to PATH environment variable because you can run the script easily from the working folder. The library files (in `taniclass` and `taniext) is automatically found by the python interpreter as long as they are located in the folder of script files.

If you have installed [git](https://git-scm.com/), you can clone from my [GitHub repository](https://github.com/takushim/tanitracer) by:

```
git clone https://github.com/takushim/tanitracer.git
```

You can check the correct installation by showing the help messages:
```
tanitrace.py --help
```

## Usage

### Overview

**NOTE:** sample images will be uploaded after publication

**tanitracer** accepts time-lapse multipage (or single-page) TIFF and MetaMorph stack files. The following procedure is tested with 16-bit grayscale images, but should work with 8-bit and 32-bit grayscale images. RGB images are not basically accepted. The results of spot detection and drift calculation are saved in tab separated values (TSV) files.

Usually, images are processed in the following order:
1. Parameter optimization to detect single-molecule fluorescent spots
1. Detection of fluorescent spots and output to TSV files
1. Calculation of sample drift during acquisition
1. Reconstruction of a super-resolved image
1. Analysis of resolution by Fourier ring correlation (advanced)

Please see `--help` for options not explained in this document.

### Parameter optimization to detect single-molecule fluorescent spots

Appropriate detection of single-molecule fluorescent spots requires optimization of two parameters, sigma of LoG filter and threshold in Gaussian fitting. `tanifit.py` helps to optimize these parameters by processing the input image with different parameters. The output is a multipage TIFF, which is consisted of the first (or specified) frame from the input image, but markers are drawn to indicate the detection result with the given parameters.

`tanifit.py` is usually used in the following style:
```
tanifit.py -l 1.4 -T 0.005 0.1 0.001 input_images.tif
```
`-l 1.4` sets the sigma of LoG filter. The sigma is usually adjusted slightly smaller than the average diameter (in pixel) of fluorescent spots. `-T 0.005 0.1 0.001` steps up the threshold in Gaussian fitting from 0.005 to 0.1 by 0.001. If the output image is difficult to see, you can invert the lookup table (of output image) by `-i` option.

The effect of LoG filter can be checked by:
```
tanilacian.py -l 1.4 input_images.tif
```
which outputs the image processed by LoG filter at sigma = 1.4.

### Detection of fluorescent spots and output to TSV files

After optimizing the parameters, `tanitrace.py` processes the entire time-lapse image with given parameters. The result is output to a TSV file.

Given that sigma = 1.4 and threshold = 0.03, the command line should be:
```
tanitrace.py -l 1.4 -t 0.03 -C input_images.tif
```
which process the entire time-lapse image, and output the results to a TSV file. The filename of TSV file is automatically assigned replacing the extension of image file to ".txt" ("input_images.txt" in this case) unless otherwise specified. `-C` turns on tracking by *k*-nearest neighbor algorithm.

Under PowerShell, multiple files can be processed by:

```
foreach ($file in (get-item images/*.tif))
{
    tanitrace.py -l 1.4 -t 0.03 -C $file
}
```

**Note:** The result TSV files is output in the **current** folder, not the folder of images. Thus, you can output the result TSV files in a different folder from the image files by moving to another folder before running the command.

### Calculation of sample drift during acquisition

Third, calculate drift using reference images, such as bright field images taken at certain intervals. If you want to use phase only correlation, use:
```
tanipoc.py [path_to_reference_images]/*.tif
```
If you want A-KAZE feature matching, use:
```
tanialign.py [path_to_reference_images]/*.tif
```
These commands output the drift (in pixels) "align.txt" in the current folder. You can use wildcards to specify multiple images. Input images can be single-page TIFF, multipage TIFF, or their mixture. Images will be sorted in alphabetical order, and concatenated. You can use your own programs to calculate sample drift, but should be a TSV file containing at least three columns, "align_plane", "align_x", and "align_y". You can specify `-O` to check the alignment of sample drift.

### Reconstruction of a super-resolved image

Finally, reconstruct super-resolved images from the centroids of detected spots considering the drift of samples:
```
taniplot.py -X 8 -o output_image.tif -a align.txt -e 500 [path_to_results]/*.txt
```
`-X` and `-o` are the magnification and the name of output super-resolved image. `-a align.txt` specifies the name of alignment TSV file, and `-e 500` assumes that drift correction images are acquired every 500 frames of single-molecule images (i.e. 500-frame single-molecule image, 1-frame bright-field, 500-frame single-molecule image, 1-frame bright-field, and so on). **You have to use `-n` not to use drift correction**, or `-a align.txt -e 500` is implicitly specified.

### Analysis of resolution by Fourier ring correlation (advanced)

Please read the source file beforehand if you want to use `frcplot.py`, `firecalc.py`, `fireheat.py`.

`tanimark.py` puts markers of detected spots listed in the TSV file. This script is useful to adjust the contrast of single-molecule images beforehand (**and output to 8-bit**), and put markers on it. Helpful when you make figure images.

For example:
```
tanimark.py -f result.txt -z 4 -i -r images_8bit.tif
```
`-z 4` set the marker diameter to 4 pixels. `-i` invert the gray scale. `-r` uses rainbow colors for each set of tracking. If `-r` is not specified, beginning and end of tracking are drawn by red and blue circles, respectively. Other spots are drawn by orange circles.

`frcplot.py` reconstruct two super-resolved images dividing the TSV files into two groups.
```
frcplot.py -d 80 -X 8 -o output -a align.txt -e 500 [path_to_results]/*.txt
```
plots the first image from files #1-#40, #81-#120, #161-#200,... into "output_each80_1.tif" and the second image from files #41-#80, #121-#160, #201-#240,... into "output_each80_2.tif".

`firecalc.py` calculate the FRC curve and determine FIRE value from the two super-resolved files.
```
firecalc.py -m mask.tif output_each80_1.tif output_each80_2.tif
```
displays a FRC curve calculated from the two images. `-m` specifies the masking image. The masking image is converted to an array of TRUE and FALSE, and multiplied to the super-resolved images. Thus, the area of value 0 in the masking image is excluded from the calculation.

`fireheat.py` calculate local FIRE value from the two super-resolved files, and makes a heat map.
```
fireheat.py -m mask.tif output_each80_1.tif output_each80_2.tif
```

## Author

* **[Takushi Miyoshi](https://github.com/takushim)**


See also the list of [contributors](https://github.com/takushim/tanitracer/contributors) who participated in this project.

## License

This project is licensed under the BSD 3-clause licence except for phase only correlation script, `poc.py`, which was originally written by [Daisuke Kobayashi](https://github.com/daisukekobayashi/) and licensed under the Apache 2.0 license. The algorithm of `firefrc.py` was implemented referring to two scripts, `fourier_ring_corr.py` and `spin_average.py`, written by [Sajid Ari](https://github.com/s-sajid-ali/).

