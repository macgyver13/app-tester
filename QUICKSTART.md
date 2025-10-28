
## Quick Start Guide

Get your wallet documentation automated in 10 minutes.

## Prerequisites

- Python 3.9+
- A Bitcoin wallet app installed on your Mac
- 10 minutes

## Setup (2 minutes)

```bash
# Clone and setup
git clone <repo-url>
cd app-tester
```

## Create Your First Wallet Guide (8 minutes)

### 1. Copy the Template

```bash
cp -r wallets/template wallets/my-wallet
cd wallets/my-wallet
```

### 2. Update Basic Config

Edit `config.yaml`:

```yaml
wallet:
  name: "My Wallet"
```

### 3. Record Your Clicks (for PyAutoGui Automation)

Open your wallet app, then:

```bash
python scripts/record_clicks.py --interactive --setup-crop
```

**What to do:**

1. Click**upper-left** corner of the area to capture
2. Click**lower-right** corner of the area to capture
3. Click each button/field you want to document
4. Type a name for each coordinate (e.g.,`create_wallet`,`import_seed`)
5. Press**Ctrl+C** when done

### 4. Paste to Config

Copy the generated YAML output and paste it into your `config.yaml`:

```yaml
documentation:
  sections:
    setup:
      title: "Initial Setup"
      description: "Create and configure your wallet"
      crop: [100, 100, 800, 600]
      coordinates:
        create_wallet: [400, 300]
        import_seed: [400, 350]
      steps:
        - name: "Create Wallet"
          description: "Click to create a new wallet"
          action: "click"
          target: "create_wallet"
          screenshot: true
```

Update the section name, titles, and descriptions.

### 5. Run the Automation

```bash
python scripts/run_wallet.py wallets/my-wallet/setup_walkthrough.py
```

Screenshots are saved to `output/staging/my-wallet/`

### 6. Review & Regenerate

Edit descriptions in `config.yaml`, then regenerate docs **without re-running automation**:

```bash
python scripts/run_wallet.py wallets/my-wallet/setup_walkthrough.py --docs-only
```

### 7. Approve & Publish

Documentation is generated to `output/staging/` first. Review and approve when ready:

```bash
# Review what's staged
python scripts/review.py

# View specific wallet
python scripts/review.py my-wallet

# Approve and publish
python scripts/review.py my-wallet --approve
```

This moves documentation from `output/staging/my-wallet/` → `output/my-wallet/` (published).

## Next Steps

### Improve Your Documentation

**Edit `config.yaml` to add:**

- Better descriptions (multi-line = bullets)
- Notes for important steps
- Build instructions
- Troubleshooting tips

**Then regenerate and re-review:**

```bash
python scripts/run_wallet.py wallets/my-wallet/setup_walkthrough.py --docs-only
python scripts/review.py my-wallet --approve
```

### Adjust Screenshot Display Size

In `config.yaml`:

```yaml
documentation:
  screenshot_max_height: 600  # Adjust as needed
```

### Organize into Sections

Group steps into logical sections:

```yaml
sections:
  setup:
    title: "Initial Setup"
    steps: [...]

  usage:
    title: "Using the Wallet"
    steps: [...]
```

### Add Type Steps

For text input:

```yaml
- name: "Enter Seed Phrase"
  description: "Type your recovery phrase"
  action: "type"
  value: "your seed words here"
  screenshot: true
```

### Add Wait Steps

For loading screens:

```yaml
- name: "Wait for Sync"
  description: "Wait for blockchain sync"
  action: "wait"
  wait_time: 5
  screenshot: true
```

## Common Commands

```bash
# Record new coordinates
python scripts/record_clicks.py --interactive --setup-crop

# Run full automation (screenshots + docs)
python scripts/run_wallet.py wallets/my-wallet/setup_walkthrough.py

# Just regenerate docs (fast!)
python scripts/run_wallet.py wallets/my-wallet/setup_walkthrough.py --docs-only

# Run specific sections only
python scripts/run_wallet.py wallets/my-wallet/setup_walkthrough.py --sections setup
```

## Tips

1. **Start simple** - Record 3-5 clicks first, test, then add more
2. **Use `--docs-only`** - Fast iteration on descriptions and formatting
3. **Name coordinates clearly** -`create_wallet` not`button1`
4. **Group by section** -`setup`,`usage`,`advanced` keeps it organized
5. **Test incrementally** - Add one step, test, repeat

## Example: See BlindBit Wallet

```bash
# View working example
cat wallets/blindbit/config.yaml

# Run the example
python scripts/run_wallet.py wallets/blindbit/setup_walkthrough.py --docs-only

# View generated docs
open output/staging/blindbit_desktop/user-guide.md
```

## Troubleshooting

### Wrong Coordinates

- Check your`scale_factor` in`setup_walkthrough.py` (2.0 for Retina displays)
- Re-record with`record_clicks.py`

### Screenshots Too Large

- Adjust`screenshot_max_height` in`config.yaml`
- Default is 600px

### Clicks Missing Target

- Increase`wait_before` in step definition
- Make sure app window is in same position
- Use`--setup-crop` to ensure consistent framing

### YAML Errors

- Check indentation (use spaces, not tabs)
- Ensure colons have space after them
- Use`|` for multi-line strings

## Need Help?

- Review working examples in`wallets/blindbit/`
- See`wallets/template/README.md` for all features
