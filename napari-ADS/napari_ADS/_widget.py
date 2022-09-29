from typing import TYPE_CHECKING

from qtpy.QtWidgets import QVBoxLayout, QPushButton, QWidget, QComboBox

if TYPE_CHECKING:
    import napari


class ADSplugin(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        load_image_button = QPushButton("Load image")
        load_image_button.clicked.connect(self._on_load_image_button_click)

        model_selection_combobox = QComboBox()
        model_selection_combobox.addItems(["Select the model","SEM", "TEM", "BF"])

        apply_model_button = QPushButton("Apply ADS model")
        fill_axons_button = QPushButton("Fill axons")
        compute_morphometrics_button = QPushButton("Compute morphometrics")

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(load_image_button)
        self.layout().addWidget(model_selection_combobox)
        self.layout().addWidget(apply_model_button)
        self.layout().addWidget(fill_axons_button)
        self.layout().addWidget(compute_morphometrics_button)

    def _on_load_image_button_click(self):
        # Change the path of the image to load it in Napari
        self.viewer.open("C:/Users/Stoyan/Desktop/ADS/ads_with_napari/axondeepseg"
                    "/AxonDeepSeg/models/model_seg_rat_axon-myelin_sem/data_test/image.png")
        pass
