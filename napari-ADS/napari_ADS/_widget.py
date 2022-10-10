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

        load_image_button = QPushButton("Load image")
        load_image_button.clicked.connect(self._on_load_image_button_click)

        self.available_models = ads_utils.get_existing_models_list()
        self.model_selection_combobox = QComboBox()
        self.model_selection_combobox.addItems(["Select the model"] + self.available_models)

        apply_model_button = QPushButton("Apply ADS model")
        apply_model_button.clicked.connect(self._on_apply_model_button_click)

        fill_axons_button = QPushButton("Fill axons")
        compute_morphometrics_button = QPushButton("Compute morphometrics")

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(load_image_button)
        self.layout().addWidget(self.model_selection_combobox)
        self.layout().addWidget(apply_model_button)
        self.layout().addWidget(fill_axons_button)
        self.layout().addWidget(compute_morphometrics_button)

    def _on_load_image_button_click(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)  #TODO: only allow image file
        file_path = None

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]

        if file_path is None:
            return

        #TODO: make sure the file is an image file
        # image_data = ads_utils.imread(file_path)
        # self.viewer.add_image(image_data, name="TODO")
        self.viewer.open(file_path)
        self.viewer.layers[-1].metadata["file_path"] = file_path # TODO: test this with multiple images opened
        #TODO: add the pixel size to the metadata
        pass

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
        if "file_path" in selected_layer.metadata:
            image_path = Path(selected_layer.metadata["file_path"])
        else:
            return

        image_directory = image_path.parents[0]

        # Check if the pixel size txt file exist in the imageDirPath
        pixel_size_exists = (image_directory / "pixel_size_in_micrometer.txt").exists()

        if pixel_size_exists:
            resolution_file = open((image_directory / "pixel_size_in_micrometer.txt").__str__(), 'r')
            pixel_size_float = float(resolution_file.read())
        else:
            print("Couldn't find pixel size information")
            return

        try:
            segment.segment_image(
                path_testing_image=image_path,
                path_model=model_path,
                overlap_value=[segment.default_overlap, segment.default_overlap],
                acquired_resolution=pixel_size_float,
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

        image_name_no_extension = image_path.stem
        axon_mask_path = image_directory / (image_name_no_extension + str(axon_suffix))
        myelin_mask_path = image_directory / (image_name_no_extension + str(myelin_suffix))

        #TODO: change the colors
        axon_data = ads_utils.imread(axon_mask_path).astype(bool)
        self.viewer.add_labels(axon_data, seed=0.42)
        myelin_data = ads_utils.imread(myelin_mask_path).astype(bool)
        self.viewer.add_labels(myelin_data, seed=0.5)
