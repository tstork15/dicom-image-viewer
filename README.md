# DICOM Image Viewer
![dicom-image-viewer](https://github.com/user-attachments/assets/042733c0-f3bf-4613-8442-be63480e0980)


## Overview
The DICOM Image Viewer is a utility for viewing the pixel data of DICOM files. It provides a graphical user interface (GUI) using `tkinter` to select and display DICOM files.

## Features
- **File Selection**: Easily select a DICOM file from a directory using the GUI.
- **Preload Additional Files**: Additional DICOM files in the same directory (e.g., CT slices) will be loaded into a 3D array to easily switch between slices.
- **Navigation**: Navigate through image slices using a scrollbar or mouse wheel.
- **Window Center and Width**: Adjust window center and window width using sliders, preset values, based on DICOM, or based on the maximum pixel value.

## Requirements
- Python 3.x
- numpy
- pydicom
- Pillow

## Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/tstork15/dicom-image-viewer.git
    cd dicom-image-viewer
    ```
2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage
1. Run the `dicomImageViewer.py` script:
    ```bash
    python dicomImageViewer.py
    ```
2. Use the "Select DICOM File" button to open a file dialog and select a DICOM file.
3. View the DICOM pixel data.
4. Update the window center/width via the menu or the sliders.
5. Scroll to other slices.
