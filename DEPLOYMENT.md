# Deployment Instructions

## Config File Deployment

Your slideshow configuration is stored in `~/.photo_slideshow_config.json` and contains your personal settings (people filters, timing preferences, etc.).

### Option 1: Automated Deployment (Recommended)

Use the provided deployment script:

```bash
# Deploy to a specific machine
./deploy_config.sh username@runtime-machine

# Or just the hostname if SSH keys are set up
./deploy_config.sh runtime-machine
```

On the target machine, move the file to the correct location:
```bash
mv ~/photo_slideshow_config.json ~/.photo_slideshow_config.json
```

### Option 2: Manual Copy

Copy your config file to the runtime machine:

```bash
# From your development machine
scp ~/.photo_slideshow_config.json username@runtime-machine:~

# On the runtime machine
mv ~/photo_slideshow_config.json ~/.photo_slideshow_config.json
```

### Option 3: Git-Based Deployment

If you want to include your config in version control (not recommended for personal settings):

```bash
# Copy to project directory
cp ~/.photo_slideshow_config.json config_user.json

# Commit and push
git add config_user.json
git commit -m "Add user config for deployment"
git push

# On runtime machine, after cloning
cp config_user.json ~/.photo_slideshow_config.json
```

## Why Not Commit User Configs Directly?

- Contains personal data (names of people in your photos)
- Different settings for different deployment scenarios
- Should remain private and user-specific
- Repository should contain templates/defaults, not personal configs

## Config File Contents

Your current config includes:
- Photo timer: 1 second
- Video max duration: 5 seconds
- People filter: ["Ally"]
- Voice commands enabled
- Various display and overlay settings

This file will be automatically loaded by the slideshow application on startup.
