# tanitracer

A python script set for reconstructing and analyzing super-resolution images

## Introduction

**tanitracer** is a set of python scripts that accepts (Multipage) TIFF files (or MetaMorph stack files) containing fluorescent spots of single-molecule microscopy images. It include script files to detect the fluorescent spots, and to reconstruct super-resolved images from the centroids of detected spots. Single-molecule microscopy images are pre-processed by Gaussian-Laplacian filter and fluorescent spots are detected by Gaussian fitting with subpixel correction. Tracking is implemented by *k*-nearest neighbor algorhythm, which may not be possible when spots moves largely between frames, but will be sufficient for most tracking in super-resolution usages. **tanitracer** also includes scripts for drift correction (phase only correlation and A-KAZE algorhythms) and scripts to calculate  Fourier ring correlation (FRC) curves and Fourier image resolution (FIRE) values.

**tanitracer** was named after **Daisuke Taniguchi**, who provided the core scripts implementing Gaussian fitting with subpixel correction, spot tracking, A-KAZE feature matching, etc.

Usual reconstruction process is in the following order:
1. `tanifit.py` - determining parameters to detect fluorescent spots
1. `tanitrace.py` - detection and tracking of fluorescent spots
1. `tanipoc.py` or `tanialign.py` - drift correction using bright field images
1. `taniplot.py` - reconstruction of super-resolved images

Other scripts will help process or analyze images:
* `tanilacian.py` - checks the effect of Gaussian-Laplacian filter
* `tanimark.py` - plots markers of detected spots, helper for figures
* `frcplot.py` - makes two super-resolved images for FRC analysis
* `firecalc.py` - calculates FRC curves and FIRE values from two images
* `fireheat.py` - calculates local FIRE values and makes heatmaps

Algorhythms are implemented in the library files at `taniclass` and `taniext` folders, which include:
* `gaussian8.py` - gaussian fitting of fluorescent spots
* `nnchaser.py` - tracking by *k*-nearest neighbor algorhythm
* `spotplotter.py` - reconstructin of super-resolved images
* `spotfilter.py` - filtering and sorting of detected spots
* `spotmarker.py` - putting markers for detected spots
* `akaze.py` - drift calculation by A-KAZE algorhythm
* `poc.py` - drift calculation by phase only correlation (*)
* `firefrc.py` - calculation of FRC curves and FIRE values (**)

(*) implemented by [Daisuke Kobayashi](https://github.com/daisukekobayashi/phase-only-correlation)

(**) implemented by the author referring to the codes by [Sajid Ari](https://github.com/s-sajid-ali/FRC)

## Required environment

**tanitracer** works on Python 3.6 and several libraries for numerical calculation and image processing including:

* `argparse`
* `numpy`
* `pandas`
* `scipy`
* `scikit-image`
* `scikit-learn`
* `Pillow (PIL)`
* `matplotlib`
* `OpenCv3-Python` - required for A-KAZE drift calculation
* `statmodels` - required for FRC and FIRE

Installing [Anaconda](https://www.anaconda.com/) will provide most of the libraries above except for `OpenCv3-Python`. Please make sure to install **64-bit python 3.6 version**. With recent Anaconda, `OpenCv3-Python` can be installed by:
```
conda install opencv
```

## Installation

Download the zip file from my [GitHub repository](https://github.com/takushim/tanitracer) and place all the files in an appropriate folder, for example, `C:\Users\[username]\tanitracer`. Add the installed folder to the PATH enviroment variable. If correctly installed, you will get the help messages of `tanitrace.py` by:
```
tanitrace.py --help
```

If you have installed [git](https://git-scm.com/), you can clone from my [GitHub repository](https://github.com/takushim/tanitracer) by:

```
git clone https://github.com/takushim/tanitracer.git
```


## Usage of main scripts

The following instruction demonstrates representative usage of **tanitracer**. Scripts have many undescribed options. Please use ``--help`` option to see all options. **Images should be 16-bit or 8-bit (multipage) TIFF files (or MetaMorph stack files)**.

First, run `tanifit.py` for a representative (multipage) TIFF file (or MetaMorph stack) of single-molecule microscopy. This script uses the first page of the TIFF file, and try to detect fluorescent spots in the range of specified parameters.

For example:
```
tanifit.py -l 1.4 -T 0.005 0.1 0.001 -z 3 -i spot_images.tif
```
`-l 1.4` option applies Gauccian-Laplacian filter at sigma = 1.4. You will need to adjust sigma near the average pixel diameter of fluorescent spots. Fitting seems to be better if sigma is slightly smaller than the average pixel diameter. `-T 0.001 0.1 0.001` increase the threshold in gaussian fitting from 0.005 to 0.1 by 0.001 interval. `-z 3` specify the size of markers. `-i` invert the image intensity. You can use `tanilacian.py` to check the effect of Gauccian-Laplacian filter as:
```
tanilacian.py -l 1.4 spot_images.tif
```

Second, run `tanitracer.py` to detect fluorescent spots. This detect fluorescnt spots in the all pages of input image file. Specify the parameters determined above. The result is output to a tab separated (TSV) file.
```
tanitrace.py -l 1.4 -t 0.03 -C spot_images.tif
```
`-l 1.4` and `-t 0.03` specify the parameters in Gauccian-Laplacian filter and gaussian fitting, respectively. Please make sure to use `-t` in small letter. `-C` turns on tracking of fluorescent spots between frames. The name of result file is automatically assigned by replacing the ".tif" or ".stk" of the image file to ".txt" ("spot_images.txt" in this case) unless specified. You can output the image with markers on the detected spots by `-O` option (the name of output image is automatically assigned to "spot_images_marked.tif" unless specified).

If you are using PowerShell, you can apply the command to all files as:
```
ls [image_folder]/*.tif | foreach {tanitrace.py -l 1.4 -t 0.03 -C $_.fullname}
```
or
```
foreach ($file in (get-item [image_folder]/*.tif))
{
    tanitrace.py -l 1.4 -t 0.03 -C $file
}
```
Result TSV files are output in the **current** folder, not the folder of images. You can separate the result files from the image files by moving to the different folder to run the command beforehand.

Third, calculate drift using reference images, such as bright field images taken at certain intervals. If you want to use phase only correlation, use:
```
tanipoc.py [path_to_reference_images]/*.tif
```
If you want A-KAZE feature matching, use:
```
tanialign.py [path_to_reference_images]/*.tif
```
These commands output the drift (in pixels) "align.txt" in the current folder. You can use wildcards to specify multiple images. Input images can be single-page TIFF, multipage TIFF, or their mixture. Images will be sorted in alphabetical order, and concatenated. You can use your own programs to calculate sample drift, but should be a TSV file containing at least three culumns, "align_plane", "align_x", and "align_y". You can specify `-O` to check the alignment of sample drift.

Finally, reconstruct super-resolved images from the centroids of detected spots considering the drift of samples:
```
taniplot.py -X 8 -o output_image.tif -a align.txt -e 500 [path_to_results]/*.txt
```
`-X` and `-o` are the magnification and the name of output super-resolved image. `-a align.txt` specifies the name of alignment TSV file, and `-e 500` assumes that drift correction images are acquired every 500 frames of single-molecule images (i.e. 500-frame single-molecue image, 1-frame bright-field, 500-frame single-molecue image, 1-frame bright-field, and so on). **You have to use `-n` not to use drift correction**, or `-a align.txt -e 500` is implicitly specified.

## Usage of other scripts

Please read the source file beforehand if you want to use `frcplot.py`, `firecalc.py`, `fireheat.py`.

`tanimark.py` puts markers of detected spots listed in the TSV file. This script is useful to adjust the contrast of single-molecule images beforehand (**and output to 8-bit**), and put markers on it. Helpful when you make figure images.

For example:
```
tanimark.py -f result.txt -z 4 -i -r images_8bit.tif
```
`-z 4` set the marker diameter to 4 pixels. `-i` invert the grayscale. `-r` uses rainbow colors for each set of tracking. If `-r` is not specified, beginning and end of tracking are drawn by red and blue circles, respectively. Other spots are drawn by orange circles.

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

`fireheat.py` calculate local FIRE value from the two super-resolved files, and makes a heatmap.
```
fireheat.py -m mask.tif output_each80_1.tif output_each80_2.tif
```

## Author

* **[Takushi Miyoshi](https://github.com/takushim)**

See also the list of [contributors](https://github.com/takushim/tanitracer/contributors) who participated in this project.

## License

This project is licensed under the BSD 3-clause licence. `poc.py` is originally written by [Daisuke Kobayashi](https://github.com/daisukekobayashi/) and licenced under the Apache 2.0 license. `firefrc.py` is written by [Takushi Miyoshi](https://github.com/takushim) and licensed under the BSD 3-clause licence, but the algorhythm was originally implemented by [Sajid Ari](https://github.com/s-sajid-ali/).

