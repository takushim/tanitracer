# tanitracer

A python toolbox for semi-automatic single particle tracking (SPT) and reconstruction of super-resolution images. The python scripts in this toolbox were used in our paper, **Semi-automated single-molecule microscopy screening of fast-dissociating specific antibodies directly from hybridoma cultures**, [published in Cell Reports, 2021](https://pubmed.ncbi.nlm.nih.gov/33535030/).

**tanitracer** was named after **Daisuke Taniguchi**, who provided the core scripts implementing Gaussian fitting with subpixel correction and several candidate algorithms for spot tracking and image registration.

## Introduction

**tanitracer** is a set of python scripts for single particle tracking (SPT) and reconstruction of super-resolution images. In this document, basic usages of scripts are described using a 16-bit multi-page sample TIFF file, [testimage.tif](https://github.com/takushim/tanitracer/raw/main/testdata/testimage.tif).

These four scripts are for SPT of fluorescent spots:
* `tanilacian.py` - tests the pre-processing using the LoG filter
* `tanifit.py` - determines parameters to detect fluorescent spots
* `tanitrace.py` - tracks fluorescent spots
* `tanitime.py` - calculates regression rates or distribution of dwell times

These two scripts are to reconstruct super-resolution images:
* `tanipoc.py` or `taniakaze.py` - calculation of sample drift (optional)
* `taniplot.py` - reconstruction of super-resolved images

Other scripts help to process or analyze images:
* `tanimark.py` - drawing markers for detected spots (helper for figures)
* `frcplot.py` - making two divided super-resolved images for FRC analysis
* `firecalc.py` - calculates FRC curves and FIRE values from two images
* `fireheat.py` - making heat-maps of local FIRE values from two images

Algorithms are capsuled in the module files in `taniclass` and `taniext` folders:
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

First of all, install [ImageJ](https://imagej.nih.gov/ij/) or [Fiji](https://fiji.sc/) to check output images. Then, install Python 3.6 or later to run the python scripts in **tanitracer**. The 64-bit version is highly recommended. Required libraries are:
* `numpy`
* `pandas`
* `scipy`
* `scikit-image`
* `scikit-learn`
* `Pillow (PIL)`
* `matplotlib`
* `tifffile`
* `opencv-contrib-python` - for A-KAZE feature matching
* `statsmodels` - for calculating FRC curves and FIRE values

All of these libraries can be installed using `pip` by typing:
```
pip install numpy pandas scipy scikit-image scikit-learn pillow \
  matplotlib tifffile opencv-contrib-python statsmodels
```

**Note:** It is highly recommended to install these packages in [a virtual environment of python](https://docs.python.org/3/library/venv.html).

### Installation

Download the zip file from my [GitHub repository](https://github.com/takushim/tanitracer) and place all the files in an appropriate folder, for example, `C:\Users\[username]\tanitracer`. Add the installed folder to the `PATH` environment variable. The library files in `taniclass` and `taniext` folders are automatically found by the python interpreter as long as they are located in the folder of script files. If [git](https://git-scm.com/) is installed, my git repository can be cloned using the following commend:
```
git clone https://github.com/takushim/tanitracer.git
```

## Single particle tracking (SPT)

### Overview

Basic usages are described using a 16-bit multi-page sample TIFF file, [testimage.tif](https://github.com/takushim/tanitracer/raw/main/testdata/testimage.tif). The file contains time-lapse single-molecule microscopy images of fluorescently-labeled anti-FLAG tag Fab fragment probes (Fab probes) recognizing FLAG-tagged actin expressed in a *Xenopus* XTC cell. Bound Fab probes are frequently exchanged since the Fab probes are synthesized from our new reagent, **fast-dissociating, highly-specific antibody**.

The first frame of testimage.tif is shown below. Each white spot is an anti-FLAG tag Fab probe molecule recognizing FLAG-actin in the cell and a single particle to be tracked.

![testimage.tif](https://github.com/takushim/tanitracer/raw/main/images/testimage_raw.jpg)


### Parameter optimization

Download [testimage.tif](https://github.com/takushim/tanitracer/raw/main/testdata/testimage.tif) and place in an appropriate folder. In this tutorial, **I assume that we are in the folder where `testimage.tif` is placed**.

**Note:** Run each script with a `--help` option to see the options not explained in this document.

First, optimize the parameter of a LoG filter since **tanitracer** pre-process images using a LoG filter and then determine the centroids of fluorescent spots. Type the following command to see how images are pre-processed:
```
tanilacian.py -l 1.8 testimages.tif
```

Processed images are output in `testimages_log.tif` in the current folder. The first frame is shown below. Fluorescent spots are selectively enhanced. The parameter, `1.8`, was determined to be close to the radius of fluorescent spots because the LoG filter enhances objects with the diameters double of the given parameter. Empirically, better tracking can be achieved by setting the parameter slightly smaller than the radius of fluorescent spots. 

![testimage_log.jpg](https://github.com/takushim/tanitracer/raw/main/images/testimage_log.jpg)

Next, determine the threshold for Gaussian fitting. Type the following command:
```
tanifit.py -l 1.8 -T 0.01 0.1 0.001 -i -z 3 testimages.tif
```

For the first frame of `testimages.tif`, this script apply a LoG filter with a parameter, `1.8`, and then try to locate fluorescent spots using a Gaussian fitting algorithm. The option, `-T 0.01 0.1 0.001`, is to step up the threshold in Gaussian fitting from 0.01 to 0.1 by 0.001. The options, `-i` and `-z 3`, are to invert the lookup table of output image and to set the radius of markers, respectively.

The image below is a montage of three frames chosen from the output, `testimages_fit.tif`. In the left panel (threshold = 0.01), false spots are detected in almost all areas of the image. In the right panel (threshold = 0.1), many fluorescent spots are "missed". **The center panel (threshold = 0.03) seems to be the best.**

![testimage_fit.jpg](https://github.com/takushim/tanitracer/raw/main/images/testimage_fit.jpg)

### Particle tracking 

Finally, run the following command to track the fluorescent spots in `testimages.tif`:
```
tanitrace.py -l 1.8 -t 0.03 -C -O -z 3 -i -r testimages.tif
```

This script apply the LoG filter with the parameter of `1.8` and perform Gaussian fitting with the threshold of `0.03` for the entire frames of `testimages.tif`. The option, `-C`, turns on the tracking of spots using *k*-nearest neighbor algorithm. The option, `-O`, is to output an image file with markers on detected spots. The effect of options, `-i` and `-z 3`, are to invert the lookup table of output image and to set the radius of markers as described above. The option, `-r`, is to distinguish each tracking of spots using different colors.

Here is the first frame of output image:

![testimage_marked.jpg](https://github.com/takushim/tanitracer/raw/main/images/testimage_marked.jpg)

The list of detected spots (and tracking results) are output into **a TSV (tab separated values) file**. The TSV file for the demonstration above can be downloaded from [testimage.txt](https://github.com/takushim/tanitracer/raw/main/testdata/testimage.txt).

**Note:** The script, `tanitrace.py`, automatically converts input images into 8-bit images and draw markers on them. To improve the contrast of images, convert the input images into 8-bit by yourself and use `tanimark.py` to draw markers.


### Determination of "dissociation rates"

The TSV file output above with "tracking on" can be used to determine the dissociation rates of fluorescent probes from their targets. Both `regression from t = 0` and `distribution of dwell-time` can be calculated using the TSV file. Type the following command to output the regression from t = 0:
```
tanitime.py -x 0.05 testimage.txt
```

The option, `-x 0.05`, is set since the time-lapse images were acquired every 50 ms. An output TSV file can be downloaded from  [testimage_regression.txt](https://github.com/takushim/tanitracer/raw/main/testdata/testimage_regression.txt). Using an appropriate software, such as GraphPad Prism, a one-phase decay model can be fit to determine the "dissociation rate" as shown below. **Note that the curve below does not indicate the accurate dissociation rate of our Fab probe from their targets because the intervals of time-lapse images are not optimized. Determination of dissociation rates requires careful optimization of imaging condition and image processing parameters.**

![testimage_regression.jpg](https://github.com/takushim/tanitracer/raw/main/images/regression.jpg)


## Reconstruction of super-resolution images

### Preparation of test data

**Note: This section is under construction. Test data (very large) are going to be deposited at [Mendeley](https://www.mendeley.com/)**. 

In [our paper](https://pubmed.ncbi.nlm.nih.gov/33535030/), super-resolution images were reconstructed using the centroids of many fluorescent spots. The test data will be archived in the following tree:
```
testdata/   spots/  image001.stk
                    image002.stk
                    image003.stk
                    ...
                    image320.stk
            bf/     bf001.stk
                    bf002.stk
                    bf003.stk
                    ...
                    bf320.stk
```

These files are 320 pairs of a bright-field image, `bf*.stk`, and a 500-frame time-lapse single-molecule microscopy images, `image*.stk`, as described in the diagram below. The files, `image*.stk`, are 500-frame time-lapse single-molecule microscopy images (MetaMorph stacks) of our fast-dissociating anti-FLAG tag Fab fragment probes (Fab probes) recognizing FLAG-tagged actin expressed in a *Xenopus* XTC cell. The files, `bf*.stk`, are single-frame bright-field images acquired for drift correction. Each bright-field image was acquired before starting each time-lapse acquisition. 

![acquisition.jpg](https://github.com/takushim/tanitracer/raw/main/images/acquisition.jpg)

### Centroid determination for each fluorescent spot

First, open a **PowerShell** window and move to the `testdata` folder. Run the following commands sequentially to determine the centroids of fluorescent spots in the `image*.stk` files:
```
mkdir analysis
cd analysis
foreach ($i in ../spots/image*.stk) {tanitrace.py -l 1.8 -t 0.05 -C $i}
cd ..
```

These commands will make a folder to store output TSV files, `analysis`, and detect fluorescent spots in each `image*.stk` file. The options, `-l 1.8` and `-t 0.05`, are determined using the procedure described in the SPT section. The threshold was slightly elevated to `0.05` to suppress noise. The option, `-C`, is not always necessary to reconstruct super-resolution images but specified here since tracking information might be used in the future. Options to output images are not necessary.

A **bash** user may prefer running the following commands:
```
mkdir analysis
cd analysis
for i in ../spots/image*.stk; do tanitrace.py -l 1.8 -t 0.05 -C $i; done
cd ..
```

### Correction of sample drifting

Next, calculate sample drifting during the acquisition by running the following command in the `testdata` folder:
```
tanipoc.py bf/*.stk
```

This script concatenate the image files specified as the arguments and compare each image with the first image. Sample drifts are calculated using a phase-only-correlation (POC) algorithm and output the results in a TSV file, `align.txt`. Empirically, the POC algorithm works well with images with some bright structures, such as bright-field images of *Xenopus* XTC cells shown below. Another script, `taniakaze.py`, using an AKAZE feature matching algorithm seems to be better for samples with a more complicated structure.

![bf.jpg](https://github.com/takushim/tanitracer/raw/main/images/bf.jpg)

### Reconstruction of super-resolution images

Finally, reconstruct a super-resolution images using the TSV files in the `analysis` folder listing the centroids of fluorescent spots and `align.txt` recording the sample drifting during the acquisition. Run the following command:

```
taniplot.py -X 4 analysis/*.txt
```

The centroids in the TSV files are plotted on a blank image. The option, `-X`, specifies the magnification to the original images. The script automatically find `align.txt` in the current folder and correct sample drifting using each line for every 500 frames. The final super-resolution image of FLAG-actin is shown below.

![testimage_plot.jpg](https://github.com/takushim/tanitracer/raw/main/images/testimage_plot.jpg)

## Analysis of resolution by Fourier ring correlation (TL;DR)

**Note:** The analysis in this section is not required for regular use. Usages are explained very briefly. Please read the source files before use.

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

This project is licensed under the MIT license except for phase only correlation script, `poc.py`, which was originally written by [Daisuke Kobayashi](https://github.com/daisukekobayashi/) and licensed under the Apache 2.0 license. The algorithm of `firefrc.py` was implemented referring to two scripts, `fourier_ring_corr.py` and `spin_average.py`, written by [Sajid Ari](https://github.com/s-sajid-ali/).

