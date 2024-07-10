import tkinter as tk
from tkinter import filedialog
import os
from PIL import Image, ImageTk
import pydicom
import numpy as np

# Initialize global variables to store the slices and current index
slices_array = None
current_slice_index = 0

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

        # Extract pixel data and stack into a 3D numpy array
        slices_array = np.stack([s.pixel_array for s in dicom_slices], axis=-1)

    elif len(dicom_files) == 1:
        # If there's only one DICOM file, assume it's an entire image (like an NM)
        # Read the single DICOM file
        dicom_slices = pydicom.dcmread(dicom_files[0])

        # Extract the pixel array from the DICOM file
        slices_array = dicom_slices.pixel_array

        # Swap axes to match the expected (x, y, z) format
        slices_array = np.swapaxes(slices_array, 0, 2)

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

    # Convert the pixel array to a PIL image
    image = Image.fromarray(slice_array)

    # Convert to grayscale (L mode)
    image = image.convert('L')

    # Convert the PIL image to a PhotoImage object for Tkinter
    tk_image = ImageTk.PhotoImage(image)

    # Create an image item in the canvas
    canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)

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

if __name__ == "__main__":
    root = tk.Tk()  # Create the main window
    root.title("DICOM Image Viewer")  # Set the window title

    frame = tk.Frame(root)  # Create a frame to hold the buttons and dropdown
    frame.pack(padx=10, pady=10)  # Add padding around the frame

    file_selection_var = tk.StringVar()  # Variable to store the selected file name
    folder_path_var = tk.StringVar()  # Variable to store the folder path

    select_file_button = tk.Button(frame, text="Select DICOM File", command=select_file_and_display_data)  # Button to select a DICOM file
    select_file_button.pack(side=tk.LEFT, padx=5, pady=5)  # Pack the button with padding

    # Create a canvas to display the image
    canvas = tk.Canvas(root)
    canvas.pack(fill=tk.BOTH, expand=1)

    # Bind the mouse scroll event to update the slice
    root.bind("<MouseWheel>", update_slice_on_scroll)

    # Set default window size
    root.geometry("800x600")  # Set the default size of the main window

    root.mainloop()  # Start the Tkinter main loop
