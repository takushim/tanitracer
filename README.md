# tanitracer

A python script set for reconstructing and analyzing super-resolution images

## Introduction

**tanitracer** is a set of python scripts to detect fluorescent spots in single-molecule microscopy images, and to reconstruct super-resolved images from the centroids of detected spots. Single-molecule microscopy images are pre-processed by Gaussian-Laplacian filter and fluorescent spots are detected by Gaussian fitting with subpixel correction. Tracking is implemented by *k*-nearest neighbor algorhythm, which may not be possible when spots moves largely between frames, but will be sufficient for most tracking in super-resolution usages. **tanitracer** also includes scripts for drift correction (phase only correlation and A-KAZE algorhythms) and scripts to calculate Fourier image resolution (FIRE) by Fourier ring correlation (FRC) analysis.

**tanitracer** was named after **Daisuke Taniguchi**, who provided the author many useful scripts describing gaussian fitting, spot tracking, A-KAZE, etc.

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
* `akaze.py` - drift correction by A-KAZE algorhythm
* `poc.py` - drift correction by phase only correlation (*)
* `firefrc.py` - calculation of FRC curves and FIRE values (**)

(*) implemented by Daisuke Kobayashi (https://github.com/daisukekobayashi/phase-only-correlation)

(**) implemented by the author but referring to the codes by Sajid Ari (https://github.com/s-sajid-ali/FRC)

## Getting Started

### Prerequisites

**tanitracer** works on Python 3.6 and several libraries for numerical calculation and image processing including:

* `argparse`
* `numpy`
* `pandas`
* `scipy`
* `scikit-image`
* `scikit-learn`
* `Pillow (PIL)`
* `matplotlib`
* `Opencv3-Python` - for A-KAZE
* `statmodels` - for FRC and FIRE

Installing Anaconda (https://www.anaconda.com/) will provide most of the libraries above except for `Opencv3-Python`. Please make sure to install **64-bit python 3.6 version**. With recent Anaconda, `Opencv3-Python` can be installed by:
```
conda install opencv
```

### Installing

Download the zip file from GitHub ()

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc
