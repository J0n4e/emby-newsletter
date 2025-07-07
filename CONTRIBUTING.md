# Contributing to Emby Newsletter

Thank you for your interest in contributing to Emby Newsletter! This document provides guidelines and information for contributors.

## Getting Started

Before you start contributing, make sure to fork the Emby Newsletter repository to your GitHub account. You will be working on your forked repository and submitting pull requests from there.

### Development Setup

1. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/emby-newsletter.git
   cd emby-newsletter
   ```

2. **Set up a virtual environment:**
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

3. **Copy the config file and configure it:**
   Copy the `config/config-example.yml` to `./config/config.yml` and fill in the required fields. All fields are required.

   ```yaml
   emby:
     # URL of your emby server
     url: ""
     # API token of your emby server, see requirements for more info
     api_token: ""
     # List of folders to watch for new movies
     # You can find them in your Emby Dashboard -> Libraries -> Select a library -> Folder **WITHOUT THE TRAILING /**
     watched_film_folders:
       - ""
       # example for /movies folder add "movies"
     # List of folders to watch for new shows
     # You can find them in your Emby Dashboard -> Libraries -> Select a library -> Folder **WITHOUT THE TRAILING /**
     watched_tv_folders:
       - ""
       # example for /tv folder add "tv"
     # Number of days to look back for new items
     observed_period_days: 30

   tmdb:
     # TMDB API key, see requirements for more info
     api_key: ""

   # Email template to use for the newsletter
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

4. **Run the application:**
   ```bash
   python src/main.py
   ```

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. **Search existing issues** to see if your issue has already been reported.
2. **Create a new issue** with a clear title and description.
3. **Include relevant information** such as:
   - Emby server version
   - Python version
   - Operating system
   - Error messages or logs
   - Steps to reproduce the issue

### Submitting Changes

1. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bugfix-name
   ```

2. **Make your changes** following the coding standards below.

3. **Test your changes** thoroughly.

4. **Commit your changes** with clear, descriptive commit messages:
   ```bash
   git add .
   git commit -m "Add feature: description of what you added"
   ```

5. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a pull request** from your fork to the main repository.

### Pull Request Guidelines

- **Provide a clear description** of what your PR does
- **Reference any related issues** using keywords like "Fixes #123"
- **Include tests** if applicable
- **Update documentation** if you're adding new features
- **Follow the existing code style**

## Coding Standards

### Python Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and concise
- Handle errors gracefully with appropriate logging

### Example:

```python
def get_recent_items(self, days: int = 30, folders: List[str] = None) -> List[Dict]:
    """Get recently added items from Emby
    
    Args:
        days: Number of days to look back for new items
        folders: List of folder names to filter by
        
    Returns:
        List of recently added items
        
    Raises:
        Exception: If API request fails
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error(f"Error fetching recent items: {e}")
        return []
```

### Configuration Changes

- Always update the example configuration file when adding new options
- Document new configuration options in the README
- Ensure backward compatibility when possible

### Documentation

- Update README.md for new features or installation changes
- Keep documentation clear and concise
- Include examples where helpful

## Security

If you discover any security vulnerabilities or potential issues, please **DO NOT** open a public issue. Instead, use the following methods to report security issues:

- **GitHub Private vulnerability reporting** (preferred). You can find this option in the "Security" tab of the repository.
- **Email** at emby-newsletter-security[at]example.com

## Community Guidelines

We value a friendly and inclusive community. Be respectful and considerate when communicating with other contributors.

If you have questions or need help, feel free to ask through GitHub issues or discussions.

## Development Tips

### Testing

- Test with different Emby server versions when possible
- Test with various email providers
- Test error conditions (invalid API keys, network issues, etc.)

### Adding New Features

Before adding major new features, consider opening an issue to discuss the feature with maintainers and the community.

### Debugging

- Use the logging system for debugging information
- Check Emby server logs if API calls are failing
- Verify email settings with your email provider

## Getting Help

If you need help with development:

1. Check the existing documentation
2. Look at existing code for examples
3. Ask questions in GitHub issues
4. Reach out to maintainers

Thank you for contributing to Emby Newsletter!