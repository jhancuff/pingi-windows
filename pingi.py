import tkinter as tk
from ping3 import ping
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from itertools import groupby
from operator import itemgetter
from tkinter import simpledialog
import threading
import collections
import argparse
import time

# Initialize variables
ping_times = collections.deque(maxlen=100)
ping_status = collections.deque(maxlen=100)


rolling_avg = 0
is_paused = False





# Function to update the graph and labels
def update(host):
    global rolling_avg, is_paused
    while True:
        if not is_paused:
            latency = ping(host, timeout=1)
            if latency is None or latency > 1:
                status_label.config(text="Status: Down", fg="red")
                ping_times.append(0)
                ping_status.append('down')
            else:
                latency_ms = latency * 1000
                status_label.config(text="Status: Up", fg="green")
                ping_times.append(latency_ms)
                ping_status.append('up')


            if len(ping_times) > 0:
                rolling_avg = sum(ping_times) / len(ping_times)
                avg_label.config(text=f"Rolling Avg: {rolling_avg:.2f} ms", fg="white")

            ax.clear()
            x = list(range(len(ping_times)))
            heights = [1000 if status == 'down' else latency for latency, status in zip(ping_times, ping_status)]
            colors = ['red' if status == 'down' else 'green' for status in ping_status]
            ax.bar(x, heights, color=colors)

            
            # Add a red vertical span when the host is down
            down_indices = [i for i, status in enumerate(ping_status) if status == 'down']
            def group_consecutive(lst):
                for _, group in groupby(enumerate(lst), lambda i_x: i_x[0]-i_x[1]):
                    yield list(map(itemgetter(1), group))

                ax.axvspan(start, end, color='red', alpha=0.5)
            
            ax.set_facecolor("black")
            ax.set_title(f'Ping Latency to {host} Over Time', color="white")
            ax.set_xlabel('Pings', color="white")
            ax.set_ylabel('Latency (ms)', color="white")
            
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            canvas.draw()
        
        time.sleep(ping_interval.get() / 1000)

# Pause and Play function
def toggle_pause():
    global is_paused
    is_paused = not is_paused
    pause_button.config(text="Pause" if not is_paused else "Play")

# CLI Argument Parsing
parser = argparse.ArgumentParser(description="Pingi - The Rockstar of Ping")
parser.add_argument("host", nargs="?", help="The IP address or hostname to ping")
args = parser.parse_args()

if args.host is None:
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    args.host = simpledialog.askstring("Input", "No host provided. Please enter the IP address or hostname to ping:")
    root.destroy()  # Destroy the main window

    if not args.host:
        print("You gotta give me something to work with! Exiting.")
        exit(1)


# GUI setup
root = tk.Tk()
root.title(f"Pingi - Pinging {args.host}")
root.configure(bg="black")
root.resizable(False, False)
ping_interval = tk.IntVar()
ping_interval.set(250)  # Default value
frame = tk.Frame(root, bg="black")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

status_label = tk.Label(frame, text="Status: Unknown", fg="white", bg="black")
status_label.grid(row=0, column=0, sticky=tk.W)

avg_label = tk.Label(frame, text="Rolling Avg: Unknown", fg="white", bg="black")
avg_label.grid(row=1, column=0, sticky=tk.W)

fig, ax = plt.subplots()
fig.patch.set_facecolor("black")
canvas = FigureCanvasTkAgg(fig, master=frame)
canvas_widget = canvas.get_tk_widget()
canvas_widget.grid(row=2, column=0)

pause_button = tk.Button(frame, text="Pause", command=toggle_pause)
pause_button.grid(row=3, column=0, sticky=tk.W)
def on_closing():
    global is_paused  # Because we're messing with the fabric of reality here
    is_paused = True  # Pause the update thread
    root.quit()       # End the Tkinter main loop
    root.destroy()    # Destroy the window

root.protocol("WM_DELETE_WINDOW", on_closing)
exit_button = tk.Button(frame, text="Exit", command=root.quit)
exit_button.grid(row=3, column=1, sticky=tk.E)
options = [250, 500, 750, 1000]
interval_menu = tk.OptionMenu(frame, ping_interval, *options)
interval_menu.grid(row=4, column=1, sticky=tk.W)
interval_label = tk.Label(frame, text="Ping Interval (ms):", fg="white", bg="black")
interval_label.grid(row=4, column=0, sticky=tk.E)
# Start the update thread
update_thread = threading.Thread(target=update, args=(args.host,))
update_thread.daemon = True
update_thread.start()

root.mainloop()