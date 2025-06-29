"""
Fixed Gauge Components - Custom gauge widgets for displaying test data
Type-safe version that addresses PyRight warnings
"""

import tkinter as tk
import math
from typing import Optional, Union


class BaseGauge:
    """Base class for gauge components with improved error handling"""
    
    def __init__(self, parent: tk.Widget, colors: dict, title: str, unit: str, 
                 max_value: Union[int, float] = 100, is_countdown: bool = False):
        self.parent = parent
        self.colors = colors
        self.title = title
        self.unit = unit
        self.max_value = float(max_value)  # Ensure float type
        self.is_countdown = is_countdown
        self.current_value = 0.0
        self.canvas: Optional[tk.Canvas] = None

    def create(self) -> Optional[tk.Canvas]:
        """Create the gauge canvas and initial drawing"""
        try:
            self.canvas = tk.Canvas(self.parent, width=400, height=400, 
                                   bg=self.colors['white'], highlightthickness=0)
            self.canvas.pack()
            
            # Draw initial gauge
            self.draw_gauge()
            return self.canvas
        except Exception as e:
            print(f"Error creating gauge: {e}")
            return None

    def draw_gauge(self) -> None:
        """Draw the complete gauge with error handling"""
        if not self.canvas:
            return
            
        try:
            self.canvas.delete("all")
            CENTER_X, CENTER_Y, RADIUS = 200, 200, 160

            # Draw shadow effects for main circle
            for i in range(3):
                shadow_offset = i + 1
                self.canvas.create_oval(
                    CENTER_X - RADIUS + shadow_offset,
                    CENTER_Y - RADIUS + shadow_offset,
                    CENTER_X + RADIUS + shadow_offset,
                    CENTER_Y + RADIUS + shadow_offset,
                    fill='', outline='#E0E0E0'
                )

            # Main circle
            self.canvas.create_oval(
                CENTER_X - RADIUS, CENTER_Y - RADIUS,
                CENTER_X + RADIUS, CENTER_Y + RADIUS,
                fill=self.colors['white'],
                outline=self.colors['border'],
                width=2
            )

            # Draw ticks and labels
            self.draw_ticks(CENTER_X, CENTER_Y, RADIUS)
            
            # Draw progress arc
            self.draw_progress_arc(CENTER_X, CENTER_Y, RADIUS)
            
            # Draw center display
            self.draw_center_display(CENTER_X, CENTER_Y)
            
            # Draw title
            self.draw_title(CENTER_X, CENTER_Y)
            
        except Exception as e:
            print(f"Error drawing gauge: {e}")

    def draw_ticks(self, center_x: int, center_y: int, radius: int) -> None:
        """Draw tick marks and labels with improved calculations"""
        if not self.canvas:
            return
            
        try:
            for i in range(31):  # 30 ticks total
                is_major = i % 5 == 0
                angle = 150 - (i * 10)  # Spread over 300 degrees
                radian = math.radians(angle)

                # Calculate tick positions
                tick_length = 15 if is_major else 7
                start_x = center_x + (radius - tick_length) * math.cos(radian)
                start_y = center_y - (radius - tick_length) * math.sin(radian)
                end_x = center_x + radius * math.cos(radian)
                end_y = center_y - radius * math.sin(radian)

                # Draw tick
                self.canvas.create_line(
                    start_x, start_y, end_x, end_y,
                    fill=self.colors['text_primary'],
                    width=2 if is_major else 1
                )

                # Add labels for major ticks
                if is_major:
                    label_radius = radius - 30
                    text_x = center_x + label_radius * math.cos(radian)
                    text_y = center_y - label_radius * math.sin(radian)
                    
                    if self.is_countdown:
                        # For duration gauge - show countdown values
                        tick_value = self.max_value - (i / 30) * self.max_value
                    else:
                        # For pressure gauge - show normal values
                        tick_value = (i / 30) * self.max_value
                    
                    # Ensure tick value is not negative
                    tick_value = max(0, tick_value)
                    
                    self.canvas.create_text(
                        text_x, text_y,
                        text=f"{tick_value:.1f}",
                        font=('Arial', 14, 'bold'),  # Smaller font for better fit
                        fill=self.colors['text_primary']
                    )
        except Exception as e:
            print(f"Error drawing ticks: {e}")

    def draw_progress_arc(self, center_x: int, center_y: int, radius: int) -> None:
        """Draw the progress arc with improved calculations"""
        if not self.canvas:
            return
            
        try:
            start_angle = 150
            total_angle = 300
            
            # Draw background arc track
            self.canvas.create_arc(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                start=start_angle, extent=-total_angle,
                style=tk.ARC, outline='#E0E0E0', width=30
            )

            # Calculate progress with bounds checking
            if self.max_value <= 0:
                progress = 0.0
            else:
                progress = max(0.0, min(1.0, self.current_value / self.max_value))
            
            value_angle = progress * total_angle

            # Draw progress arc
            if self.current_value > 0 and value_angle > 0:
                self.canvas.create_arc(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    start=start_angle, extent=-value_angle,
                    style=tk.ARC, outline=self.colors['primary'], width=15
                )
        except Exception as e:
            print(f"Error drawing progress arc: {e}")

    def draw_center_display(self, center_x: int, center_y: int) -> None:
        """Draw center value display with improved formatting"""
        if not self.canvas:
            return
            
        try:
            display_radius = 40
            
            # Center display with shadow
            for i in range(2):
                shadow_offset = i + 1
                self.canvas.create_oval(
                    center_x - display_radius + shadow_offset,
                    center_y - display_radius + shadow_offset,
                    center_x + display_radius + shadow_offset,
                    center_y + display_radius + shadow_offset,
                    fill='', outline='#E0E0E0'
                )

            # Center circle
            self.canvas.create_oval(
                center_x - display_radius, center_y - display_radius,
                center_x + display_radius, center_y + display_radius,
                fill=self.colors['white'],
                outline=self.colors['border']
            )

            # Format display value
            if self.is_countdown:
                display_value = max(0.0, self.max_value - self.current_value)
                display_text = f"{display_value:.1f}"
            else:
                display_text = f"{self.current_value:.1f}"
            
            # Add unit on separate line for better readability
            unit_text = self.unit

            # Create shadow effect for text
            shadow_offsets = [(1,1), (1,-1), (-1,1), (-1,-1)]
            for offset_x, offset_y in shadow_offsets:
                self.canvas.create_text(
                    center_x + offset_x, center_y - 5 + offset_y,
                    text=display_text,
                    font=('Arial', 16, 'bold'),
                    fill='#E0E0E0'
                )
                self.canvas.create_text(
                    center_x + offset_x, center_y + 15 + offset_y,
                    text=unit_text,
                    font=('Arial', 10),
                    fill='#E0E0E0'
                )

            # Main value display
            self.canvas.create_text(
                center_x, center_y - 5,
                text=display_text,
                font=('Arial', 16, 'bold'),
                fill=self.colors['text_primary']
            )
            
            # Unit display
            self.canvas.create_text(
                center_x, center_y + 15,
                text=unit_text,
                font=('Arial', 10),
                fill=self.colors['text_secondary']
            )
        except Exception as e:
            print(f"Error drawing center display: {e}")

    def draw_title(self, center_x: int, center_y: int) -> None:
        """Draw gauge title"""
        if not self.canvas:
            return
            
        try:
            self.canvas.create_text(
                center_x, center_y - 80,
                text=self.title,
                font=('Arial', 16, 'bold'),
                fill=self.colors['text_primary']
            )
        except Exception as e:
            print(f"Error drawing title: {e}")

    def update_value(self, value: Union[int, float], max_val: Optional[Union[int, float]] = None) -> None:
        """Update the gauge with a new value"""
        try:
            # Update max value if provided
            if max_val is not None and max_val > 0:
                self.max_value = float(max_val)
            
            # Update current value with bounds checking
            self.current_value = max(0.0, min(float(value), self.max_value))
            
            # Redraw gauge
            self.draw_gauge()
            
            if self.canvas:
                self.canvas.update_idletasks()
        except Exception as e:
            print(f"Error updating gauge value: {e}")

    def set_max_value(self, max_val: Union[int, float]) -> None:
        """Set new maximum value and redraw"""
        try:
            if max_val > 0:
                self.max_value = float(max_val)
                self.draw_gauge()
        except Exception as e:
            print(f"Error setting max value: {e}")


class PressureGauge(BaseGauge):
    """Pressure gauge component with fixed parameters"""
    
    def __init__(self, parent: tk.Widget, colors: dict, max_value: Union[int, float] = 4.5):
        super().__init__(parent, colors, "Pressure", "bar", float(max_value), is_countdown=False)


class DurationGauge(BaseGauge):
    """Duration/Time gauge component with countdown functionality"""
    
    def __init__(self, parent: tk.Widget, colors: dict, max_value: Union[int, float] = 120.0):
        super().__init__(parent, colors, "Time", "min", float(max_value), is_countdown=True)

    def update_max_value(self, new_max: Union[int, float]) -> None:
        """Update the maximum value for the gauge"""
        try:
            if new_max > 0:
                self.max_value = float(new_max)
                self.draw_gauge()
        except Exception as e:
            print(f"Error updating max value: {e}")

    def update_countdown(self, elapsed_time_minutes: Union[int, float]) -> None:
        """Update with elapsed time for countdown display"""
        try:
            # Clamp elapsed time to max value
            elapsed = max(0.0, min(float(elapsed_time_minutes), self.max_value))
            self.update_value(elapsed)
        except Exception as e:
            print(f"Error updating countdown: {e}")