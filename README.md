# Emby Newsletter

A newsletter for Emby to notify your users of your latest additions. Emby Newsletter connects to the Emby API to retrieve recently added items and send them to your users.

It is fully customizable and can be run on a schedule using a cron job or a task scheduler.

![Emby Newsletter](https://github.com/J0n4e/emby-newsletter/raw/main/assets/newsletter-example.png)

## What it looks like

You can see examples of the newsletter in the [assets](https://github.com/J0n4e/emby-newsletter/tree/main/assets) folder.

## Features

- Retrieve the last added movies and TV shows from your Emby server
- Send a newsletter to your users with the last added items
- Retrieve the movie details from TMDB, including poster
- Group TV shows by seasons
- Fully customizable and responsive email template
- Easy to maintain, extend, setup and run
- Support for English and French
- Configure the list of recipients
- Configure specific folders to watch for new items

## Requirements

- Docker
- Emby API key - [How to generate an API key](https://github.com/J0n4e/emby-newsletter?tab=readme-ov-file#how-to-generate-an-emby-api-key)
- A TMDB API key (free) - [How to generate a TMDB API key](https://github.com/J0n4e/emby-newsletter?tab=readme-ov-file#how-to-generate-a-tmdb-api-key)
- A SMTP server

## Recommended installation: Docker

This is the default and recommended way to run the newsletter. The Docker container will run on a schedule using a built-in cron job. It will run on the schedule defined in the `config/config.yml` file.

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

5. Edit the `config/config.yml` file and fill in the required fields. All fields are required.

   ```yaml
   scheduler:
     # Crontab expression to send the newsletter.
     # Comment the scheduler section to disable the automatic sending of the newsletter. WARNING: IF COMMENTED, THE NEWSLETTER WILL BE RAN ONCE AT THE START OF THE CONTAINER.
     # Test your crontab expression here: https://crontab.guru/
     # This example will send the newsletter on the first day of every month at 8:00 AM
     cron: "0 8 1 * *"

   emby:
     # URL of your emby server
     url: ""
     # API token of your emby server, see requirements for more info
     api_token: ""
     # List of folders to watch for new movies
     # You can find them in your Emby Dashboard -> Libraries -> Select a library -> Folder **ONLY ADD THE LAST FOLDER NAME, WITHOUT ANY '/'**
     watched_film_folders:
       - ""
       # example for /media/movies folder add "movies"
     # List of folders to watch for new shows
     # You can find them in your Emby Dashboard -> Libraries -> Select a library -> Folder **ONLY ADD THE LAST FOLDER NAME, WITHOUT ANY '/'**
     watched_tv_folders:
       - ""
       # example for /media/tv folder add "tv"
     # Number of days to look back for new items
     observed_period_days: 30

   tmdb:
     # TMDB API key, see requirements for more info
     api_key: ""

   # Email template to use for the newsletter
   # You can use placeholders to dynamically insert values. See available placeholders here : https://github.com/J0n4e/emby-newsletter/wiki/How-to-use-placeholder
   email_template:
     # Language of the email, supported languages are "en" and "fr"
     language: "en"
     # Subject of the email
     subject: ""
     # Title of the email
     title: ""
     # Subtitle of the email
     subtitle: ""
     # Will be used to redirect the user to your Emby instance
     emby_url: ""
     # For the legal notice in the footer
     unsubscribe_email: ""
     # Used in the footer
     emby_owner_name: ""

   # SMTP server configuration, TLS is required for now
   # Check your email provider for more information
   email:
     # Example: GMail: smtp.gmail.com
     smtp_server: ""
     # Usually 587
     smtp_port:
     # The username of your SMTP account
     smtp_username: ""
     # The password of your SMTP account
     smtp_password: ""
     # Example: "emby@example.com" or to set display username "Emby <emby@example.com>"
     smtp_sender_email: ""

   # List of users to send the newsletter to
   recipients:
     - ""
     # Example: "name@example.com" or to set username "Name <name@example.com>"
   ```

6. Run the docker container with docker compose
   ```bash
   docker compose up -d
   ```

> **Note:** It is recommended to use a static version instead of `latest`, and manually upgrade. [Last version](https://github.com/J0n4e/emby-newsletter/releases)

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

3. Edit the `config/config.yml` file and fill in the required fields. All fields are required.
   ```yaml
   #scheduler:
     # Crontab expression to send the newsletter.
     # Comment the scheduler section to disable the automatic sending of the newsletter. WARNING: IF COMMENTED, THE NEWSLETTER WILL BE RAN ONCE AT THE START OF THE CONTAINER.
     # Test your crontab expression here: https://crontab.guru/
     # This example will send the newsletter on the first day of every month at 8:00 AM
     #cron: "0 8 1 * *"

   emby:
     # URL of your emby server
     url: ""
     # API token of your emby server, see requirements for more info
     api_token: ""
     # List of folders to watch for new movies
     # You can find them in your Emby Dashboard -> Libraries -> Select a library -> Folder **ONLY ADD THE LAST FOLDER NAME, WITHOUT ANY '/'**
     watched_film_folders:
       - ""
       # example for /media/movies folder add "movies"
     # List of folders to watch for new shows
     # You can find them in your Emby Dashboard -> Libraries -> Select a library -> Folder **ONLY ADD THE LAST FOLDER NAME, WITHOUT ANY '/'**
     watched_tv_folders:
       - ""
       # example for /media/tv folder add "tv"
     # Number of days to look back for new items
     observed_period_days: 30

   tmdb:
     # TMDB API key, see requirements for more info
     api_key: ""

   # Email template to use for the newsletter
   # You can use placeholders to dynamically insert values. See available placeholders here : https://github.com/J0n4e/emby-newsletter/wiki/How-to-use-placeholder
   email_template:
     # Language of the email, supported languages are "en" and "fr"
     language: "en"
     # Subject of the email
     subject: ""
     # Title of the email
     title: ""
     # Subtitle of the email
     subtitle: ""
     # Will be used to redirect the user to your Emby instance
     emby_url: ""
     # For the legal notice in the footer
     unsubscribe_email: ""
     # Used in the footer
     emby_owner_name: ""

   # SMTP server configuration, TLS is required for now
   # Check your email provider for more information
   email:
     # Example: GMail: smtp.gmail.com
     smtp_server: ""
     # Usually 587
     smtp_port:
     # The username of your SMTP account
     smtp_username: ""
     # The password of your SMTP account
     smtp_password: ""
     # Example: "emby@example.com" or to set display username "Emby <emby@example.com>"
     smtp_sender_email: ""

   # List of users to send the newsletter to
   recipients:
     - ""
     # Example: "name@example.com" or to set username "Name <name@example.com>"
   ```

4. Run the docker container to send the newsletter
   ```bash
   docker run --rm \
     -v ./config:/app/config \
     j0n4e/emby-newsletter:latest
   ```

> **Note:** It is recommended to use a static version instead of `latest`, and manually upgrade. [Last version](https://github.com/J0n4e/emby-newsletter/releases)

5. Schedule the script to run on a regular basis.
   ```bash
   # Unix :
   crontab -e
   # Add the following line to run the script every 1st of the month at 8am
   0 8 1 * * root docker run --rm -v PATH_TO_CONFIG_FOLDER/config:/app/config/ j0n4e/emby-newsletter:latest
   ```

## Current limitations

- Only supports English and French languages for the email template
- Only supports TLS for the SMTP server
- Only supports movies and TV shows for now
- Not available as an Emby plugin yet
- Must be run manually or scheduled

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

### How to generate a TMDB API key

1. Go to the [TMDB website](https://www.themoviedb.org/)
2. Create an account or log in
3. Go to your account settings
4. Click on the API section
5. Click on the `Create` button to create a new API key
6. Copy the API key named "API Read Access Token"
7. Paste it in the `config.yml` file under `tmdb.api_key`