import plotly.graph_objects as go
import plotly.io as pio

pio.renderers.default = "browser"

# --- Constants (Meters) ---
PITCH_W = 68.0    # y direction (sideline to sideline)
HALF_L  = 52.5    # x direction (goal line to halfway)
GOAL_W  = 7.32
GOAL_H  = 2.44
BOX_6_Y = 5.5
BOX_18_Y = 16.5
PEN_SPOT = 11.0

# --- SOFASCORE CORRECTION LOGIC ---
# In SofaScore API: 
# x is distance from goal (0 is goal line)
# y is distance from the side (0 to 100)
def scale_x(val): 
    return (val / 50) * HALF_L

def scale_y(val): 
    # To match your "top-right" origin drawing:
    return (val / 100) * PITCH_W

def scale_z(val): 
    # SofaScore Z: 0 is ground, 100 is roughly top of goal/high sky.
    # We map 100 to slightly above the crossbar for realism.
    return (val / 100) * (GOAL_H * 1.2)

def draw_half_pitch(fig: go.Figure):
    goal_center_y = PITCH_W / 2
    left_post  = goal_center_y + GOAL_W / 2
    right_post = goal_center_y - GOAL_W / 2

    # Boundary
    fig.add_trace(go.Scatter3d(
        x=[0, HALF_L, HALF_L, 0, 0], y=[0, 0, PITCH_W, PITCH_W, 0], z=[0]*5,
        mode="lines", name="Boundary", line=dict(color="#888", width=4), showlegend=False
    ))

    # Goal
    fig.add_trace(go.Scatter3d(
        x=[0, 0, 0, 0, 0], y=[right_post, left_post, left_post, right_post, right_post],
        z=[0, 0, GOAL_H, GOAL_H, 0], mode="lines", name="Goal", line=dict(color="white", width=8)
    ))

    # 18-Yard Box
    fig.add_trace(go.Scatter3d(
        x=[0, BOX_18_Y, BOX_18_Y, 0], y=[goal_center_y-20.16, goal_center_y-20.16, goal_center_y+20.16, goal_center_y+20.16],
        z=[0, 0, 0, 0], mode="lines", line=dict(color="#666", width=4), showlegend=False
    ))

# --- Data ---
raw_data = [
    {"p": "N. Njie", "type": "goal", "start": [8.3, 30.9], "end": [0, 47, 12.7]},
    {"p": "N. Njie", "type": "save", "start": [9.2, 32.7], "end": [2.5, 46.6, 3.8]},
    {"p": "M. Vitális", "type": "save", "start": [29.6, 63.9], "end": [2.3, 50.7, 3.8]},
    {"p": "A. Benbouali", "type": "goal", "start": [2, 38], "end": [0, 52.9, 2.5]},
    {"p": "C. Bumba", "type": "save", "start": [24.6, 33.4], "end": [2.4, 48.2, 7]},
    {"p": "Z. Gavrić", "type": "block", "start": [10.1, 37.6], "end": [4.8, 44, 0]},
]

fig = go.Figure()
draw_half_pitch(fig)

colors = {'goal': '#2ecc71', 'save': '#3498db', 'block': '#f1c40f', 'miss': '#e74c3c'}

for shot in raw_data:
    # 1. Coordinate Correction: 
    # Start: x is dist from goal. y is width.
    s_x = scale_x(shot['start'][0])
    s_y = scale_y(shot['start'][1])
    
    # End: x is usually 0 for goal/miss or >0 for blocks.
    e_x = scale_x(shot['end'][0])
    e_y = scale_y(shot['end'][1])
    e_z = scale_z(shot['end'][2])
    
    clr = colors.get(shot['type'], 'white')
    
    # Trajectory
    fig.add_trace(go.Scatter3d(
        x=[s_x, e_x], y=[s_y, e_y], z=[0, e_z],
        mode="lines+markers",
        line=dict(color=clr, width=6),
        marker=dict(size=[8, 0], color=clr), # Marker only at start
        name=f"{shot['p']} ({shot['type']})"
    ))

# Layout
fig.update_layout(
    template="plotly_dark",
    scene=dict(
        xaxis=dict(title="Dist from Goal", range=[0, HALF_L]),
        yaxis=dict(title="Pitch Width", range=[0, PITCH_W]),
        zaxis=dict(title="Height", range=[0, 5]),
        aspectmode="data"
    )
)

fig.show()