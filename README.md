# Emby/Jellyfin Newsletter - Keep Your Users Updated

<p align="center">
<img src="https://github.com/j0n4e/emby-newsletter/actions/workflows/build_and_deploy.yml/badge.svg?branch=main"/>
 <img src="https://img.shields.io/github/license/j0n4e/emby-newsletter"/>
<img src="https://img.shields.io/github/v/release/j0n4e/emby-newsletter"/>
</p>


A newsletter service for Emby and Jellyfin media servers to notify your users of the latest additions. This application connects to your media server's API to retrieve recently added items and sends beautifully formatted newsletters to your users.

It is fully customizable and can be run on a schedule using a cron job or a task scheduler.

## Table of Contents
1. [What it looks like](#what-it-looks-like)
2. [Features](#features)
3. [Supported Media Servers](#supported-media-servers)
4. [Recommended installation: Docker](#recommended-installation-docker)
5. [Manual Installation](#manual-installation)
6. [Current limitations](#current-limitations)
7. [License](#license)
8. [Contribution](#contribution)
9. [How to](#how-to)
   - [How to generate an Emby API key](#how-to-generate-an-emby-api-key)
   - [How to generate a Jellyfin API key](#how-to-generate-a-jellyfin-api-key)
   - [How to generate a TMDB API key](#how-to-generate-a-tmdb-api-key)
10. [Credits](#credits)

## What it looks like 
<p align="center">
<img src="https://raw.githubusercontent.com/J0n4e/emby-newsletter/refs/heads/main/assets/emby_newsletter.jpg" width=500>
</p>

## Features
- **Multi-platform support**: Works with both Emby and Jellyfin media servers
- Retrieve the last added movies and TV shows from your media server
- Send newsletters to your users with the latest added items
- Retrieve movie details from TMDB, including posters
- Configure the list of recipients
- Configure specific folders to watch for new items
- Built-in scheduler with cron expressions
- Docker support with automatic updates

## Supported Media Servers
- **Emby** - Full support
- **Jellyfin** - Full support

## Recommended installation: Docker

### Requirements
- Docker 
- Media server (Emby or Jellyfin) API key
- A TMDB API key (free) - [How to generate a TMDB API key](#how-to-generate-a-tmdb-api-key)
- A SMTP server 

### Configuration with built-in cron job
This is the default and recommended way to run the newsletter. The Docker container will run on a schedule using a built-in cron job.

1. Download the [docker-compose.yml](https://raw.githubusercontent.com/j0n4e/emby-newsletter/main/docker-compose.yml) file:
```bash 
curl -o docker-compose.yml https://raw.githubusercontent.com/j0n4e/emby-newsletter/main/docker-compose.yml
```

2. (optional) Edit the `docker-compose.yml` file to change the default user or timezone.

3. Create a `config` folder in the same directory as the `docker-compose.yml` file:
```bash
mkdir config
```

4. Download the [config file](https://raw.githubusercontent.com/j0n4e/emby-newsletter/main/config/config-example.yml) in the `config` folder:
```bash
curl -o config/config.yml https://raw.githubusercontent.com/j0n4e/emby-newsletter/main/config/config-example.yml
```

5. Edit the `config/config.yml` file and fill in the required fields. **All fields are required.**

```yaml
scheduler:
    # Crontab expression to send the newsletter. 
    # Comment the scheduler section to disable the automatic sending of the newsletter. 
    # WARNING: IF COMMENTED, THE NEWSLETTER WILL BE RAN ONCE AT THE START OF THE CONTAINER.
    # Test your crontab expression here: https://crontab.guru/
    # This example will send the newsletter on the first day of every month at 8:00 AM
    cron: "0 8 1 * *"

server:
    # Type of server: "jellyfin" or "emby"
    type: "emby"

    # URL of your media server
    url: "http://your-server:8096" 

    # API token of your media server, see requirements for more info
    api_token: "your-api-token-here"

    # List of folders to watch for new movies 
    # You can find them in your Dashboard -> Libraries -> Select a library -> Folder 
    # **ONLY ADD THE LAST FOLDER NAME, WITHOUT ANY '/'**
    watched_film_folders:
        - "movies"
        # example for /media/movies folder add "movies"

    # List of folders to watch for new shows
    # You can find them in your Dashboard -> Libraries -> Select a library -> Folder 
    # **ONLY ADD THE LAST FOLDER NAME, WITHOUT ANY '/'**
    watched_tv_folders:
        - "tv"
        # example for /media/tv folder add "tv"
  
    # Number of days to look back for new items
    observed_period_days: 30

tmdb:
    # TMDB API key, see requirements for more info
    api_key: "your-tmdb-api-key"

# Email template to use for the newsletter
# You can use placeholders to dynamically insert values. 
# See available placeholders in the wiki
email_template:
    # Language of the email, supported languages are "en"
    language: "en"
    # Subject of the email
    subject: "Weekly Newsletter"
    # Title of the email
    title: "New Content Available!"
    # Subtitle of the email
    subtitle: "Check out what's new on your media server"
    # Will be used to redirect the user to your media server instance
    server_url: "http://your-server:8096"
    # For the legal notice in the footer
    unsubscribe_email: "admin@yourdomain.com"
    # Used in the footer
    server_owner_name: "Your Name"

# SMTP server configuration, TLS is required for now
# Check your email provider for more information
email:
    # Example: Gmail: smtp.gmail.com
    smtp_server: "smtp.gmail.com"
    # Usually 587
    smtp_port: 587
    # The username of your SMTP account
    smtp_username: "your-email@gmail.com"
    # The password of your SMTP account
    smtp_password: "your-app-password"
    # Example: "server@example.com" or to set display username "Media Server <server@example.com>"
    smtp_sender_email: "Media Server <your-email@gmail.com>"

# List of users to send the newsletter to
recipients:
  - "user1@example.com"
  - "user2@example.com"
  # Example: "name@example.com" or to set username "Name <name@example.com>"
```

6. Run the docker container with docker compose:
```bash
docker compose up -d
```

> [!NOTE]
> It is recommended to use a static version instead of `latest`, and manually upgrade. Check the [releases page](https://github.com/j0n4e/emby-newsletter/releases) for the latest version.

### Configuration with external cron job
Use this method if you want to run the script on a schedule using an external cron job or task scheduler.

1. Create a `config` folder and download the config file as shown above.

2. Comment out the scheduler section in your `config.yml`:
```yaml
#scheduler:
    # Crontab expression to send the newsletter. 
    #cron: "0 8 1 * *"
```

3. Run the docker container to send the newsletter once:
```bash
docker run --rm \
    -v ./config:/app/config \
    ghcr.io/j0n4e/emby-newsletter:latest
```

4. Schedule the script to run on a regular basis using your system's cron:
```bash
# Unix example - run every 1st of the month at 8am
crontab -e
# Add this line:
0 8 1 * * docker run --rm -v /path/to/config:/app/config ghcr.io/j0n4e/emby-newsletter:latest
```

## Manual Installation

### Requirements
- Python 3.9+ 
- Media server (Emby or Jellyfin) API key
- A TMDB API key (free)
- A SMTP server 

### Installation steps

1. Clone the repository:
```bash
git clone https://github.com/j0n4e/emby-newsletter.git
cd emby-newsletter
```

2. Install the required packages:
```bash
# Unix:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Windows:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. Copy the config file and configure it:
```bash
cp config/config-example.yml config/config.yml
```

4. Edit `config/config.yml` with your settings (see Docker configuration example above).

5. Make sure to support the following locales:
- `en_US.UTF-8 UTF-8`

On Debian-based systems:
```bash
sudo sed -i 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
sudo locale-gen
```

6. Run the script:
```bash
python main.py
```

## Current limitations
- Only supports English language for the email template
- Only supports TLS for the SMTP server
- Only supports movies and TV shows for now
- Not available as a media server plugin yet 
- Must be run manually or scheduled

## License
This project is licensed under the MIT License—see the [LICENSE](LICENSE) file for details.

## How to 

### How to generate an Emby API key
1. Go to your Emby dashboard
2. Navigate to Advanced → API Keys
3. Click on the `+` button to create a new API key
4. Fill in the required fields and click save
5. Copy the generated API key
6. Paste it in the `config.yml` file under `server.api_token`

### How to generate a Jellyfin API key
1. Go to your Jellyfin dashboard
2. Scroll to advanced section and click on API keys
3. Click on the `+` button to create a new API key
4. Fill in the required fields and click on save
5. Copy the generated API key
6. Paste it in the `config.yml` file under `server.api_token`

### How to generate a TMDB API key
1. Go to the [TMDB website](https://www.themoviedb.org/)
2. Create an account or log in
3. Go to your account settings
4. Click on the API section
5. Click on the `Create` button to create a new API key
6. Copy the API key named "API Read Access Token"
7. Paste it in the `config.yml` file under `tmdb.api_key`

## Credits

This project is based on the excellent [jellyfin-newsletter](https://github.com/SeaweedbrainCY/jellyfin-newsletter) by [SeaweedbrainCY](https://github.com/SeaweedbrainCY). The original project was designed specifically for Jellyfin servers and provided the foundation for this enhanced version.

Special thanks to SeaweedbrainCY for creating the original codebase and making it available under an open-source license, which made this multi-platform adaptation possible.

### Original Project
- **Original Repository**: [jellyfin-newsletter](https://github.com/SeaweedbrainCY/jellyfin-newsletter)
- **Original Author**: [SeaweedbrainCY](https://github.com/SeaweedbrainCY)
- **Original License**: MIT License