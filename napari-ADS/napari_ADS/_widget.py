from typing import TYPE_CHECKING

from pathlib import Path
import numpy as np
from qtpy.QtWidgets import QVBoxLayout, QPushButton, QWidget, QComboBox, QFileDialog, QLabel, QPlainTextEdit
from qtpy.QtCore import QStringListModel
from qtpy.QtGui import QPixmap

import AxonDeepSeg
from AxonDeepSeg import ads_utils, segment, postprocessing
from config import axonmyelin_suffix, axon_suffix, myelin_suffix

if TYPE_CHECKING:
    import napari


class ADSplugin(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        citation_textbox = QPlainTextEdit(self)
        citation_textbox.setPlainText(self.get_citation_string())
        citation_textbox.setReadOnly(True)
        citation_textbox.setMaximumHeight(100)

        hyperlink_label = QLabel()
        hyperlink_label.setOpenExternalLinks(True)
        hyperlink_label.setText(
            '<a href="https://axondeepseg.readthedocs.io/en/latest/">Need help? Read the documentation</a>')

        self.available_models = ads_utils.get_existing_models_list()
        self.model_selection_combobox = QComboBox()
        self.model_selection_combobox.addItems(["Select the model"] + self.available_models)

        apply_model_button = QPushButton("Apply ADS model")
        apply_model_button.clicked.connect(self._on_apply_model_button_click)

        fill_axons_button = QPushButton("Fill axons")
        fill_axons_button.clicked.connect(self._on_fill_axons_click)

        compute_morphometrics_button = QPushButton("Compute morphometrics")

        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(10)
        self.layout().setContentsMargins(10, 20, 20, 10)
        self.layout().addWidget(self.get_logo())
        self.layout().addWidget(citation_textbox)
        self.layout().addWidget(hyperlink_label)
        self.layout().addWidget(self.model_selection_combobox)
        self.layout().addWidget(apply_model_button)
        self.layout().addWidget(fill_axons_button)
        self.layout().addWidget(compute_morphometrics_button)
        self.layout().addStretch()


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


    def _on_fill_axons_click(self):
        axon_layer = self.get_axon_layer()
        myelin_layer = self.get_myelin_layer()

        if (axon_layer is None) or (myelin_layer is None):
            return

        myelin_array = np.array(myelin_layer.data, copy=True)
        axon_extracted_array = postprocessing.fill_myelin_holes(myelin_array)
        axon_array_indexes = np.where(axon_extracted_array > 0)
        axon_layer._save_history((axon_array_indexes,
                                  np.array(axon_layer.data[axon_array_indexes], copy=True),
                                  1))
        axon_layer.data[axon_array_indexes] = 1
        axon_layer.refresh()

    def get_axon_layer(self):
        #TODO: find a better way to find the layer
        for layer in self.viewer.layers:
            if layer.name == "axon_data":
                return layer
        return None

    def get_myelin_layer(self):
        #TODO: find a better way to find the layer
        for layer in self.viewer.layers:
            if layer.name == "myelin_data":
                return layer
        return None

    def get_logo(self):
        ads_path = Path(AxonDeepSeg.__file__).parents[0]
        logo_file = ads_path / "logo_ads-alpha_small.png"
        logo_label = QLabel(self)
        logo_pixmap = QPixmap(str(logo_file))
        logo_label.setPixmap(logo_pixmap)
        logo_label.resize(logo_pixmap.width(), logo_pixmap.height())
        return logo_label

    def get_citation_string(self):
        """
        This function returns the AxonDeepSeg paper citation.
        :return: The AxonDeepSeg citation
        :rtype: string
        """
        return (
            "If you use this work in your research, please cite it as follows: \n"
            "Zaimi, A., Wabartha, M., Herman, V., Antonsanti, P.-L., Perone, C. S., & Cohen-Adad, J. (2018). "
            "AxonDeepSeg: automatic axon and myelin segmentation from microscopy data using convolutional "
            "neural networks. Scientific Reports, 8(1), 3816. "
            "Link to paper: https://doi.org/10.1038/s41598-018-22181-4. \n"
            "Copyright (c) 2018 NeuroPoly (Polytechnique Montreal)"
        )
