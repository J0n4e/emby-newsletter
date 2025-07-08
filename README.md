# Emby Newsletter

A newsletter for Emby to notify your users of your latest additions. Emby Newsletter connects to the Emby API to retrieve recently added items and send them to your users.

It is fully customizable and can be run on a schedule using a cron job or a task scheduler.

## What it looks like

![Emby Newsletter](https://github.com/J0n4e/emby-newsletter/raw/main/assets/newsletter-example.jpg)

## Features

- Retrieve the last added movies and TV shows from your Emby server
- Send a newsletter to your users with the last added items
- Professional dark theme with red accents
- Retrieve the movie details from TMDB, including poster
- Group TV shows by seasons with episode details
- Fully customizable and responsive email template
- Built-in cron scheduler with security-compliant setup
- Easy to maintain, extend, setup and run
- English language support
- Configure the list of recipients
- Configure specific folders to watch for new items

## Requirements

- Docker
- Emby API key - [How to generate an Emby API key](#how-to-generate-an-emby-api-key)
- A TMDB API key (free) - [How to generate a TMDB API key](#how-to-generate-a-tmdb-api-key)
- A SMTP server

## Installation Methods

### Option 1: Unraid (Recommended for Unraid Users)

For Unraid users, you can install this as a Docker container using the provided template:

1. **Download the Unraid template**: [emby-newsletter.xml](https://raw.githubusercontent.com/J0n4e/emby-newsletter/main/assets/emby-newsletter.xml)
2. **Install the template**:
   - Save the template file to `/boot/config/plugins/dockerMan/templates-user/` on your Unraid server
   - Go to **Docker** tab in Unraid
   - Click **Add Container** 
   - The template will appear in your local templates list
3. **Configure your settings** in the template fields
4. **Click Apply** to install and start the container

The Unraid template includes:
- Pre-configured security settings with read-only filesystem
- Built-in cron support with proper permissions
- Easy timezone and scheduling configuration
- Optional pre-filling of API keys and settings
- Secure tmpfs mounts for optimal performance

### Option 2: Docker Compose (Recommended for other systems)

This is the default and recommended way to run the newsletter. The Docker container will run on a schedule using a built-in cron job.

1. Download the [docker-compose.yml](https://raw.githubusercontent.com/J0n4e/emby-newsletter/refs/heads/main/docker-compose.yml) file:
   ```bash
   curl -o docker-compose.yml https://raw.githubusercontent.com/J0n4e/emby-newsletter/refs/heads/main/docker-compose.yml
   ```

2. (optional) Edit the `docker-compose.yml` file to change the default user or timezone.

3. Create a `config` folder in the same directory as the `docker-compose.yml` file:
   ```bash
   mkdir config
   ```

4. Download the [config file](https://raw.githubusercontent.com/J0n4e/emby-newsletter/refs/heads/main/config/config-example.yml) in the `config` folder:
   ```bash
   curl -o config/config.yml https://raw.githubusercontent.com/J0n4e/emby-newsletter/refs/heads/main/config/config-example.yml
   ```

5. Edit the `config/config.yml` file and fill in the required fields. See the [Configuration](#configuration) section below for details.

6. Run the docker container with docker compose
   ```bash
   docker compose up -d
   ```

> **Note:** It is recommended to use a static version instead of `latest`, and manually upgrade. [Last version](https://github.com/J0n4e/emby-newsletter/releases)

## Configuration

Here's a complete example configuration file with explanations:

```yaml
# Emby Newsletter Configuration Example
# Copy this file to config.yml and fill in your details

scheduler:
  # Uncomment and set your desired schedule (cron format)
  # Examples:
  # "0 8 * * *"     - Daily at 8 AM
  # "0 8 * * 1"     - Weekly on Monday at 8 AM  
  # "0 8 1 * *"     - Monthly on 1st at 8 AM
  # "0 8 1,15 * *"  - Twice monthly (1st and 15th) at 8 AM
  # Test your cron expression: https://crontab.guru/
  #cron: "0 8 1 * *"

emby:
  # Your Emby server URL (include http:// or https://)
  url: "http://YOUR_SERVER_IP:PORT"
  
  # Your Emby API token
  # How to get: Dashboard > Advanced > API Keys > Create new key
  api_token: "YOUR_API_TOKEN_HERE"
  
  # List of movie folders to watch for new content
  # Use the folder name as it appears in Emby
  # Example: if your path is /media/movies, use "movies"
  watched_film_folders:
    - "movies"
    # - "4k-movies"
    # - "foreign-films"
  
  # List of TV show folders to watch for new content
  watched_tv_folders:
    - "tvshows"
    # - "anime"
    # - "documentaries"
  
  # Number of days to look back for new content
  observed_period_days: 7

tmdb:
  # TMDB API key for movie posters and details (free account required)
  # Get yours at: https://www.themoviedb.org/settings/api
  # Use the "API Read Access Token" (starts with eyJ...)
  api_key: "YOUR_TMDB_API_READ_ACCESS_TOKEN"

email_template:
  # Language for the email template
  language: "en"
  
  # Email subject line
  subject: "New content on your media server!"
  
  # Main title in the email
  title: "Media Server Newsletter"
  
  # Subtitle text
  subtitle: "Recently added movies and TV shows"
  
  # URL to your Emby server (for "Visit Server" button)
  emby_url: "http://YOUR_SERVER_IP:PORT"
  
  # Contact email for unsubscribe requests
  unsubscribe_email: "admin@yourdomain.com"
  
  # Your server name (appears in email footer)
  emby_owner_name: "Your Media Server"

email:
  # SMTP server settings for sending emails
  # Common examples:
  # Gmail: smtp.gmail.com (port 587)
  # Outlook: smtp.live.com (port 587) 
  # Yahoo: smtp.mail.yahoo.com (port 587)
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  
  # Your email account credentials
  smtp_username: "your-email@gmail.com"
  
  # For Gmail: Use an "App Password" instead of your regular password
  # How to get Gmail App Password: https://support.google.com/mail/answer/185833
  smtp_password: "your-app-password-here"
  
  # Sender email and display name
  # Format: "Display Name <email@domain.com>" or just "email@domain.com"
  smtp_sender_email: "Your Media Server <your-email@gmail.com>"

# List of email recipients
recipients:
  - "user1@example.com"
  - "user2@example.com"
  # - "family@example.com"
  # You can add as many recipients as needed
```

### Alternative: Docker without cron

Use this method if you want to run the script on a schedule using an external cron job or task scheduler, instead of the built-in cron job. Docker will run once, and exit after sending the newsletter.

1. Create a `config` folder.
   ```bash
   mkdir config
   ```

2. Download the [config file](https://raw.githubusercontent.com/J0n4e/emby-newsletter/refs/heads/main/config/config-example.yml) in the `config` folder:
   ```bash
   curl -o config/config.yml https://raw.githubusercontent.com/J0n4e/emby-newsletter/refs/heads/main/config/config-example.yml
   ```

3. Edit the `config/config.yml` file and fill in the required fields. **Important:** Comment out the `scheduler` section to disable built-in cron:
   ```yaml
   #scheduler:
     # Comment this section to disable built-in scheduling
     #cron: "0 8 1 * *"
   ```

4. Run the docker container to send the newsletter
   ```bash
   docker run --rm \
     -v ./config:/app/config \
     ghcr.io/j0n4e/emby-newsletter:latest
   ```

> **Note:** It is recommended to use a static version instead of `latest`, and manually upgrade. [Last version](https://github.com/J0n4e/emby-newsletter/releases)

5. Schedule the script to run on a regular basis.
   ```bash
   # Unix :
   crontab -e
   # Add the following line to run the script every 1st of the month at 8am
   0 8 1 * * root docker run --rm -v PATH_TO_CONFIG_FOLDER/config:/app/config/ ghcr.io/j0n4e/emby-newsletter:latest
   ```

## Security Features

This newsletter application is built with security in mind:

- **Read-only filesystem** - Container runs with read-only root filesystem
- **Secure tmpfs mounts** - Temporary files use memory-based storage with security restrictions  
- **No privilege escalation** - Container runs with `no-new-privileges:true`
- **Input sanitization** - All user data is properly escaped and validated
- **XSS protection** - Multiple layers of protection against cross-site scripting
- **Security scanning** - Code is regularly scanned with Semgrep for vulnerabilities

## Current limitations

- Email template language is currently set to English
- Only supports TLS for the SMTP server
- Only supports movies and TV shows for now
- Not available as an Emby plugin yet
- Must be run manually or scheduled

## Acknowledgments

This project was inspired by and builds upon the excellent work of [SeaweedbrainCY](https://github.com/SeaweedbrainCY) and his [jellyfin-newsletter](https://github.com/SeaweedbrainCY/jellyfin-newsletter) project. 

**Special thanks to SeaweedbrainCY for:**
- Providing the original concept and inspiration
- Creating the foundation that made this project possible
- Demonstrating how to integrate with Jellyfin/Emby APIs
- Inspiring the community to build better media server tools

This emby-newsletter project extends that foundation with enhanced security, professional styling, improved email templates, and additional features while maintaining the same core philosophy of keeping users informed about their media libraries. 🙏

If you're looking for a Jellyfin-specific solution, definitely check out the [original jellyfin-newsletter](https://github.com/SeaweedbrainCY/jellyfin-newsletter) project!

## License

This project is licensed under the MIT License—see the [LICENSE](LICENSE) file for details.

## Contribution

Feel free to contribute to this project by opening an issue or a pull request.

A contribution guide is available in the [CONTRIBUTING.md](CONTRIBUTING.md) file.

If you like this project, consider giving it a ⭐️.

If you encounter any issues, please let me know by opening an issue.

## How to

### How to generate an Emby API key

1. Go to your Emby dashboard
2. Scroll to advanced section and click on API keys
3. Click on the `+` button to create a new API key
4. Fill in the required fields and click on save
5. Copy the generated API key
6. Paste it in the `config.yml` file under `emby.api_token`

> **Note:** This project primarily focuses on Emby servers. While it may work with Jellyfin, it has been specifically designed and tested with Emby.

### How to generate a TMDB API key

1. Go to the [TMDB website](https://www.themoviedb.org/)
2. Create an account or log in
3. Go to your account settings
4. Click on the API section
5. Click on the `Create` button to create a new API key
6. Copy the API key named "API Read Access Token" (starts with `eyJ...`)
7. Paste it in the `config.yml` file under `tmdb.api_key`

### Gmail Setup Guide

For Gmail users, you'll need to use an App Password instead of your regular password:

1. **Enable 2-Factor Authentication** on your Google account
2. **Go to** [Google App Passwords](https://myaccount.google.com/apppasswords)
3. **Generate a new App Password** for "Mail"
4. **Use this App Password** in your `smtp_password` field
5. **Set smtp_server** to `smtp.gmail.com` and **smtp_port** to `587`

More details: [Gmail SMTP Settings](https://support.google.com/mail/answer/185833)