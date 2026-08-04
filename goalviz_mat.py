import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

player = (2, 38, 0)
goal   = (0, 52.9, 2.5)

fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")

# Trajectory line
ax.plot([player[0], goal[0]],
        [player[1], goal[1]],
        [player[2], goal[2]],
        linewidth=3, label="Shot trajectory")

# Points
ax.scatter(*player, s=60, label="Shooter")
ax.scatter(*goal,   s=60, label="Goal mouth point")

ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")

ax.legend()
ax.set_title("3D shot visualization")
plt.show()
