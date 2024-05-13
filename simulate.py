import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

def load_data(filename):
    data = {}
    with open(filename, 'r') as file:
        headers = file.readline().strip().split('|')
        for line in file:
            items = line.strip().split('|')
            if filename.endswith('Bullet.txt'):
                firearm_id = items[1].strip()  # This is the firearm ID
                if firearm_id not in data:
                    data[firearm_id] = []
                data[firearm_id].append({headers[i].strip(): items[i].strip() for i in range(len(items))})
            else:
                data_id = items[0].strip()
                data[data_id] = {headers[i].strip(): items[i].strip() for i in range(1, len(items))}
    return data

# Load data from files
firearms = load_data('Firearms.txt')
bullets = load_data('Bullet.txt')
ballistic_coefficients = load_data('Ballistic Coefficients.txt')

def calculate_accuracy(wind_speed, distance, bc, muzzle_velocity, bullet_weight_grains):
    # Constants
    g = 9.81  # gravitational acceleration (m/s^2)
    rho = 1.225  # air density at sea level (kg/m^3)
    A = 0.000509  # cross-sectional area of the bullet (m^2) - typical for .30 caliber bullet

    # Convert bullet weight from grains to kilograms
    m = bullet_weight_grains * 0.0000648  

    # Compute initial bullet speed and time of flight
    time_of_flight = distance / muzzle_velocity

    # Compute bullet drop with gravitational force
    bullet_drop = 0.5 * g * time_of_flight**2

    # Calculate drag force and wind drift, factoring in ballistic coefficient
    drag_factor = (0.5 * rho * A) / (bc * m)
    wind_drift = drag_factor * wind_speed**2 * time_of_flight**2

    # Calculate overall accuracy, considering drag and wind drift
    accuracy = np.exp(-0.05 * bullet_drop - 0.1 * wind_drift)
    return accuracy


def wind_influence(v_initial, angle, wind_speed, wind_angle, time):
    # Constants and conversions
    g = 9.81  # gravitational acceleration (m/s^2)
    rho = 1.225  # air density at sea level (kg/m^3)
    Cd = 0.5  # drag coefficient, assume it to be variable in an advanced model
    A = 0.000509  # cross-sectional area of the bullet (m^2)
    m = 0.005  # mass of the bullet (kg)

    # Convert angles to radians
    angle_rad = np.deg2rad(angle)
    wind_angle_rad = np.deg2rad(wind_angle)

    # Initial velocity components
    vx = v_initial * np.cos(angle_rad)
    vy = v_initial * np.sin(angle_rad)

    # Wind velocity components
    vw_x = wind_speed * np.cos(wind_angle_rad)
    vw_y = wind_speed * np.sin(wind_angle_rad)

    # Setup for Euler's method
    dt = 0.01  # time step
    x, y = 0, 0
    x_array, y_array = [0], [0]

    for t in np.arange(0, time, dt):
        F_drag_x = -0.5 * Cd * rho * A * (vx - vw_x)**2
        F_drag_y = -0.5 * Cd * rho * A * (vy - vw_y)**2

        vx += (F_drag_x / m) * dt
        vy += (-m * g + F_drag_y / m) * dt

        x += vx * dt
        y += vy * dt

        x_array.append(x)
        y_array.append(y)

    return x_array, y_array

def update_graph(frame, accuracy_percentage):
    frame.clear()
    frame.bar(0, accuracy_percentage, color='blue')
    frame.set_ylim(0, 100)  # Set y-axis limit from 0 to 100
    frame.set_title('Bullet Accuracy Rate')
    frame.set_ylabel('Accuracy Rate (%)')

def update_bullet_options(event):
    selected_firearm_id = firearm_combo.get().split(" - ")[0]
    bullet_options = bullets.get(selected_firearm_id, [])

    # Debugging: Print what bullet_options looks like
    print(f"bullet_options: {bullet_options}")

    # Ensure bullet_options is a list of dictionaries
    if not all(isinstance(bullet, dict) for bullet in bullet_options):
        print("Error: bullet_options does not contain dictionaries as expected.")
        bullet_combo.set('')
        bullet_combo['values'] = []
        return

    formatted_bullet_options = [
        f"{bullet['Bullet_ID']} - {bullet['Caliber']} - {bullet['Weight_Grains']} grains - {bullet['Bullet_Type']}"
        for bullet in bullet_options
    ]
    bullet_combo['values'] = formatted_bullet_options

    if formatted_bullet_options:
        bullet_combo.current(0)
    else:
        bullet_combo.set('')

def simulate():
    firearm_id = firearm_combo.get().split(" - ")[0]
    bullet_id = bullet_combo.get().split(" - ")[0]
    wind_speed = float(windspeed_entry.get())
    wind_angle = float(wind_angle_entry.get())
    distance = float(distance_entry.get())

    # Retrieve bullet details and check if the bullet is found
    bullet_dict = next((b for b in bullets[firearm_id] if b['Bullet_ID'] == bullet_id), None)
    if bullet_dict is None:
        print("Bullet not found!")
        accuracy_label.config(text="Bullet not found!")
        return

    muzzle_velocity = float(firearms[firearm_id]['Muzzle_Velocity'].split(' ')[0])
    bullet_weight_grains = float(bullet_dict['Weight_Grains'])
    bc = float(ballistic_coefficients[bullet_id]['Estimated_BC'])

    accuracy = calculate_accuracy(wind_speed, distance, bc, muzzle_velocity, bullet_weight_grains)
    accuracy_percentage = accuracy * 100

    update_graph(ax, accuracy_percentage)
    accuracy_label.config(text=f"Accuracy: {accuracy_percentage:.2f}%")
    canvas.draw()

root = tk.Tk()
root.title("Firearm Accuracy Simulator")

fig, ax = plt.subplots()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.grid(column=1, row=6, columnspan=2)

ttk.Label(root, text="Select Firearm:").grid(column=0, row=0)
firearm_combo = ttk.Combobox(root, values=[f"{fid} - {firearms[fid]['Name']}" for fid in sorted(firearms.keys())])
firearm_combo.grid(column=1, row=0)
firearm_combo.bind('<<ComboboxSelected>>', update_bullet_options)

ttk.Label(root, text="Select Bullet:").grid(column=0, row=1)
bullet_combo = ttk.Combobox(root)
bullet_combo.grid(column=1, row=1)

ttk.Label(root, text="Enter Distance (m):").grid(column=0, row=2)
distance_entry = ttk.Entry(root)
distance_entry.grid(column=1, row=2)

ttk.Label(root, text="Enter Wind Speed (m/s):").grid(column=0, row=3)
windspeed_entry = ttk.Entry(root)
windspeed_entry.grid(column=1, row=3)

ttk.Label(root, text="Enter Wind Angle (degrees):").grid(column=0, row=4)
wind_angle_entry = ttk.Entry(root)
wind_angle_entry.grid(column=1, row=4)

simulate_button = ttk.Button(root, text="Simulate Trajectory", command=simulate)
simulate_button.grid(column=1, row=5)

accuracy_label = ttk.Label(root, text="Accuracy: 0.00%")
accuracy_label.grid(column=1, row=7)

root.mainloop()
