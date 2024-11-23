import tkinter as tk
from tkinter import filedialog
import os
from PIL import Image, ImageTk, ImageOps
import pydicom
import numpy as np

# Initialize global variables to store the slices, current index, scrollbar, and modality
slices_array = None
current_slice_index = 0
scrollbar = None
modality = None

# Define preset values for CT and Functional
preset_values = {
    'Soft Tissue': {'window_center': 50, 'window_width': 350},
    'Bone': {'window_center': 500, 'window_width': 2000},
    'Lung': {'window_center': -600, 'window_width': 1600},
    'Auto': {'window_center': 0, 'window_width': 1},  # these values need to update based on the image, not be preset
    'DICOM': {'window_center': 0, 'window_width': 1}  # these values need to update based on the image, not be preset
}
preset_names = ['Soft Tissue', 'Bone', 'Lung', 'Auto', 'DICOM']


def select_file_and_display_data():
    """
    Open a file dialog to select a DICOM file

    Inputs: None
    Outputs: None
    """
    global slices_array, current_slice_index, modality
    # Open a file dialog to select a DICOM file and get its path
    file_path = filedialog.askopenfilename(title="Select DICOM file", filetypes=[("DICOM files", "*.dcm")])

    # Read the modality from the selected DICOM file
    ds = pydicom.read_file(file_path)
    modality = ds.Modality
    try:
        window_width = ds.WindowWidth
    except:
        window_width = [350]
        #TODO: appropriately handle missing window width and center
    try:
        window_center = ds.WindowCenter
    except:
        window_center = [50]

    if file_path:  # If a file is selected
        # Get the directory of the selected file
        folder_path = os.path.dirname(file_path)

        # Load the 3D image
        slices_array = get_image_from_dicom(folder_path)

        # Reset the current slice index
        current_slice_index = 0

        # Configure scrollbar
        scrollbar.config(from_=0, to=slices_array.shape[2] - 1)
        scrollbar.set(0)

        # Show initial slice
        show_slice(current_slice_index)

        # Update window width and center drop down based on modality
        update_default_dropdown(modality, window_width, window_center)

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
        if current_slice_index > 0:
            current_slice_index -= 1
    else:
        if current_slice_index < slices_array.shape[2] - 1:
            current_slice_index += 1

    # Show the updated slice
    show_slice(current_slice_index)

    # Update the scrollbar to reflect the current slice
    scrollbar.set(current_slice_index)


def update_slice_on_scrollbar(value):
    """
    Update the slice displayed based on scrollbar position.

    Inputs:
    value: int
    """
    global current_slice_index, slices_array
    # Update the current slice index based on scrollbar position
    current_slice_index = int(value)

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
    pixel_array: np.array
    """
    # Calculate minimum and maximum pixel values for the given window
    min_pixel_value = window_center - window_width / 2
    max_pixel_value = window_center + window_width / 2

    # Clip and scale the pixel values
    pixel_array = np.clip(pixel_array, min_pixel_value, max_pixel_value)
    pixel_array = ((pixel_array - min_pixel_value) / (max_pixel_value - min_pixel_value) * 255).astype(np.uint8)

    return pixel_array


def update_sliders_based_on_dropdown():
    """
    Update the window center and window width sliders based on the selected dropdown.
    """
    selected_dropdown = dropdown_var.get()
    if selected_dropdown in preset_values:
        # Set the window center and width sliders to the preset values
        window_center_slider.set(preset_values[selected_dropdown]['window_center'])
        window_width_slider.set(preset_values[selected_dropdown]['window_width'])


def update_default_dropdown(modality, dicom_window_width, dicom_window_center):
    """
    Automatically set the default dropdown for window width and center based on the DICOM modality.

    Inputs:
    modality: str - the modality of the DICOM file (e.g., 'CT', 'NM')

    Outputs: None
    """
    max_pixel_value = slices_array.max()

    # update the preset values for 'Auto'
    auto_width = max_pixel_value * 0.6
    auto_center = auto_width / 2
    preset_values['Auto'] = {'window_center': auto_center, 'window_width': auto_width}

    # update the preset values for 'DICOM'
    if dicom_window_width and dicom_window_center:
        preset_values['DICOM'] = {'window_center': dicom_window_center, 'window_width': dicom_window_width}

    if modality in 'CT':
        new_dropdown = 'Soft Tissue'

        # Update slider ranges based on pixel data
        window_center_slider.config(from_=-1024, to=max_pixel_value)
        window_width_slider.config(from_=1, to=max_pixel_value)
    else:
        if dicom_window_width and dicom_window_center:
            new_dropdown = 'DICOM'
        else:
            new_dropdown = 'Auto'

        # Update slider ranges based on pixel data
        window_center_slider.config(from_=0, to=max_pixel_value)
        window_width_slider.config(from_=1, to=max_pixel_value)

    # Update the dropdown menu
    dropdown_var.set(new_dropdown)

    # Update the image based on the new selection
    update_sliders_based_on_dropdown()


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

    select_file_button = tk.Button(frame, text="Select DICOM File", command=select_file_and_display_data)   # Button to select a DICOM file
    select_file_button.pack(side=tk.LEFT, padx=5, pady=5)  # Pack the button with padding

    # Create an option menu for dropdown selection
    dropdown_var = tk.StringVar(value='Auto')  # Default value
    preset_menu = tk.OptionMenu(frame, dropdown_var, *preset_names, command=lambda _: update_sliders_based_on_dropdown())
    preset_menu.pack(side=tk.LEFT, padx=5, pady=5)

    # Create a frame to hold the canvas and scrollbar side by side
    image_frame = tk.Frame(root)
    image_frame.pack(fill=tk.BOTH, expand=1)

    # Create a canvas to display the image
    canvas = tk.Canvas(image_frame)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

    # Create a vertical scrollbar linked to the canvas
    scrollbar = tk.Scale(image_frame, from_=0, to=1, orient=tk.VERTICAL, command=update_slice_on_scrollbar)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Create sliders for window center and window width
    window_center_slider = tk.Scale(root, from_=-1024, to=3071, orient=tk.HORIZONTAL, label='Window Center', command=on_slider_change)
    window_center_slider.pack(fill=tk.X, padx=10, pady=5)

    window_width_slider = tk.Scale(root, from_=1, to=4096, orient=tk.HORIZONTAL, label='Window Width', command=on_slider_change)
    window_width_slider.pack(fill=tk.X, padx=10, pady=5)

    # Set initial values for the sliders based on default dropdown
    update_sliders_based_on_dropdown()

    # Bind the mouse scroll event to update the slice
    root.bind("<MouseWheel>", update_slice_on_scroll)

    # Redraw the image when the window is resized
    root.bind('<Configure>', lambda event: show_slice(current_slice_index) if slices_array is not None else None)

    # Set default window size
    root.geometry("800x700")  # Set the default size of the main window

    root.mainloop()  # Start the Tkinter main loop
