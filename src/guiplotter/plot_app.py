"""Tkinter GUI for interactive plotting."""
from __future__ import annotations

import itertools
from pathlib import Path
from typing import Callable, Iterable, List

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from .data_loader import DataLoaderError
from .data_models import DataSet, SeriesSelection


def _color_cycle() -> itertools.cycle[str]:
    colors = matplotlib.rcParams["axes.prop_cycle"].by_key().get("color", ["C0", "C1", "C2"])
    return itertools.cycle(colors)


class PlotApplication(ttk.Frame):
    """Main application frame that wires the loader and Matplotlib canvas."""

    def __init__(self, master: tk.Tk, loader: Callable[[Iterable[str | Path]], List[DataSet]]) -> None:
        super().__init__(master)
        self.master = master
        self.master.title("GUI Plotter")
        self.loader = loader

        self.datasets: List[DataSet] = []
        self.series: List[SeriesSelection] = []
        self.color_cycle = _color_cycle()

        self.dataset_var = tk.StringVar(value="No datasets loaded")
        self.x_column_var = tk.StringVar()
        self.left_label_var = tk.StringVar(value="Left Axis")
        self.right_label_var = tk.StringVar(value="Right Axis")
        self.x_label_var = tk.StringVar(value="X Axis")
        self.series_label_var = tk.StringVar()
        self.show_legend_var = tk.BooleanVar(value=True)
        self.x_min_var = tk.StringVar()
        self.x_max_var = tk.StringVar()
        self.left_y_min_var = tk.StringVar()
        self.left_y_max_var = tk.StringVar()
        self.right_y_min_var = tk.StringVar()
        self.right_y_max_var = tk.StringVar()
        self.x_scale_var = tk.StringVar(value="1")
        self.left_y_scale_var = tk.StringVar(value="1")
        self.right_y_scale_var = tk.StringVar(value="1")
        self.x_log_var = tk.BooleanVar(value=False)
        self.left_y_log_var = tk.BooleanVar(value=False)
        self.right_y_log_var = tk.BooleanVar(value=False)

        self.left_series_indices: list[int] = []
        self.right_series_indices: list[int] = []

        self._build_layout()
        self.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------ UI setup
    def _build_layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        controls = ttk.Frame(self, padding=10)
        controls.grid(row=0, column=0, sticky="ns")

        plot_area = ttk.Frame(self, padding=5)
        plot_area.grid(row=0, column=1, sticky="nsew")
        plot_area.rowconfigure(0, weight=1)
        plot_area.columnconfigure(0, weight=1)

        self._build_file_controls(controls)
        self._build_column_controls(controls)
        self._build_series_controls(controls)
        self._build_axis_controls(controls)

        # Matplotlib canvas
        self.figure = Figure(figsize=(6,4), dpi=200, tight_layout=True)
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_area)
        toolbar = NavigationToolbar2Tk(self.canvas, plot_area, pack_toolbar=False)
        toolbar.update()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        toolbar.grid(row=1, column=0, sticky="ew")
        self.canvas.draw_idle()

    def _build_file_controls(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Data", padding=8)
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        frame.columnconfigure(0, weight=1)

        ttk.Button(frame, text="Open Files...", command=self._prompt_files).grid(row=0, column=0, sticky="ew")
        ttk.Label(frame, textvariable=self.dataset_var, wraplength=220).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.dataset_list = tk.Listbox(frame, height=6, exportselection=False)
        self.dataset_list.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.dataset_list.yview)
        scrollbar.grid(row=2, column=1, sticky="ns", padx=(4, 0))
        self.dataset_list.configure(yscrollcommand=scrollbar.set)
        self.dataset_list.bind("<<ListboxSelect>>", self._on_dataset_select)

    def _build_column_controls(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Columns", padding=8)
        frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Use column for X axis:").grid(row=0, column=0, sticky="w")
        self.x_column_combo = ttk.Combobox(frame, textvariable=self.x_column_var, state="readonly")
        self.x_column_combo.grid(row=1, column=0, sticky="ew", pady=(2, 6))

        ttk.Label(frame, text="Available columns:").grid(row=2, column=0, sticky="w")
        self.column_list = tk.Listbox(frame, height=6, exportselection=False)
        self.column_list.grid(row=3, column=0, sticky="nsew", pady=(4, 0))
        self.column_list.bind("<<ListboxSelect>>", self._on_column_select)

        add_button_frame = ttk.Frame(frame)
        add_button_frame.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(add_button_frame, text="Add to Left Axis", command=lambda: self._add_series("left")).grid(
            row=0, column=0, sticky="ew"
        )
        ttk.Button(add_button_frame, text="Add to Right Axis", command=lambda: self._add_series("right")).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        ttk.Label(frame, text="Custom label (optional):").grid(row=5, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(frame, textvariable=self.series_label_var).grid(row=6, column=0, sticky="ew")

    def _build_series_controls(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent)
        frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        left_frame = ttk.LabelFrame(frame, text="Left Axis Series", padding=8)
        left_frame.grid(row=0, column=0, sticky="nsew")
        right_frame = ttk.LabelFrame(frame, text="Right Axis Series", padding=8)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.left_series_listbox = tk.Listbox(left_frame, height=6, exportselection=False)
        self.left_series_listbox.grid(row=0, column=0, columnspan=2, sticky="nsew")
        ttk.Button(left_frame, text="Remove", command=lambda: self._remove_series("left")).grid(
            row=1, column=0, sticky="ew", pady=(6, 0)
        )
        ttk.Button(left_frame, text="Color...", command=lambda: self._update_series_color("left")).grid(
            row=1, column=1, sticky="ew", pady=(6, 0), padx=(6, 0)
        )

        self.right_series_listbox = tk.Listbox(right_frame, height=6, exportselection=False)
        self.right_series_listbox.grid(row=0, column=0, columnspan=2, sticky="nsew")
        ttk.Button(right_frame, text="Remove", command=lambda: self._remove_series("right")).grid(
            row=1, column=0, sticky="ew", pady=(6, 0)
        )
        ttk.Button(right_frame, text="Color...", command=lambda: self._update_series_color("right")).grid(
            row=1, column=1, sticky="ew", pady=(6, 0), padx=(6, 0)
        )

    def _build_axis_controls(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Plot Options", padding=8)
        frame.grid(row=3, column=0, sticky="ew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="X label:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.x_label_var).grid(row=0, column=1, sticky="ew")

        ttk.Label(frame, text="Left axis label:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(frame, textvariable=self.left_label_var).grid(row=1, column=1, sticky="ew", pady=(6, 0))

        ttk.Label(frame, text="Right axis label:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(frame, textvariable=self.right_label_var).grid(row=2, column=1, sticky="ew", pady=(6, 0))

        ttk.Checkbutton(frame, text="Show legend", variable=self.show_legend_var).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )

        x_options = ttk.LabelFrame(frame, text="X Axis Options", padding=6)
        x_options.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        x_options.columnconfigure(1, weight=1)
        x_options.columnconfigure(3, weight=1)
        ttk.Label(x_options, text="Min:").grid(row=0, column=0, sticky="w")
        ttk.Entry(x_options, textvariable=self.x_min_var, width=10).grid(row=0, column=1, sticky="ew")
        ttk.Label(x_options, text="Max:").grid(row=0, column=2, sticky="w", padx=(6, 0))
        ttk.Entry(x_options, textvariable=self.x_max_var, width=10).grid(row=0, column=3, sticky="ew")
        ttk.Label(x_options, text="Scale:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(x_options, textvariable=self.x_scale_var, width=10).grid(row=1, column=1, sticky="ew", pady=(6, 0))
        ttk.Checkbutton(x_options, text="Log scale", variable=self.x_log_var).grid(
            row=1, column=2, columnspan=2, sticky="w", padx=(6, 0), pady=(6, 0)
        )

        left_options = ttk.LabelFrame(frame, text="Left Axis Options", padding=6)
        left_options.grid(row=5, column=0, columnspan=2, sticky="ew")
        left_options.columnconfigure(1, weight=1)
        left_options.columnconfigure(3, weight=1)
        ttk.Label(left_options, text="Min:").grid(row=0, column=0, sticky="w")
        ttk.Entry(left_options, textvariable=self.left_y_min_var, width=10).grid(row=0, column=1, sticky="ew")
        ttk.Label(left_options, text="Max:").grid(row=0, column=2, sticky="w", padx=(6, 0))
        ttk.Entry(left_options, textvariable=self.left_y_max_var, width=10).grid(row=0, column=3, sticky="ew")
        ttk.Label(left_options, text="Scale:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(left_options, textvariable=self.left_y_scale_var, width=10).grid(row=1, column=1, sticky="ew", pady=(6, 0))
        ttk.Checkbutton(left_options, text="Log scale", variable=self.left_y_log_var).grid(
            row=1, column=2, columnspan=2, sticky="w", padx=(6, 0), pady=(6, 0)
        )

        right_options = ttk.LabelFrame(frame, text="Right Axis Options", padding=6)
        right_options.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        right_options.columnconfigure(1, weight=1)
        right_options.columnconfigure(3, weight=1)
        ttk.Label(right_options, text="Min:").grid(row=0, column=0, sticky="w")
        ttk.Entry(right_options, textvariable=self.right_y_min_var, width=10).grid(row=0, column=1, sticky="ew")
        ttk.Label(right_options, text="Max:").grid(row=0, column=2, sticky="w", padx=(6, 0))
        ttk.Entry(right_options, textvariable=self.right_y_max_var, width=10).grid(row=0, column=3, sticky="ew")
        ttk.Label(right_options, text="Scale:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(right_options, textvariable=self.right_y_scale_var, width=10).grid(row=1, column=1, sticky="ew", pady=(6, 0))
        ttk.Checkbutton(right_options, text="Log scale", variable=self.right_y_log_var).grid(
            row=1, column=2, columnspan=2, sticky="w", padx=(6, 0), pady=(6, 0)
        )

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(button_frame, text="Plot", command=self._plot_series).grid(row=0, column=0, sticky="ew")
        ttk.Button(button_frame, text="Clear", command=self._clear_plot).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

    # ------------------------------------------------------------------ Dataset management
    def _prompt_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select space-delimited files",
            filetypes=[("Data files", "*.txt *.dat *.csv *.tsv"), ("All files", "*.*")],
        )
        if not paths:
            return

        try:
            new_datasets = self.loader(paths)
        except DataLoaderError as exc:
            messagebox.showerror("Failed to load data", str(exc))
            return

        if not new_datasets:
            return

        start_index = len(self.datasets)
        self.datasets.extend(new_datasets)
        self.dataset_var.set(f"{len(self.datasets)} dataset(s) loaded")
        self._refresh_dataset_list()

        # Auto-select the first of the newly loaded datasets.
        self.dataset_list.selection_clear(0, tk.END)
        self.dataset_list.selection_set(start_index)
        self._on_dataset_select()

    def _refresh_dataset_list(self) -> None:
        self.dataset_list.delete(0, tk.END)
        for dataset in self.datasets:
            self.dataset_list.insert(tk.END, dataset.name)

    def _on_dataset_select(self, _: tk.Event | None = None) -> None:
        selection = self.dataset_list.curselection()
        if not selection:
            self._clear_column_panel()
            return
        dataset = self.datasets[selection[0]]
        self.dataset_var.set(f"Selected: {dataset.name}")

        self.column_list.delete(0, tk.END)
        for column in dataset.columns:
            self.column_list.insert(tk.END, column)

        self.x_column_combo["values"] = dataset.columns
        if self.x_column_var.get() not in dataset.columns:
            if dataset.columns:
                self.x_column_var.set(dataset.columns[0])
            else:
                self.x_column_var.set("")

    def _clear_column_panel(self) -> None:
        self.column_list.delete(0, tk.END)
        self.x_column_combo["values"] = []
        self.x_column_var.set("")

    def _on_column_select(self, _: tk.Event | None = None) -> None:
        dataset_idx = self._current_dataset_index()
        column = self._current_column_name()
        if dataset_idx is None or not column:
            return
        dataset = self.datasets[dataset_idx]
        self.series_label_var.set(f"{dataset.name}: {column}")

    def _current_dataset_index(self) -> int | None:
        selection = self.dataset_list.curselection()
        return selection[0] if selection else None

    def _current_column_name(self) -> str | None:
        selection = self.column_list.curselection()
        return self.column_list.get(selection[0]) if selection else None

    # ------------------------------------------------------------------ Series management
    def _add_series(self, axis: str) -> None:
        dataset_index = self._current_dataset_index()
        column = self._current_column_name()
        x_column = self.x_column_var.get()

        if dataset_index is None:
            messagebox.showinfo("Select dataset", "Choose a dataset before adding a series.")
            return
        if not column:
            messagebox.showinfo("Select column", "Choose a column before adding a series.")
            return
        if not x_column:
            messagebox.showinfo("Select X column", "Choose a column to use for the X axis.")
            return

        dataset = self.datasets[dataset_index]
        if x_column not in dataset.columns:
            messagebox.showerror(
                "Column unavailable", f"Dataset '{dataset.name}' does not contain column '{x_column}'."
            )
            return

        label = self.series_label_var.get().strip() or f"{dataset.name}: {column}"
        color = next(self.color_cycle)
        self.series.append(SeriesSelection(dataset_index=dataset_index, column=column, axis=axis, label=label, color=color))
        self.series_label_var.set("")
        self._refresh_series_lists()

    def _refresh_series_lists(self) -> None:
        self.left_series_listbox.delete(0, tk.END)
        self.right_series_listbox.delete(0, tk.END)
        self.left_series_indices.clear()
        self.right_series_indices.clear()

        for index, selection in enumerate(self.series):
            dataset = self.datasets[selection.dataset_index]
            display = f"{selection.label} [{dataset.name}/{selection.column}]"
            if selection.color:
                display = f"{display} ({selection.color})"
            if selection.axis == "left":
                self.left_series_indices.append(index)
                self.left_series_listbox.insert(tk.END, display)
            else:
                self.right_series_indices.append(index)
                self.right_series_listbox.insert(tk.END, display)

    def _remove_series(self, axis: str) -> None:
        listbox, index_map = self._series_widgets(axis)
        selection = listbox.curselection()
        if not selection:
            return
        target = index_map[selection[0]]
        del self.series[target]
        self._refresh_series_lists()

    def _update_series_color(self, axis: str) -> None:
        listbox, index_map = self._series_widgets(axis)
        selection = listbox.curselection()
        if not selection:
            return
        target = index_map[selection[0]]
        current_color = self.series[target].color
        _, hex_color = colorchooser.askcolor(color=current_color, title="Select series color")
        if hex_color:
            self.series[target] = SeriesSelection(
                dataset_index=self.series[target].dataset_index,
                column=self.series[target].column,
                axis=self.series[target].axis,
                label=self.series[target].label,
                color=hex_color,
            )
            self._refresh_series_lists()

    def _series_widgets(self, axis: str) -> tuple[tk.Listbox, list[int]]:
        if axis == "left":
            return self.left_series_listbox, self.left_series_indices
        return self.right_series_listbox, self.right_series_indices

    def _get_float_from_var(
        self, var: tk.StringVar, label: str, default: float | None = None
    ) -> float | None:
        """Return float value for the given entry or show an error if invalid."""
        value = var.get().strip()
        if not value:
            return default
        try:
            return float(value)
        except ValueError:
            messagebox.showerror("Invalid value", f"Enter a numeric value for {label}.")
            raise ValueError from None

    # ------------------------------------------------------------------ Plotting
    def _plot_series(self) -> None:
        if not self.series:
            messagebox.showinfo("No series", "Add at least one series to plot.")
            return
        x_column = self.x_column_var.get()
        if not x_column:
            messagebox.showinfo("Select X column", "Choose a column for the X axis.")
            return

        try:
            x_scale = self._get_float_from_var(self.x_scale_var, "X axis scale", default=1.0)
            left_y_scale = self._get_float_from_var(self.left_y_scale_var, "Left axis scale", default=1.0)
            right_y_scale = self._get_float_from_var(self.right_y_scale_var, "Right axis scale", default=1.0)
            x_min = self._get_float_from_var(self.x_min_var, "X axis minimum")
            x_max = self._get_float_from_var(self.x_max_var, "X axis maximum")
            left_y_min = self._get_float_from_var(self.left_y_min_var, "Left axis minimum")
            left_y_max = self._get_float_from_var(self.left_y_max_var, "Left axis maximum")
            right_y_min = self._get_float_from_var(self.right_y_min_var, "Right axis minimum")
            right_y_max = self._get_float_from_var(self.right_y_max_var, "Right axis maximum")
        except ValueError:
            return

        self.figure.clear()
        ax_left = self.figure.add_subplot(111)
        ax_right = None

        legend_handles: list = []
        legend_labels: list[str] = []

        for selection in self.series:
            dataset = self.datasets[selection.dataset_index]
            if selection.column not in dataset.data.columns:
                messagebox.showwarning(
                    "Missing column", f"Column '{selection.column}' no longer exists in dataset '{dataset.name}'."
                )
                continue
            if x_column not in dataset.data.columns:
                messagebox.showwarning(
                    "Missing column", f"Column '{x_column}' not found in dataset '{dataset.name}'."
                )
                continue

            x_data = dataset.data[x_column]
            y_data = dataset.data[selection.column]
            x_data = x_data * x_scale
            y_scale = left_y_scale if selection.axis == "left" else right_y_scale
            y_data = y_data * y_scale

            target_axis = ax_left if selection.axis == "left" else ax_right
            if target_axis is None:
                ax_right = ax_left.twinx()
                target_axis = ax_right

            (line,) = target_axis.plot(x_data, y_data, label=selection.label, color=selection.color)
            legend_handles.append(line)
            legend_labels.append(selection.label)

        ax_left.set_xlabel(self.x_label_var.get().strip() or x_column)
        ax_left.set_ylabel(self.left_label_var.get().strip() or "Left Axis")
        if ax_right:
            ax_right.set_ylabel(self.right_label_var.get().strip() or "Right Axis")

        if self.show_legend_var.get() and legend_handles:
            labels = legend_labels
            handles = legend_handles
            # If twin axes exist, place legend on the left axis to avoid duplication.
            ax_left.legend(handles, labels, loc="best")

        if x_min is not None or x_max is not None:
            ax_left.set_xlim(left=x_min, right=x_max)
        if left_y_min is not None or left_y_max is not None:
            ax_left.set_ylim(bottom=left_y_min, top=left_y_max)
        if ax_right and (right_y_min is not None or right_y_max is not None):
            ax_right.set_ylim(bottom=right_y_min, top=right_y_max)

        ax_left.set_xscale("log" if self.x_log_var.get() else "linear")
        ax_left.set_yscale("log" if self.left_y_log_var.get() else "linear")
        if ax_right:
            ax_right.set_yscale("log" if self.right_y_log_var.get() else "linear")

        self.canvas.draw_idle()

    def _clear_plot(self) -> None:
        self.figure.clear()
        self.canvas.draw_idle()


__all__ = ["PlotApplication"]
