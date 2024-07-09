import tkinter as tk
from tkinter import filedialog
import os
from PIL import Image, ImageTk
import pydicom

def select_file_and_display_data():
    """
    Open a file dialog to select a DICOM file

    Inputs: None
    Outputs: None
    """
    # Open a file dialog to select a DICOM file and get its path
    file_path = filedialog.askopenfilename(title="Select DICOM file", filetypes=[("DICOM files", "*.dcm")])

    if file_path: # If a file is selected

        # Get the directory of the selected file
        folder_path = os.path.dirname(file_path)

        # List all DICOM files in the directory
        dicom_files = [file for file in os.listdir(folder_path) if file.endswith(".dcm")]

        if dicom_files:
            # If there are DICOM files in the directory
            # Check if the selected file has Pixel Data
            try:
                ds = pydicom.dcmread(file_path)
                if 'PixelData' in ds:
                    # TODO: call another function to read the data
                    print("pixel data present")
                else:
                    # TODO: add error message indicating there isn't pixel data
                    print("Selected file does not contain image data")
            except Exception as e:
                # TODO: add error message stating the file couldn't be read
                print("Could not open file: {e}")

            # Display the pixel data of the selected file

            for file in dicom_files:
                # TODO: Find the other images and preload them in if they are other slices
                print("TODO: add scroll for other slices")

        else: # If no DICOM files are found in the directory
            # TODO: Insert a message indicating no DICOM files were found
            print("TODO: add error message stating no files are found in the directory")

if __name__ == "__main__":
    root = tk.Tk()  # Create the main window
    root.title("DICOM Image Viewer")  # Set the window title

    frame = tk.Frame(root)  # Create a frame to hold the buttons and dropdown
    frame.pack(padx=10, pady=10)  # Add padding around the frame

    file_selection_var = tk.StringVar()  # Variable to store the selected file name
    folder_path_var = tk.StringVar()  # Variable to store the folder path

    select_file_button = tk.Button(frame, text="Select DICOM File", command=select_file_and_display_data)  # Button to select a DICOM file
    select_file_button.pack(side=tk.LEFT, padx=5, pady=5)  # Pack the button with padding

    # Set default window size
    root.geometry("800x600")  # Set the default size of the main window

    root.mainloop()  # Start the Tkinter main loop
