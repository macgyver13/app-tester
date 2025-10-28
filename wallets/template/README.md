# Wallet Template README

This template provides a starting point for creating new wallet documentation with two powerful approaches: **config-driven** (recommended) and **code-driven**.

## Quick Start

### 1. Copy the Template
```bash
cp -r wallets/template wallets/my-wallet
cd wallets/my-wallet
```

### 2. Edit `config.yaml`

Update the basic wallet information:
```yaml
wallet:
  name: "My Wallet"
  app_path:
    macos: "/Applications/MyWallet.app"
```

### 3. Choose Your Approach

#### **RECOMMENDED: Config-Driven Approach**

Define your automation in `config.yaml` using the contextual syntax:

```yaml
documentation:
  sections:
    setup:
      title: "Initial Wallet Setup"
      description: "Create and configure your wallet"
      crop: [100, 100, 800, 600]  # Optional default crop

      coordinates:
        create_button: [400, 300]
        name_field: [400, 350]

      steps:
        - name: "Create Wallet"
          description: "Click to create a new wallet"
          action: "click"
          target: "create_button"  # References coordinates.create_button
          screenshot: true
```

The `setup_walkthrough.py` will automatically load steps from config:
```python
wallet.add_steps_from_config()  # Load all sections
```

**Benefits:**
- Single source of truth in config.yaml
- Easy to update coordinates without touching code
- Non-developers can modify automation
- Cleaner, more maintainable

#### **Alternative: Code-Driven Approach**

For complex logic or dynamic steps, define them in Python:

```python
wallet.add_step(
    Step(
        name="Create Wallet",
        description="Click to create a new wallet",
        action="click",
        target=(400, 300),  # Direct coordinates or selector
        screenshot=True,
        section="setup"
    )
)
```

### 4. Test the Automation

```bash
# Full pipeline with automation + docs
python scripts/run_wallet.py wallets/my-wallet/setup_walkthrough.py

# Just regenerate docs (no automation)
python scripts/run_wallet.py wallets/my-wallet/setup_walkthrough.py --docs-only
```

## Configuration Structure

### Contextual Syntax Features

#### 1. Named Coordinates
Define once, reference everywhere:
```yaml
coordinates:
  create_button: [400, 300]
  import_button: [400, 350]

steps:
  - name: "Create"
    target: "create_button"  # Resolves to [400, 300]
```

#### 2. Inherited Crop Regions
Set a default crop for all steps in a section:
```yaml
setup:
  crop: [100, 100, 800, 600]
  steps:
    - name: "Step 1"
      # Inherits crop: [100, 100, 800, 600]
    - name: "Step 2"
      crop_region: [200, 200, 600, 400]  # Override for this step
```

#### 3. Section Organization
Organize steps into logical sections:
```yaml
sections:
  build:
    title: "Building from Source"
    steps: []  # Informational only

  setup:
    title: "Initial Setup"
    steps: [...]

  usage:
    title: "Using the Wallet"
    steps: [...]
```

#### 4. Step Properties
All step properties can be defined in config:
```yaml
steps:
  - name: "Enter Password"
    description: "Set a strong password"
    action: "type"
    target: "password_field"
    value: "SecurePass123!"
    screenshot: true
    flags: ["NEW"]  # Optional: Mark as new feature
    notes: "Remember your password!"
    omit_from_output: false  # Include in docs
```

## Automation Backends

### Appium (GUI Element-Based)

For apps with accessible UI elements:

```python
wallet = WalletAutomation(
    name=config.name,
    app_path=config.get_app_path(),
    version="1.0.0",
    config=config
)
```

**Finding Selectors:**
1. Install [Appium Inspector](https://github.com/appium/appium-inspector)
2. Start Appium: `appium`
3. Connect Inspector to your app
4. Click elements to see their selectors

**Target formats:**
- Accessibility ID: `"CreateWalletButton"`
- Name: `"Create Wallet"`
- XPath: `"//XCUIElementTypeButton[@name='Create']"`

### PyAutoGUI (Coordinate-Based)

For coordinate-based automation (any desktop app):

```python
wallet = PyAutoGUIAutomation(
    name=config.name,
    app_path=config.get_app_path(),
    version="1.0.0",
    config=config,
    scale_factor=2.0  # Retina displays
)
```

**Finding Coordinates:**
1. Use `record_clicks.py` to capture coordinates
2. Position mouse and click to record (x, y)
3. Use in config or code as `[x, y]`

**Target formats:**
- Direct coordinates: `[400, 300]`
- Named reference: `"create_button"` (resolved from config)

## Common Patterns

### Basic Click
```yaml
- name: "Click Button"
  description: "Click to proceed"
  action: "click"
  target: "button_name"
  screenshot: true
```

### Text Input
```yaml
- name: "Enter Text"
  description: "Type into field"
  action: "type"
  target: "input_field"
  value: "Text to type"
  screenshot: true
```

### Wait Step
```yaml
- name: "Wait for Loading"
  description: "Wait for operation to complete"
  action: "wait"
  wait_time: 5
  screenshot: false
```

### Screenshot Only
```yaml
- name: "View Dashboard"
  description: "Main wallet screen"
  action: "screenshot"
  screenshot: true
```

### Hidden Step (No Docs)
```yaml
- name: "Focus Field"
  description: "Internal step"
  action: "click"
  target: "input_field"
  screenshot: false
  omit_from_output: true  # Won't appear in docs
```

## Advanced Features

### Multiple Sections
Run specific sections only:
```bash
python scripts/run_wallet.py wallets/my-wallet/setup_walkthrough.py --sections setup
```

### Documentation Only
Regenerate docs without running automation:
```bash
python scripts/run_wallet.py wallets/my-wallet/setup_walkthrough.py --docs-only
```

### Hybrid Approach
Mix config and code:
```python
wallet.add_steps_from_config('setup')    # Load from config
wallet.add_step(Step(...))               # Add custom step
wallet.add_steps_from_config('usage')    # Load more from config
```

### Feature Flags
Mark steps as new, changed, or deprecated:
```yaml
steps:
  - name: "New Feature"
    flags: ["NEW"]
  - name: "Updated Step"
    flags: ["CHANGED"]
  - name: "Old Feature"
    flags: ["DEPRECATED"]
```

## Step Properties Reference

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `name` | string | Step name (appears in docs) | `"Create Wallet"` |
| `description` | string | Step description | `"Click to create..."` |
| `action` | string | Action type | `click`, `type`, `wait`, `screenshot`, `launch` |
| `target` | string/array | Element selector or [x, y] | `"button_id"` or `[400, 300]` |
| `value` | string | Text to type (for `type` action) | `"My Wallet"` |
| `screenshot` | boolean | Capture screenshot | `true` |
| `crop_region` | array | Crop as [x, y, w, h] | `[100, 100, 800, 600]` |
| `flags` | array | Feature markers | `["NEW"]` |
| `notes` | string | Additional notes | `"Remember this!"` |
| `section` | string | Section grouping | `"setup"` |
| `omit_from_output` | boolean | Hide from docs | `true` |
| `wait_before` | float | Seconds before action | `0.5` |
| `wait_after` | float | Seconds after action | `0.5` |

## Troubleshooting

### Config-Driven Issues

**Steps not loading:**
- Check YAML syntax (indentation, colons)
- Ensure `sections` is under `documentation`
- Verify `wallet.add_steps_from_config()` is called

**Coordinates not resolving:**
- Check coordinate name matches exactly
- Ensure coordinates are under correct section
- Verify format: `coordinate_name: [x, y]`

### Appium Issues

**Can't find elements:**
- Use Appium Inspector to verify selectors
- Increase `implicit_wait` in config
- Try different selector strategies

**App doesn't launch:**
- Verify `app_path` in config
- Check Appium server is running: `appium`
- Ensure correct driver installed

### PyAutoGUI Issues

**Wrong coordinates:**
- Check `scale_factor` (2.0 for Retina)
- Use `record_clicks.py` to capture coordinates
- Ensure app window is in same position

**Screenshots missing:**
- Verify app is in foreground
- Increase `screenshot_delay`
- Check app has focus

### Documentation Issues

**Wrong screenshot paths:**
- Fixed automatically in master guide
- Section files use `../screenshots/`
- Master file uses `screenshots/`

**Missing sections:**
- Check section has steps defined
- Verify `sections_only` filter if used
- Ensure steps have `section` attribute

## Examples

See working examples:
- **BlindBit Desktop**: `wallets/blindbit/` - PyAutoGUI with config-driven approach
- **Demo Wallet**: `wallets/demo/` - Appium with code-driven approach

## Next Steps

1. Copy template and rename
2. Update `config.yaml` with your wallet details
3. Define steps in config (recommended) or code
4. Test with: `python scripts/run_wallet.py wallets/my-wallet/setup_walkthrough.py`
5. Review output in: `output/staging/my-wallet/`
6. Regenerate docs as needed with: `--docs-only`
7. Commit both script and generated docs

## Tips

1. **Start with config-driven** - easier to maintain
2. **Use named coordinates** - update once, apply everywhere
3. **Test incrementally** - add steps one at a time
4. **Use `--docs-only`** - fast iteration on docs
5. **Set crop regions** - cleaner screenshots
6. **Hide internal steps** - `omit_from_output: true`
7. **Organize with sections** - better document structure
8. **Mark feature changes** - use flags for clarity
