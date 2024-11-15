import cv2
import tkinter as tk
from PIL import Image, ImageTk
from predict import *

# Initialize Tkinter window
root = tk.Tk()
root.title("Vehicle Meter")

# Set up the video capture from the webcam
cap = cv2.VideoCapture(0)

# Check if webcam opened successfully
if not cap.isOpened():
    print("Error: Could not open webcam.")
    root.destroy()

# Set up a label widget to display frames
video_label = tk.Label(root)
video_label.pack()

init_tracker()
init_tracker()
current_dir = Path.cwd()

predictor = DetectionPredictor()


def update_frame():
    # Capture a frame from the webcam
    ret, frame = cap.read()
    if ret:
        # Run predictions on the frame
        results = predictor.predict(frame)  # Assuming `predict` processes the frame and returns results

        # Display the frame with results
        frame = predictor.write_results(frame, results)  # Assuming `write_results` overlays annotations

        # Convert the frame to RGB (OpenCV uses BGR by default)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert the frame to a format that Tkinter can use
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)

        # Display the image on the Tkinter label
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

    # Schedule the next frame update
    video_label.after(10, update_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
        print("Window closed via key press.")

        cap.release()
        cv2.destroyAllWindows()
        return


# Start the frame update loop
update_frame()


# Run the Tkinter event loop
root.mainloop()

# Release the webcam when the window is closed


