import matplotlib.pyplot as plt

FREQUENCIES = [125, 250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000]

def plot_audiogram(right_ac=None, right_bc=None, left_ac=None, left_bc=None, title="Pure Tone Audiogram"):
    """
    Each of right_ac, right_bc, left_ac, left_bc is a dict like:
        {500: 20, 1000: 25, 2000: 30, 4000: 35}
    Any of them can be left as None if that data isn't available.
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    # Flip the y-axis: 0 at top (best hearing), 120 at bottom (worst)
    ax.set_ylim(120, -10)
    ax.set_xscale("log")
    ax.set_xticks(FREQUENCIES)
    ax.set_xticklabels(FREQUENCIES)
    ax.set_xlim(100, 9000)

    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Hearing Level (dB HL)")
    ax.set_title(title)
    ax.grid(True, which="both", linestyle="--", alpha=0.5)

    def plot_series(data, color, marker, linestyle, label):
        if not data:
            return
        freqs = sorted(data.keys())
        values = [data[f] for f in freqs]
        ax.plot(freqs, values, color=color, marker=marker,
                 linestyle=linestyle, markersize=10, markerfacecolor='none',
                 markeredgewidth=2, label=label)

    plot_series(right_ac, "red", "o", "-", "Right AC")
    plot_series(right_bc, "red", "<", "--", "Right BC")
    plot_series(left_ac, "blue", "x", "-", "Left AC")
    plot_series(left_bc, "blue", ">", "--", "Left BC")

    ax.legend()
    plt.tight_layout()
    return fig


if __name__ == "__main__":
    right_ac = {500: 20, 1000: 25, 2000: 30, 4000: 35}
    right_bc = {500: 15, 1000: 20, 2000: 20, 4000: 25}
    left_ac = {500: 45, 1000: 55, 2000: 65, 4000: 75}
    left_bc = {500: 40, 1000: 45, 2000: 50, 4000: 55}

    fig = plot_audiogram(right_ac, right_bc, left_ac, left_bc)
    plt.show()