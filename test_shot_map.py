import matplotlib.pyplot as plt
import pandas as pd
from mplsoccer import VerticalPitch

# 1. YOUR RAW DATA
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

# 2. FILTER & PREPARE
# Extract only isHome=True and transform coordinates for the pitch
data = []
for s in raw_shotmap:
    if s['isHome']:
        # SofaScore x is distance from endline, y is distance from sideline
        # VerticalPitch 'opta' uses 100-x for vertical height
        start_x, start_y = 100 - s['coords']['x'], 100 - s['coords']['y']
        
        # Determine the line endpoint (either the block point or the final end point)
        dest = s['draw'].get('block') if 'block' in s['draw'] else s['draw'].get('end')
        end_x, end_y = dest['y'], dest['x'] # Draw coords are often flipped in API
        
        data.append({
            'player': s['player'],
            'x': start_x,
            'y': start_y,
            'end_x': 100 if s['type'] == 'goal' else (100 - dest.get('y', 0)),
            'end_y': 100 - dest.get('x', 50),
            'type': s['type']
        })

df = pd.DataFrame(data)

# 3. PLOTTING
pitch = VerticalPitch(pitch_type='opta', half=True, pitch_color='#1a1a1a', line_color='#444444')
fig, ax = pitch.draw(figsize=(10, 8))
fig.set_facecolor('#1a1a1a')

colors = {'goal': '#2ecc71', 'save': '#3498db', 'miss': '#e74c3c', 'block': '#f1c40f'}

for _, row in df.iterrows():
    color = colors.get(row['type'], 'white')
    
    # Draw the shot path line
    pitch.lines(row['x'], row['y'], row['end_x'], row['end_y'], 
                lw=2, color=color, alpha=0.4, comet=True, ax=ax)
    
    # Draw the shot origin point
    pitch.scatter(row['x'], row['y'], 
                  edgecolors='white', c=color, s=250, 
                  marker='*' if row['type'] == 'goal' else 'o', 
                  ax=ax, zorder=3)

# 4. POLISH
plt.title("Home Team Shotmap", color='white', size=20, pad=10, weight='bold')
plt.legend(handles=[
    plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='#2ecc71', markersize=15, label='Goal', ls=''),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#3498db', markersize=10, label='Save', ls=''),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#f1c40f', markersize=10, label='Block', ls=''),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#e74c3c', markersize=10, label='Miss', ls=''),
], loc='lower center', bbox_to_anchor=(0.5, -0.1), ncol=4, frameon=False, labelcolor='white')

plt.show()