import matplotlib.pyplot as plt

# === Process Info ===
process_info = {
    'p1': ('FlightControlSoftware_1', 'Brake Control Software'),
    'p2': ('FlightControlSoftware_2', 'Brake Control Software Hot Spare'),
    'p3': ('FlightControlSoftware_3', 'Auto Pilot Software'),
    'p4': ('FlightControlSoftware_4', 'Utilities Control Software'),
    'p5': ('FlightControlSoftware_5', 'Environmental Control Software'),
}

# === Colors ===
colors = {
    'p1': '#e41a1c',
    'p2': '#4daf4a',
    'p3': '#377eb8',
    'p4': '#ff7f00',
    'p5': '#984ea3'
}

# === Constants ===
CYCLE_TO_TIME = 0.0025
TOTAL_CYCLES = 2000
MAJOR_SLOT = 1000
HEIGHT = 12
Y_POS = 10
PATTERN_REPEAT = 11

# === Create Plot ===
fig, ax = plt.subplots(figsize=(18, 5))

# Each pattern has 12 slots: 10 x p1/p2 + p2 + p3
slots_per_pattern = 12
slot_width = MAJOR_SLOT / (PATTERN_REPEAT * slots_per_pattern)

# === Helper: draw a block with label ===
def draw_block(start_cycle, width, label):
    ax.broken_barh([(start_cycle, width)], (Y_POS, HEIGHT), facecolors=colors[label], edgecolor='black')
    ax.text(start_cycle + width / 2, Y_POS + HEIGHT / 2, label, ha='center', va='center', color='white', fontsize=8, fontweight='bold')

# === First Half: 0–1000 cycles ===
cycle = 0
for _ in range(PATTERN_REPEAT):
    for _ in range(10):  # 10 p1s
        draw_block(cycle, slot_width, 'p1')
        cycle += slot_width
    for pid in ['p2', 'p3']:  # one each
        draw_block(cycle, slot_width, pid)
        cycle += slot_width

# Draw p4 before 1000
draw_block(MAJOR_SLOT - slot_width, slot_width, 'p4')

# === Second Half: 1000–2000 cycles ===
slot_width_after = (TOTAL_CYCLES - MAJOR_SLOT) / (PATTERN_REPEAT * slots_per_pattern)
for _ in range(PATTERN_REPEAT):
    for _ in range(10):  # 10 p2s (replacing p1)
        draw_block(cycle, slot_width_after, 'p2')
        cycle += slot_width_after
    for pid in ['p2', 'p3']:
        draw_block(cycle, slot_width_after, pid)
        cycle += slot_width_after

# Draw p4 before 2000
draw_block(TOTAL_CYCLES - slot_width_after, slot_width_after, 'p4')

# === Transition Marker ===
ax.axvline(MAJOR_SLOT, color='black', linestyle='--', linewidth=1)
ax.text(MAJOR_SLOT, Y_POS + HEIGHT + 4, 'Transition @1000 cycles\n(2.5 s)', ha='center', va='bottom', fontsize=9, fontweight='bold')

# === Axes ===
ax.set_xlim(0, TOTAL_CYCLES + 400)  # extra space for legend
ax.set_ylim(0, 60)
ax.set_yticks([])
ax.set_title('Partition Schedule', fontsize=12, fontweight='bold')

# Top axis: cycle count
ax_top = ax.twiny()
ax_top.set_xlim(ax.get_xlim())
ax_top.set_xticks(range(0, TOTAL_CYCLES + 1, 500))
ax_top.set_xlabel('Cycles', fontsize=10)

# Bottom axis: time in seconds
ax.set_xticks(range(0, TOTAL_CYCLES + 1, 500))
ax.set_xticklabels([f"{x * CYCLE_TO_TIME:.1f}" for x in range(0, TOTAL_CYCLES + 1, 500)])
ax.set_xlabel('Time (seconds)', fontsize=10)

# === Manual Legend ===
legend_x = TOTAL_CYCLES + 100
legend_y = 45
spacing = 5

# Adjust the starting position of text for better alignment
for i, pid in enumerate(['p1', 'p2', 'p3', 'p4', 'p5']):
    ax.add_patch(plt.Rectangle((legend_x, legend_y - i * spacing), 10, 3, color=colors[pid], ec='black'))
    ax.text(legend_x + 15, legend_y - i * spacing + 1.5, f"{pid}: {process_info[pid][1]}", va='center', fontsize=9, ha='left')

plt.tight_layout()
plt.show()
