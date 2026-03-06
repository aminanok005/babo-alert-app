# Push Images to GitHub Container Registry (ghcr.io)

## Step 1: Create GitHub Personal Access Token (PAT)

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Give it a name (e.g., "babo-alert-push")
4. Select scope: `write:packages`
5. Click **"Generate token"**
6. Copy the token (starts with `ghp_`)

## Step 2: Login to GitHub Container Registry

Run this command and enter your GitHub username and the PAT as password:

```bash
sudo nerdctl login ghcr.io -u YOUR_GITHUB_USERNAME
```

## Step 3: Push Images

After logging in, run:

```bash
# Push quran-app
sudo nerdctl push ghcr.io/aminanok005/babo-alert-app:latest

# Push n8n
sudo nerdctl push ghcr.io/aminanok005/babo-alert-app-n8n:latest
```

## Alternative: Using echo for password

```bash
echo "ghp_YOUR_PAT_TOKEN" | sudo nerdctl login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

## After Push - Use in Replit

In your Replit babo-alert-app, update to use:
- `ghcr.io/aminanok005/babo-alert-app:latest` (for quran-app)
- `ghcr.io/aminanok005/babo-alert-app-n8n:latest` (for n8n)
