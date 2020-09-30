import sys

import matplotlib
import numpy as np

if sys.platform == 'darwin':
    matplotlib.use("tkagg")
else:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt

import seaborn as sns
import skimage
from PIL import Image
from habitat_sim.utils.common import d3_40_colors_rgb

def visualize(fig, ax, img, semantic_obs, grid, pos, gt_pos, dump_dir, rank, ep_no, t,
              visualize, print_images, object_name, gt_action):
    for i in range(2):
        ax[i].clear()
        ax[i].set_yticks([])
        ax[i].set_xticks([])
        ax[i].set_yticklabels([])
        ax[i].set_xticklabels([])

    ax[0].imshow(img)
    ax[0].set_title("Observation", family='sans-serif',
                    fontname='Helvetica',
                    fontsize=20)


    title = "Find " + object_name + ", Action: " +str(gt_action)

    ax[1].imshow(grid)
    ax[1].set_title(title, family='sans-serif',
                    fontname='Helvetica',
                    fontsize=20)

    semantic_img = Image.new("P", (semantic_obs.shape[1], semantic_obs.shape[0]))
    semantic_img.putpalette(d3_40_colors_rgb.flatten())
    semantic_img.putdata((semantic_obs.flatten() % 40).astype(np.uint8))
    semantic_img = semantic_img.convert("RGB")
    semantic_img = np.array(semantic_img)
    ax[2].imshow(semantic_img)
    # print("================================vis: ", img.shape, "================================", grid.shape) #480 480 3
    # Draw GT agent pose
    agent_size = 8
    x, y, o = gt_pos
    x, y = x * 100.0 / 5.0, grid.shape[1] - y * 100.0 / 5.0

    dx = 0
    dy = 0
    fc = 'Grey'
    dx = np.cos(np.deg2rad(o))
    dy = -np.sin(np.deg2rad(o))
    ax[1].arrow(x - 1 * dx, y - 1 * dy, dx * agent_size, dy * (agent_size * 1.25),
                head_width=agent_size, head_length=agent_size * 1.25,
                length_includes_head=True, fc=fc, ec=fc, alpha=0.9)

    # Draw predicted agent pose
    x, y, o = pos
    x, y = x * 100.0 / 5.0, grid.shape[1] - y * 100.0 / 5.0

    dx = 0
    dy = 0
    fc = 'Red'
    dx = np.cos(np.deg2rad(o))
    dy = -np.sin(np.deg2rad(o))
    ax[1].arrow(x - 1 * dx, y - 1 * dy, dx * agent_size, dy * agent_size * 1.25,
                head_width=agent_size, head_length=agent_size * 1.25,
                length_includes_head=True, fc=fc, ec=fc, alpha=0.6)

    for _ in range(5):
        plt.tight_layout()

    if visualize:
        plt.gcf().canvas.flush_events()
        fig.canvas.start_event_loop(0.001)
        plt.gcf().canvas.flush_events()

    if print_images:
        fn = '{}/episodes/{}/{}/{}-{}-Vis-{}.png'.format(
            dump_dir, (rank + 1), ep_no, rank, ep_no, t)
        plt.savefig(fn)


def insert_circle(mat, x, y, value):
    mat[x - 2: x + 3, y - 2:y + 3] = value
    mat[x - 3:x + 4, y - 1:y + 2] = value
    mat[x - 1:x + 2, y - 3:y + 4] = value
    return mat


def fill_color(colored, mat, color):
    for i in range(3):
        colored[:, :, 2 - i] *= (1 - mat)
        colored[:, :, 2 - i] += (1 - color[i]) * mat
    return colored


def get_colored_map(mat, collision_map, visited, visited_gt, goal,
                    explored, gt_map, gt_map_explored, semantic_map):
    m, n = mat.shape
    colored = np.zeros((m, n, 3))
    pal = sns.color_palette("Paired")

    current_palette = [(0.9, 0.9, 0.9)]
    # colored = fill_color(colored, gt_map, current_palette[0]) # 灰色真实地图

    current_palette = [(235. / 255., 243. / 255., 1.)]
    colored = fill_color(colored, explored, current_palette[0]) # 已探索区域，青灰色

    green_palette = sns.light_palette("green")
    colored = fill_color(colored, mat, pal[2]) # 正常地图，青色

    current_palette = [(0.6, 0.6, 0.6)]
    colored = fill_color(colored, gt_map_explored, current_palette[0]) # 正常地图 灰色

    current_palette = [(100. / 255., 100. / 255., 100. / 255)]
    colored = fill_color(colored, mat * gt_map_explored, pal[3]) # 正常地图 绿色

    red_palette = sns.light_palette("red")

    colored = fill_color(colored, visited_gt, current_palette[0])
    colored = fill_color(colored, visited, pal[4])
    colored = fill_color(colored, visited * visited_gt, pal[5])

    # colored = fill_color(colored, collision_map, pal[2])

    current_palette = sns.color_palette()

    selem = skimage.morphology.disk(4)
    goal_mat = np.zeros((m, n))
    goal_mat[goal[0], goal[1]] = 1
    goal_mat = 1 - skimage.morphology.binary_dilation(
        goal_mat, selem) != True

    colored = fill_color(colored, goal_mat, current_palette[0])

    semantic_palette = np.array([1. / 255., 254. / 255., 254. / 255.])
    for i in range(semantic_map.shape[2]):
        semantic_palette = semantic_palette + np.array([10. / 255., -10. / 255, -10. / 255])
        colored = fill_color(colored, semantic_map[:,:,i], semantic_palette)

    current_palette = sns.color_palette("Paired")

    colored = 1 - colored
    colored *= 255
    colored = colored.astype(np.uint8)
    return colored
