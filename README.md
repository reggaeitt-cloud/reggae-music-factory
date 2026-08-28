# Reggae Music Factory

Automated two-per-day reggae music publishing pipeline.

## Current mode

- Generates one original reggae track per run through Treblo Melodia v3.
- Creates a simple audio-reactive visualizer video.
- Generates rotating fictional singer, producer, and writer credits.
- Uploads to YouTube as **Private** for initial quality review.
- Intended schedule: two runs per day.

## Security

Never commit API keys, OAuth client secrets, refresh tokens, or generated credentials to this repository.

## Setup

The remaining setup is performed through GitHub Actions secrets and the user's YouTube OAuth authorization. The first generated uploads remain private until manually approved.
