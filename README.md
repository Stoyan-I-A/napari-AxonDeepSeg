# napari-AxonDeepSeg (Work in progress)
A (work in progress) plugin for napari that implements the AxonDeepSeg tools


## Instructions to install the plugin

1. Clone the [AxonDeepSeg repo](https://github.com/axondeepseg/axondeepseg).
2. In the AxonDeepSeg repo, open the environment.yml file and change the fsleyes requirement to napari. Save the file.
3. Follow the [instructions](https://axondeepseg.readthedocs.io/en/latest/) of the AxonDeepSeg installation documentation.
4. Clone this repo:

```
git clone https://github.com/neuropoly/axondeepseg.git
```
5. Get to the napari-ADS folder:
```
cd napari-plugin
cd napari-ADS
```
6. While the conda environment in which you installed AxonDeepSeg is active, use this command to install the plugin:
```
pip install -e .
```
7. Open napari:
```
napari
```
8. The plugin should appear in the plugins tab
