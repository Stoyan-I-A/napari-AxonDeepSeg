from typing import TYPE_CHECKING

from pathlib import Path
import numpy as np
from qtpy.QtWidgets import QVBoxLayout, QPushButton, QWidget, QComboBox, QFileDialog
from qtpy.QtCore import QStringListModel

import AxonDeepSeg
from AxonDeepSeg import ads_utils, segment
from config import axonmyelin_suffix, axon_suffix, myelin_suffix

if TYPE_CHECKING:
    import napari


class ADSplugin(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        self.available_models = ads_utils.get_existing_models_list()
        self.model_selection_combobox = QComboBox()
        self.model_selection_combobox.addItems(["Select the model"] + self.available_models)

        apply_model_button = QPushButton("Apply ADS model")
        apply_model_button.clicked.connect(self._on_apply_model_button_click)

        fill_axons_button = QPushButton("Fill axons")
        compute_morphometrics_button = QPushButton("Compute morphometrics")

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.model_selection_combobox)
        self.layout().addWidget(apply_model_button)
        self.layout().addWidget(fill_axons_button)
        self.layout().addWidget(compute_morphometrics_button)


    def add_layer_pixel_size_to_metadata(self, layer):
        image_path = Path(layer.source.path)
        image_directory = image_path.parents[0]

        # Check if the pixel size txt file exist in the image_directory
        pixel_size_exists = (image_directory / "pixel_size_in_micrometer.txt").exists()

        if pixel_size_exists:
            resolution_file = open((image_directory / "pixel_size_in_micrometer.txt").__str__(), 'r')
            pixel_size_float = float(resolution_file.read())
            layer.metadata["pixel_size"] = pixel_size_float
            return True
        else:
            print("Couldn't find pixel size information")
            return False


    def _on_apply_model_button_click(self):
        selected_layers = self.viewer.layers.selection
        selected_model = self.model_selection_combobox.currentText()

        if selected_model not in self.available_models:
            return
        else:
            ads_path = Path(AxonDeepSeg.__file__).parents[0]
            model_path = ads_path / "models" / selected_model
        if len(selected_layers) != 1:
            return
        selected_layer = selected_layers.active
        image_directory = Path(selected_layer.source.path).parents[0]

        # Check if the pixel size txt file exist in the imageDirPath
        if "pixel_size" not in selected_layer.metadata.keys():
            if not self.add_layer_pixel_size_to_metadata(selected_layer):
                return # Couldn't find pixel size

        print(image_directory)
        print(model_path)

        try:
            segment.segment_image(
                path_testing_image=Path(selected_layer.source.path),
                path_model=model_path,
                overlap_value=[segment.default_overlap, segment.default_overlap],
                acquired_resolution=selected_layer.metadata["pixel_size"],
                zoom_factor=1.0,
                verbosity_level=3
            )
        except SystemExit as err:
            if err.code == 4:
                print(
                    "Resampled image smaller than model's patch size. Please take a look at your terminal "
                    "for the minimum zoom factor value to use (option available in the Settings menu)."
                )
            return

        image_name_no_extension = selected_layer.name
        axon_mask_path = image_directory / (image_name_no_extension + str(axon_suffix))
        myelin_mask_path = image_directory / (image_name_no_extension + str(myelin_suffix))

        axon_data = ads_utils.imread(axon_mask_path).astype(bool)
        self.viewer.add_labels(axon_data, color={1: 'blue'})
        myelin_data = ads_utils.imread(myelin_mask_path).astype(bool)
        self.viewer.add_labels(myelin_data, color={1: 'red'})
