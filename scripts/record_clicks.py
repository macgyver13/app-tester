#!/usr/bin/env python3
"""
PyAutoGUI Click Recorder - Records mouse clicks and coordinates
This helps you build automation scripts by recording where you click
"""
import pyautogui
import time
from pynput import mouse

class ClickRecorder:
    def __init__(self, setup_crop=False, crop=None, interactive=False):
        self.clicks = []
        self.start_time = time.time()
        self.setup_crop = setup_crop
        self.interactive = interactive
        self.crop_region = None
        self.crop_corner1 = None
        self.crop_corner2 = None
        self.listener = None
        self.waiting_for_name = False
        
        # If crop provided directly, parse it
        if crop:
            try:
                x, y, width, height = map(int, crop.split(','))
                self.crop_region = (x, y, width, height)
                print(f"Using provided crop region: {self.crop_region}")
            except:
                print(f"Warning: Invalid crop format '{crop}', expected 'x,y,width,height'")
        
    def on_click(self, x, y, button, pressed):
        """Called when mouse button is pressed"""
        if pressed and button == mouse.Button.left:
            # Handle crop setup mode
            if self.setup_crop and self.crop_region is None:
                if self.crop_corner1 is None:
                    self.crop_corner1 = (x, y)
                    print(f"\n✓ Upper-left corner recorded: ({x}, {y})")
                    print("Now click the lower-right corner of the crop region...")
                    return
                elif self.crop_corner2 is None:
                    self.crop_corner2 = (x, y)
                    # Calculate crop region
                    x1, y1 = self.crop_corner1
                    x2, y2 = self.crop_corner2
                    crop_x = min(x1, x2)
                    crop_y = min(y1, y2)
                    crop_width = abs(x2 - x1)
                    crop_height = abs(y2 - y1)
                    self.crop_region = (crop_x, crop_y, crop_width, crop_height)
                    print(f"✓ Lower-right corner recorded: ({x}, {y})")
                    print(f"\n✓ Crop region set: {self.crop_region}")
                    print(f"  Position: ({crop_x}, {crop_y})")
                    print(f"  Size: {crop_width}x{crop_height}")
                    print("\nNow recording regular clicks...\n")
                    return
            
            # Regular click recording
            elapsed = time.time() - self.start_time
            click_data = {
                'x': int(x),
                'y': int(y),
                'time': elapsed,
                'step': len(self.clicks) + 1,
                'name': None
            }
            
            print(f"\n✓ Click {len(self.clicks) + 1}: Position ({x}, {y})")
            
            # If interactive mode, pause listener and prompt for name
            if self.interactive:
                self.waiting_for_name = True
                self.listener.stop()
                
                # Prompt for name
                name = input("  Enter name for this coordinate (or press Enter to skip): ").strip()
                if name:
                    click_data['name'] = name
                    print(f"  Saved as: {name}")
                else:
                    click_data['name'] = f"coord_{len(self.clicks) + 1}"
                    print(f"  Auto-named: {click_data['name']}")
                
                self.clicks.append(click_data)
                
                # Resume listener
                self.waiting_for_name = False
                self.listener = mouse.Listener(on_click=self.on_click)
                self.listener.start()
            else:
                self.clicks.append(click_data)
                print(f"  Add to script: target=\"{x},{y}\"")
    
    def start_recording(self):
        """Start recording clicks for specified duration"""
        print("="*70)
        print("PyAutoGUI Click Recorder")
        print("="*70)
        
        if self.setup_crop and self.crop_region is None:
            print("\nSETUP MODE: Define crop region first")
            print("1. Click the UPPER-LEFT corner of the area to capture")
            print("2. Click the LOWER-RIGHT corner of the area to capture")
            print("3. Then record normal clicks\n")
        elif self.crop_region:
            print(f"\nUsing crop region: {self.crop_region}\n")
        else:
            print("\nClick on UI elements in your app to record their positions.")
        
        if self.interactive:
            print("INTERACTIVE MODE: You'll be prompted to name each coordinate.\n")
        
        print("Press Ctrl+C to stop.\n")
        
        # Start mouse listener
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()
        
        try:
            while True:
                if not self.waiting_for_name:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n✓ Recording stopped")
        
        if self.listener:
            self.listener.stop()
        self.generate_code()
    
    def generate_code(self):
        """Generate config.yaml format from recorded clicks"""
        if not self.clicks:
            print("\n✗ No clicks recorded")
            return

        print("\n\n" + "="*70)
        print(f"Recorded {len(self.clicks)} clicks")
        print("="*70)

        # Show crop region if set
        if self.crop_region:
            crop_x, crop_y, crop_width, crop_height = self.crop_region
            print(f"\nCrop Region: {self.crop_region}")
            print(f"  Position: ({crop_x}, {crop_y})")
            print(f"  Size: {crop_width}x{crop_height}")

        # Show summary
        print("\nClick Summary:")
        for click in self.clicks:
            if click.get('name'):
                print(f"  {click['name']}: ({click['x']}, {click['y']}) at {click['time']:.1f}s")
            else:
                print(f"  Step {click['step']}: ({click['x']}, {click['y']}) at {click['time']:.1f}s")

        # Generate config.yaml format
        print("\n" + "="*70)
        print("Generated config.yaml section (copy/paste into your config):")
        print("="*70)
        print()

        print("  sections:")
        print("    your_section_name:")
        print("      title: \"Your Section Title\"")
        print("      description: \"Description of this section\"")

        # Add crop region
        if self.crop_region:
            crop_x, crop_y, crop_width, crop_height = self.crop_region
            print(f"      crop: [{crop_x}, {crop_y}, {crop_width}, {crop_height}]")
        else:
            print("      crop: [100, 100, 1200, 800]  # Adjust as needed")

        # Add coordinates if interactive mode
        if self.interactive and any(click.get('name') for click in self.clicks):
            print("      coordinates:")
            for click in self.clicks:
                if click.get('name'):
                    print(f"        {click['name']}: [{click['x']}, {click['y']}]")

            print("      steps:")
            # Generate steps using named coordinates
            for click in self.clicks:
                if click.get('name'):
                    step_name = click['name'].replace('_', ' ').title()
                    print(f"        - name: \"{step_name}\"")
                    print(f"          description: \"TODO: Describe what this does\"")
                    print(f"          action: \"click\"")
                    print(f"          target: \"{click['name']}\"")
                    print(f"          screenshot: true")
                    print()
        else:
            # Generate coordinates with auto-names
            print("      coordinates:")
            for i, click in enumerate(self.clicks, 1):
                coord_name = f"coord_{i}"
                print(f"        {coord_name}: [{click['x']}, {click['y']}]")

            print("      steps:")
            # Generate steps with auto-named coordinates
            for i, click in enumerate(self.clicks, 1):
                coord_name = f"coord_{i}"
                print(f"        - name: \"Step {i}\"")
                print(f"          description: \"TODO: Describe what this does\"")
                print(f"          action: \"click\"")
                print(f"          target: \"{coord_name}\"")
                print(f"          screenshot: true")
                print()

        print("\n" + "="*70)
        print("Usage Tips:")
        print("="*70)
        print("1. Copy the section above to your config.yaml")
        print("2. Replace 'your_section_name' with a meaningful name (e.g., 'setup', 'usage')")
        print("3. Update the title and description")
        print("4. Fill in step descriptions (replace TODO comments)")
        print("5. Adjust action types if needed (click, type, wait, screenshot)")
        print("6. Add more properties: notes, flags, omit_from_output, etc.")
        print()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Record mouse clicks and generate automation code")
    parser.add_argument('--setup-crop', action='store_true', 
                        help='First 2 clicks define crop region (upper-left then lower-right)')
    parser.add_argument('--crop', type=str, 
                        help='Crop region as "x,y,width,height" (e.g., "100,100,800,600")')
    parser.add_argument('--interactive', action='store_true',
                        help='Prompt for coordinate names after each click')
    args = parser.parse_args()
    
    recorder = ClickRecorder(setup_crop=args.setup_crop, crop=args.crop, interactive=args.interactive)
    recorder.start_recording()
