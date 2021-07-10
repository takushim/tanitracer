# tanitracer

A python toolbox for semi-automatic single particle tracking (SPT) and reconstruction of super-resolution images. The python scripts in this toolbox were used in our paper, **Semi-automated single-molecule microscopy screening of fast-dissociating specific antibodies directly from hybridoma cultures**, [published in Cell Reports, 2021](https://pubmed.ncbi.nlm.nih.gov/33535030/).

**tanitracer** was named after **Daisuke Taniguchi**, who provided the core scripts implementing Gaussian fitting with subpixel correction and several candidate algorithms for spot tracking and image registration.

## Introduction

**tanitracer** is a set of pytho scripts for single particle tracking and resonstruction of super-resolution images. In this document, basic usages of the scripts are described using a 16-bit multi-page sample TIFF file, [testimage.tif](https://github.com/takushim/tanitracer/raw/master/testdata/testimage.tif). The file contains time-lapse single-molecule microscopy images of fluorescently-labeled anti-FLAG tag Fab fragment probes (Fab probes) recognizing FLAG-tagged actin expressed in a *Xenopus* XTC cell. Bound Fab probes are frequently exchanged since the Fab probes are synthesized from our new reagent, **fast-dissociting, highly-specific antibody**.


![The first frame of testimage.tif](https://github.com/takushim/tanitracer/raw/master/images/testimage_raw.jpg)



Usually, images are processed by the following scripts:
* `tanilacian.py` - testing the pre-processing by LoG filter (optional)
* `tanifit.py` - determining parameters to detect fluorescent spots
* `tanitrace.py` - detection and tracking of fluorescent spots
* `tanipoc.py` or `taniakaze.py` - calculation of sample drift (optional)
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

**tanitracer** works on Python 3.6 (or later) and several libraries for numerical calculation and image processing. Installing **[Anaconda](https://www.anaconda.com/) (Python 3.6 version, 64-bit)** is a good choice since it contains almost all requirements except for `OpenCV3-Python`.

* `Python 3.6 or later (64-bit recommended)`
* `argparse`
* `numpy`
* `pandas`
* `scipy`
* `scikit-image`
* `scikit-learn`
* `Pillow (PIL)`
* `matplotlib`
* `tifffile` - Added 07/23/2020 since tifffile module in scikit-image was deplicated 
* `OpenCv3-Python` - required for A-KAZE feature matching
* `statsmodels` - required for calculating FRC curves and FIRE values

Even with Anaconda, you have to install `OpenCv3-Python`. Recent Anaconda accepts the following command (often after many messages and long time):
```
conda install opencv
```

### Installation

Download the zip file from my [GitHub repository](https://github.com/takushim/tanitracer) and place all the files in an appropriate folder, for example, `C:\Users\[username]\tanitracer`. It is recommended to add the installed folder to PATH environment variable because you can run the script easily from the working folders. The library files (in `taniclass` and `taniext`) are automatically found by the python interpreter as long as they are located in the folder of script files.

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
1. Calculation of sample drift during acquisition (optional)
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

**Optional:** The effect of pre-processing by LoG filter can be checked as:
```
tanilacian.py -l 1.4 input_images.tif
```
which outputs the image processed by LoG filter at sigma = 1.4. The output filename is `[basename]_log.tif` ("input_images_log.tif" in this case).

### Detection of fluorescent spots and output to TSV files

After optimizing the parameters, `tanitrace.py` processes the entire time-lapse image with given parameters. The result is output to a TSV file.

Given that sigma = 1.4 and threshold = 0.03, the command line should be:
```
tanitrace.py -l 1.4 -t 0.03 -C input_images.tif
```
which process the entire time-lapse image, and output the results to a TSV file. The filename of TSV file is automatically assigned replacing the extension of image file to `.txt` ("input_images.txt" in this case) unless otherwise specified. `-C` turns on tracking by *k*-nearest neighbor algorithm, which is useful for calculating lifetimes of spots or for detecting spots that remain for several frames.

**Note:** You can check the detection using `-O` option. It outputs an RGB (multipage) TIFF file which is consisted of original single-molecule images with markers of detected spots. The output filename is `[basename]_marked.tif` ("input_images_marked.tif" in this case). The original images are converted to 8-bit images to make RGB images. If you want to mark the spots on other images (for example, images converted to 8-bit or RGB by yourself), use `tanimark.py`.

This script accepts one image file. Thus, processing multiple files requires help from shells. For example, PowerShell can process multiple files by:

```
foreach ($file in (get-item images/*.tif))
{
    tanitrace.py -l 1.4 -t 0.03 -C $file
}
```

**Note:** The result TSV files are output in the **current** folder. You can prepare a folder for analysis, move to the folder, and then output TSV files into the folder.

### Calculation of sample drift during acquisition (optional)

**Note:** The step can be skipped if sample drift is ignorable.

`tanipoc.py` and `taniakaze.py` calculate the drift of samples using a series of bright-field images inserted periodically during the acquisition of single-molecule images. Each frame is compared to the first frame to detect the drift. Although these scripts were tested with bright-field images, they may work with grayscale fluorescent images. If the bright field images contain some bright structures (such as nucleoli), `tanipoc.py` is better with its phase-only correlation. If the bright-field images are a complex structure (such as frozen tissue sections), `taniakaze.py` is better with its A-KAZE feature matching. These scripts were tested with bright-field images, but can accept fluorescent images.

The input images are a series of single-page TIFF files, multipage TIFF, files, MetaMorph stacks, or their mixtures. Wild-card characters (`*`, `?`, or other expressions that your shell accepts) are available to specify multiple files. The files are sorted in the lexical order, and concatenated before processing.

Usual commands are:
```
tanipoc.py [path_to_bright_field_images]/*.tif
```
or
```
tanialign.py [path_to_bright_field_images]/*.tif
```
The output is a TSV file with a name of `align.txt` if not specified. You can output the aligned images with `-O` option. The output filename is `[basename_of_the_first_file]_poc.tif` or `[basename_of_the_first_file]_akaze.tif` (for example, "bright_field_00_poc.tif"). A external image can be specified as the reference using `-r` option.

**Note:** You can use your own programs to calculate sample drift, but the result should be a TSV file containing three columns, `align_plane`, `align_x`, and `align_y`.

### Reconstruction of a super-resolved images

`taniplot.py` reads the TSV files listing the centroids of detected fluorescent spots, and plot them in a one-frame image (histogram binning method). Wild-card characters (`*`, `?`, or other expressions that your shell accepts) to specify multiple TSV files, which were sorted in the lexical order before reconstructing the image.

**Important note:** This script _automatically_ reads `align.txt` for drift correction, and assumes that each bright field images is inserted every _500 frames_ of time-lapse single-molecule images. Use `-n` option to turn off drift correction. `-e` can change the interval to apply drift correction.

Typical command lines are:
```
taniplot.py -X 8 [path_to_tsv_files]/*.txt
```
or
```
taniplot.py -X 8 -a drift.txt -e 1000 [path_to_tsv_files]/*.txt
```
or
```
taniplot.py -X 8 -n [path_to_tsv_files]/*.txt
```
The output file name is given as `plot_2019-09-01_09-30-00.tif` using the current date and time if not specified. `-X` specifies the magnification to the original single-molecule images. The first command automatically read `align.txt`, and use the drift in each line for each set of 500 frames. The second line reads the TSV file, `drift.txt`, and applies drift correction every 1000 frames. The third command does not use drift correction.

### Analysis of resolution by Fourier ring correlation (advanced)

**Note:** The analysis in this section is not required for reconstructing super-resolution images. Usages are explained very briefly. Please read the source files before you run the scripts.

`frcplot.py` reconstruct two super-resolved images dividing the TSV files into two groups.
```
frcplot.py -d 80 -X 8 [path_to_results]/*.txt
```
`-d` specifies the size of grouping. In this case, files are divided into groups of 80 files, and then each group is divided into two groups (40 files to group #1 and 40 files to group #2). Two super-resolved images are reconstructed from the files divided into group #1 and those divided into group #2, respectively. The filenames of two images are `plot_eachXX_1.tif` and `plot_eachXX_2.tif`. Drift correction is performed similarly to `taniplot.py` reading `align.txt` and applying the drift of each line to each set of 500 frames.

`firecalc.py` calculate the FRC curve and determine FIRE value from the two super-resolved files.
```
firecalc.py -m mask.tif output_each80_1.tif output_each80_2.tif
```
displays a FRC curve calculated from the two divided images. `-m` specifies the masking image. The masking image is converted to an array of TRUE and FALSE, and multiplied to the super-resolved images. Thus, the area of value 0 in the masking image is excluded from the calculation.

`fireheat.py` calculate local FIRE value from the two super-resolved files, and makes a heat map.
```
fireheat.py -m mask.tif output_each80_1.tif output_each80_2.tif
```

## Author

* **[Takushi Miyoshi](https://github.com/takushim)**


See also the list of [contributors](https://github.com/takushim/tanitracer/contributors) who participated in this project.

## License

This project is licensed under the BSD 3-clause licence except for phase only correlation script, `poc.py`, which was originally written by [Daisuke Kobayashi](https://github.com/daisukekobayashi/) and licensed under the Apache 2.0 license. The algorithm of `firefrc.py` was implemented referring to two scripts, `fourier_ring_corr.py` and `spin_average.py`, written by [Sajid Ari](https://github.com/s-sajid-ali/).

