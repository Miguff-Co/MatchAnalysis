import plotly.graph_objects as go
import plotly.io as pio

pio.renderers.default = "browser"   # safest outside notebooks


PITCH_W = 68.0
HALF_L  = 52.5
GOAL_W  = 7.32
GOAL_H  = 2.44
BOX_6_Y = 5.5
BOX_18_Y = 16.5
PEN_SPOT = 11.0


# --- SofaScore to Metric Scaler ---
def scale_x(val): return (val / 50) * HALF_L
def scale_y(val): return (val / 100) * PITCH_W
def scale_z(val): return (val / 100) * (GOAL_H * 1.5) # Scale Z relative to goal height

def draw_half_pitch(fig: go.Figure):
    goal_center_y = PITCH_W / 2

    left_post  = goal_center_y + GOAL_W / 2
    right_post = goal_center_y - GOAL_W / 2

    # --- pitch boundary ---
    fig.add_trace(go.Scatter3d(
        x=[0, HALF_L, HALF_L, 0, 0],
        y=[0, 0, PITCH_W, PITCH_W, 0],
        z=[0]*5,
        mode="lines",
        name="Boundary",
        line=dict(width=6)
    ))

    # --- halfway line ---
    fig.add_trace(go.Scatter3d(
        x=[HALF_L, HALF_L],
        y=[0, PITCH_W],
        z=[0, 0],
        mode="lines",
        name="Halfway line",
        line=dict(width=4, dash="dash")
    ))

    # --- goal ---
    fig.add_trace(go.Scatter3d(
        x=[0, 0, 0, 0, 0],
        y=[right_post, left_post, left_post, right_post, right_post],
        z=[0, 0, GOAL_H, GOAL_H, 0],
        mode="lines",
        name="Goal",
        line=dict(width=6)
    ))

    # --- 6-yard box ---
    fig.add_trace(go.Scatter3d(
        x=[0, BOX_6_Y, BOX_6_Y, 0, 0],
        y=[
            goal_center_y - 9.16,
            goal_center_y - 9.16,
            goal_center_y + 9.16,
            goal_center_y + 9.16,
            goal_center_y - 9.16,
        ],
        z=[0]*5,
        mode="lines",
        name="6-yard box"
    ))

    # --- penalty area ---
    fig.add_trace(go.Scatter3d(
        x=[0, BOX_18_Y, BOX_18_Y, 0, 0],
        y=[
            goal_center_y - 20.16,
            goal_center_y - 20.16,
            goal_center_y + 20.16,
            goal_center_y + 20.16,
            goal_center_y - 20.16,
        ],
        z=[0]*5,
        mode="lines",
        name="Penalty area"
    ))

    # --- penalty spot ---
    fig.add_trace(go.Scatter3d(
        x=[PEN_SPOT],
        y=[goal_center_y],
        z=[0],
        mode="markers",
        marker=dict(size=5),
        name="Penalty spot"
    ))


# --- Data Parsing ---
raw_shotmap = [
    {"player": "Ahmed Benbouali", "coords": {"x": 12.5, "y": 42.7}, "draw": {"start": {"x": 42.7, "y": 12.5}, "block": {"x": 43.7, "y": 11}}, "type": "block", "isHome": True},
    {"player": "Nfansu Njie", "coords": {"x": 8.3, "y": 30.9}, "draw": {"start": {"x": 30.9, "y": 8.3}, "end": {"x": 53, "y": 0}}, "type": "goal", "isHome": True},
    {"player": "Nfansu Njie", "coords": {"x": 9.2, "y": 32.7}, "draw": {"start": {"x": 32.7, "y": 9.2}, "block": {"x": 46.6, "y": 2.5}}, "type": "save", "isHome": True},
    {"player": "Marcell Huszár", "coords": {"x": 24.7, "y": 33.8}, "draw": {"start": {"x": 33.8, "y": 24.7}, "block": {"x": 35.9, "y": 20.2}}, "type": "block", "isHome": True},
    {"player": "Milán Vitális", "coords": {"x": 21, "y": 45.4}, "draw": {"start": {"x": 45.4, "y": 21}, "end": {"x": 47.7, "y": 0}}, "type": "miss", "isHome": True},
    {"player": "Milán Vitális", "coords": {"x": 19.8, "y": 17.2}, "draw": {"start": {"x": 17.2, "y": 19.8}, "block": {"x": 47.7, "y": 1}}, "type": "save", "isHome": True},
    {"player": "Željko Gavrić", "coords": {"x": 10.1, "y": 37.6}, "draw": {"start": {"x": 37.6, "y": 10.1}, "block": {"x": 44, "y": 4.8}}, "type": "block", "isHome": True},
    {"player": "Milán Vitális", "coords": {"x": 29.6, "y": 63.9}, "draw": {"start": {"x": 63.9, "y": 29.6}, "block": {"x": 50.7, "y": 2.3}}, "type": "save", "isHome": True},
    {"player": "Milán Vitális", "coords": {"x": 25.4, "y": 42.7}, "draw": {"start": {"x": 42.7, "y": 25.4}, "block": {"x": 50.5, "y": 2.8}}, "type": "save", "isHome": True},
    {"player": "Claudiu Bumba", "coords": {"x": 11.3, "y": 29.1}, "draw": {"start": {"x": 29.1, "y": 11.3}, "end": {"x": 42.2, "y": 0}}, "type": "miss", "isHome": True},
    {"player": "Claudiu Bumba", "coords": {"x": 24.6, "y": 33.4}, "draw": {"start": {"x": 33.4, "y": 24.6}, "block": {"x": 48.2, "y": 2.4}}, "type": "save", "isHome": True},
    {"player": "Ahmed Benbouali", "coords": {"x": 7.3, "y": 54}, "draw": {"start": {"x": 54, "y": 7.3}, "block": {"x": 50.5, "y": 3.1}}, "type": "save", "isHome": True},
    {"player": "Ahmed Benbouali", "coords": {"x": 2, "y": 38}, "draw": {"start": {"x": 38, "y": 2}, "end": {"x": 47.1, "y": 0}}, "type": "goal", "isHome": True},
    {"player": "Ahmed Benbouali", "coords": {"x": 9.5, "y": 38.9}, "draw": {"start": {"x": 38.9, "y": 9.5}, "block": {"x": 43.5, "y": 4.5}}, "type": "save", "isHome": True},
]

fig = go.Figure()
draw_half_pitch(fig)

colors = {'goal': '#2ecc71', 'save': '#3498db', 'block': '#f1c40f', 'miss': '#e74c3c'}

for s in raw_shotmap:
    # 1. Start Position logic (from your working Matplotlib version)
    # Scale from 100-x (distance from goal line) and 100-y (side mirror)
    sx = scale_x(s['coords']['x'])
    sy = scale_y(s['coords']['y'])
    
    # 2. End Position logic (from your 'dest' flip)
    dest = s['draw'].get('block') if 'block' in s['draw'] else s['draw'].get('end')
    # Use the Y of the draw coordinate for the metric X (depth)
    # Use the X of the draw coordinate for the metric Y (width)
    ex = scale_x(dest.get('y', 0)) 
    ey = scale_y(dest.get('x', 0))
    
    # Estimate a height for 3D effect (Goals are high, blocks are low)
    ez = 1.5 if s['type'] == 'goal' else (0.5 if s['type'] == 'save' else 0)

    clr = colors.get(s['type'], 'white')
    
    # Draw trajectory line
    fig.add_trace(go.Scatter3d(
        x=[sx, ex], y=[sy, ey], z=[0, ez],
        mode="lines+markers",
        line=dict(color=clr, width=6),
        marker=dict(size=[6, 0], color=clr),
        name=f"{s['player']} ({s['type']})"
    ))

# --- Layout Fixes ---
fig.update_layout(
    template="plotly_dark",
    scene=dict(
        xaxis=dict(title="Depth (m)", range=[0, HALF_L]),
        yaxis=dict(title="Width (m)", range=[0, PITCH_W]),
        zaxis=dict(title="Height (m)", range=[0, 4]),
        aspectmode="data",
        camera=dict(eye=dict(x=1.2, y=1.2, z=0.8))
    )
)

# -----------------------------
# Layout
# -----------------------------
fig.update_layout(
    title="3D shot on half pitch (origin at top-right)",
    scene=dict(
        xaxis_title="x (perpendicular to goal, 0 at goal line)",
        yaxis_title="y (parallel to goal, 0 at top-right corner)",
        zaxis_title="z (height)",
        xaxis=dict(range=[0, HALF_L]),
        yaxis=dict(range=[0, PITCH_W]),
        zaxis=dict(range=[0, 3]),
        aspectmode="data",
        camera=dict(eye=dict(x=1.6, y=1.6, z=0.6))
    ),
    legend=dict(x=0.02, y=0.98)
)

fig.show()
