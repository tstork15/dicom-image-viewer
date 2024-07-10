import tkinter as tk
from tkinter import filedialog
import os
from PIL import Image, ImageTk, ImageOps
import pydicom
import numpy as np

# Initialize global variables to store the slices and current index
slices_array = None
current_slice_index = 0

# Define preset values for CT and NM
preset_values = {
    'Soft Tissue': {'window_center': 50, 'window_width': 350},
    'Bone': {'window_center': 500, 'window_width': 2000},
    'Lung': {'window_center': -600, 'window_width': 1600},
    'Brain': {'window_center': 30, 'window_width': 70},
    'NM': {'window_center': 20, 'window_width': 80} # these values need to update based on the image, not be preset
}

def select_file_and_display_data():
    """
    Open a file dialog to select a DICOM file

    Inputs: None
    Outputs: None
    """
    global slices_array, current_slice_index
    # Open a file dialog to select a DICOM file and get its path
    file_path = filedialog.askopenfilename(title="Select DICOM file", filetypes=[("DICOM files", "*.dcm")])

    if file_path: # If a file is selected
        # Get the directory of the selected file
        folder_path = os.path.dirname(file_path)

        # Load the 3D image
        slices_array = get_image_from_dicom(folder_path)

        # Reset the current slice index
        current_slice_index = 0

        # Show initial slice
        show_slice(current_slice_index)

    else:
        # If no DICOM files are found in the directory
        # TODO: Insert a message indicating no DICOM files were found
        print("TODO: add error message stating no files are found in the directory")

def get_image_from_dicom(folder_path):
    """
    Convert DICOM pixel data to a PIL image.

    Inputs:
    folder_path: str

    Outputs:
    slices_array: np.array
    """
    # Get all DICOM files in the directory with full paths
    dicom_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith(".dcm")]

    dicom_slices = []

    if len(dicom_files) > 1:
        # If there are multiple DICOM files, assume they are slices of 1 image (like CT or PT)
        # Read the DICOM files and sort them by Instance Number
        for file in dicom_files:
            dicom_slice = pydicom.dcmread(file)
            dicom_slices.append(dicom_slice)

        # Sort slices by Instance Number or Slice Location
        dicom_slices.sort(key=lambda x: int(x.InstanceNumber))

        # Extract pixel data and apply the rescale slope/intercept if present, then stack into a 3D numpy array
        pixel_arrays = []
        for s in dicom_slices:
            # Extract pixel array
            pixel_array = s.pixel_array
            # Apply the rescale slope and intercept if present
            if 'RescaleSlope' in s and 'RescaleIntercept' in s:
                slope = s.RescaleSlope
                intercept = s.RescaleIntercept
                pixel_array = pixel_array * slope + intercept
            pixel_arrays.append(pixel_array)

        slices_array = np.stack(pixel_arrays, axis=-1)

    elif len(dicom_files) == 1:
        # If there's only one DICOM file, assume it's an entire image (like an NM)
        # Read the single DICOM file
        dicom_slices = pydicom.dcmread(dicom_files[0])

        # Extract the pixel array from the DICOM file
        slices_array = dicom_slices.pixel_array

        # Apply rescale slope and intercept if present
        if 'RescaleSlope' in dicom_slices and 'RescaleIntercept' in dicom_slices:
            slope = dicom_slices.RescaleSlope
            intercept = dicom_slices.RescaleIntercept
            slices_array = slices_array * slope + intercept

        # Swap axes to match the expected (x, y, z) format
        slices_array = np.transpose(slices_array, (1, 2, 0))

    return slices_array

def show_slice(index):
    """
    Show the slice at the given index on the canvas.

    Inputs:
    index: int
    """
    global slices_array
    # Get the slice at the specified index
    slice_array = slices_array[:, :, index]

    # Apply window and level adjustments using slider values
    window_center = window_center_slider.get()
    window_width = window_width_slider.get()
    slice_array = apply_window_level(slice_array, window_center, window_width)

    # Convert the pixel array to a PIL image
    image = Image.fromarray(slice_array)

    # Convert to grayscale (L mode)
    image = image.convert('L')

    # Resize the image to 512x512
    image = ImageOps.fit(image, (512, 512), Image.Resampling.LANCZOS)

    # Convert the PIL image to a PhotoImage object for Tkinter
    tk_image = ImageTk.PhotoImage(image)

    # Clear the canvas
    canvas.delete("all")

    # Calculate the center position
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    x_center = (canvas_width - 512) / 2
    y_center = (canvas_height - 512) / 2

    # Create an image item in the canvas at the center position
    canvas.create_image(x_center, y_center, anchor=tk.NW, image=tk_image)

    # Keep a reference to the image to prevent it from being garbage collected
    canvas.image = tk_image

def update_slice_on_scroll(event):
    """
    Update the slice displayed based on scroll direction.

    Inputs:
    event: tk.Event
    """
    global current_slice_index, slices_array
    # Update the current slice index based on scroll direction
    if event.delta > 0:
        current_slice_index = (current_slice_index - 1) % slices_array.shape[2]
    else:
        current_slice_index = (current_slice_index + 1) % slices_array.shape[2]

    # Show the updated slice
    show_slice(current_slice_index)

def apply_window_level(pixel_array, window_center, window_width):
    """
    Apply window and level adjustments to the pixel array.

    Inputs:
    pixel_array: np.array
    window_center: int
    window_width: int

    Outputs:
    adjusted_pixel_array: np.array
    """
    # Calculate minimum and maximum pixel values for the given window
    min_pixel_value = window_center - window_width / 2
    max_pixel_value = window_center + window_width / 2

    # Clip and scale the pixel values
    pixel_array = np.clip(pixel_array, min_pixel_value, max_pixel_value)
    pixel_array = ((pixel_array - min_pixel_value) / (max_pixel_value - min_pixel_value) * 255).astype(np.uint8)

    return pixel_array

def update_sliders_based_on_modality():
    """
    Update the window center and window width sliders based on the selected modality.
    """
    selected_modality = modality_var.get()
    if selected_modality in preset_values:
        window_center_slider.set(preset_values[selected_modality]['window_center'])
        window_width_slider.set(preset_values[selected_modality]['window_width'])

def on_slider_change(event=None):
    """
    Update the displayed image when the window center or window width slider is adjusted.
    """
    if slices_array is not None:
        show_slice(current_slice_index)

if __name__ == "__main__":
    root = tk.Tk()  # Create the main window
    root.title("DICOM Image Viewer")  # Set the window title

    frame = tk.Frame(root)  # Create a frame to hold the buttons and dropdown
    frame.pack(padx=10, pady=10)  # Add padding around the frame

    select_file_button = tk.Button(frame, text="Select DICOM File", command=select_file_and_display_data)  # Button to select a DICOM file
    select_file_button.pack(side=tk.LEFT, padx=5, pady=5)  # Pack the button with padding

    # Create an option menu for modality selection
    modality_var = tk.StringVar(value='Soft Tissue')  # Default value
    modality_menu = tk.OptionMenu(frame, modality_var, 'Soft Tissue', 'Bone', 'Lung', 'Brain','NM', command=lambda _: update_sliders_based_on_modality())
    modality_menu.pack(side=tk.LEFT, padx=5, pady=5)

    # Create a canvas to display the image
    canvas = tk.Canvas(root)
    canvas.pack(fill=tk.BOTH, expand=1)

    # Create sliders for window center and window width
    window_center_slider = tk.Scale(root, from_=-1000, to=2000, orient=tk.HORIZONTAL, label='Window Center', command=on_slider_change)
    window_center_slider.pack(fill=tk.X, padx=10, pady=5)

    window_width_slider = tk.Scale(root, from_=-1000, to=2000, orient=tk.HORIZONTAL, label='Window Width', command=on_slider_change)
    window_width_slider.pack(fill=tk.X, padx=10, pady=5)

    # Set initial values for the sliders based on default modality
    update_sliders_based_on_modality()

    # Bind the mouse scroll event to update the slice
    root.bind("<MouseWheel>", update_slice_on_scroll)

    # Redraw the image when the window is resized
    root.bind('<Configure>', lambda event: show_slice(current_slice_index) if slices_array is not None else None)

    # Set default window size
    root.geometry("800x700")  # Set the default size of the main window

    root.mainloop()  # Start the Tkinter main loop
