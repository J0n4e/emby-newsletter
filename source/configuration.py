import yaml
import logging


class Scheduler:
    def __init__(self, data):
        if data is None or "cron" not in data:
            logging.info("No cron expression given. The newsletter will run once at startup and then stop.")
            self.enabled = False
        else:
            self.enabled = True
            self.cron = data["cron"]
            parsed_cron = self.cron.strip().split(" ")
            if len(parsed_cron) != 5:
                raise Exception(
                    f"[FATAL] Load config fail. Was expecting a valid cron expression in scheduler.cron, got {self.cron}")
            try:
                # The week of day, if an int, is 0-6, where 0 is Sunday, according to official/usual crontab expression
                # However, APScheduler, always starts week on Monday, so there is a shift of 1
                # We are fixing this, by modifying the cron expression, so 0-6 shift from mon-sun to sun-sat
                self.week_of_day = int(parsed_cron[4])
                self.week_of_day = (self.week_of_day - 1) % 7
                self.cron = " ".join(parsed_cron[:4]) + f" {self.week_of_day}"
            except:
                pass


class Server:
    required_keys = ["type", "url", "api_token", "watched_film_folders", "watched_tv_folders", "observed_period_days"]

    def __init__(self, data):
        for key in self.required_keys:
            if key not in data:
                raise Exception(f"[FATAL] Load config fail. Was expecting the key server.{key}")

        self.type = data["type"]
        if self.type not in ["jellyfin", "emby"]:
            raise Exception(f"[FATAL] Load config fail. server.type must be 'jellyfin' or 'emby', got {self.type}")
        self.url = data["url"]
        self.api_token = data["api_token"]
        self.watched_film_folders = data["watched_film_folders"]
        self.watched_tv_folders = data["watched_tv_folders"]
        self.observed_period_days = data["observed_period_days"]


class Tmdb:
    required_keys = ["api_key"]

    def __init__(self, data):
        for key in self.required_keys:
            if key not in data:
                raise Exception(f"[FATAL] Load config fail. Was expecting the key tmdb.{key}")
        self.api_key = data["api_key"]


class EmailTemplate:
    required_keys = ["language", "subject", "title", "subtitle", "server_url", "unsubscribe_email", "server_owner_name"]

    def __init__(self, data):
        for key in self.required_keys:
            if key not in data:
                raise Exception(f"[FATAL] Load config fail. Was expecting the key email_template.{key}")

        self.language = data["language"]
        self.subject = data["subject"]
        self.title = data["title"]
        self.subtitle = data["subtitle"]
        self.server_url = data["server_url"]
        self.unsubscribe_email = data["unsubscribe_email"]
        self.server_owner_name = data["server_owner_name"]


class Email:
    required_keys = ["smtp_server", "smtp_port", "smtp_username", "smtp_password", "smtp_sender_email"]

    def __init__(self, data):
        for key in self.required_keys:
            if key not in data:
                raise Exception(f"[FATAL] Load config fail. Was expecting the key email.{key}")
        self.smtp_server = data["smtp_server"]
        self.smtp_port = data["smtp_port"]
        self.smtp_user = data["smtp_username"]
        self.smtp_password = data["smtp_password"]
        self.smtp_sender_email = data["smtp_sender_email"]


class Config:
    required_keys = ["tmdb", "email_template", "email", "recipients"]

    def __init__(self, data):
        # Support backward compatibility
        if "jellyfin" in data and "server" not in data:
            data["server"] = data["jellyfin"]
            data["server"]["type"] = "jellyfin"

        # Check for either 'server' or 'jellyfin' key
        if "server" not in data and "jellyfin" not in data:
            logging.error(
                f"[FATAL] Load config fail. Was expecting the key 'server' (or 'jellyfin' for backward compatibility)")
            exit(1)

        # Backward compatibility for email_template fields
        if "email_template" in data:
            if "jellyfin_url" in data["email_template"] and "server_url" not in data["email_template"]:
                data["email_template"]["server_url"] = data["email_template"]["jellyfin_url"]
            if "jellyfin_owner_name" in data["email_template"] and "server_owner_name" not in data["email_template"]:
                data["email_template"]["server_owner_name"] = data["email_template"]["jellyfin_owner_name"]

        for key in self.required_keys:
            if key not in data:
                logging.error(f"[FATAL] Load config fail. Was expecting the key {key}")
                exit(1)

        if "debug" in data:
            if data["debug"]:
                logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
            else:
                logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        else:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        self.server = Server(data["server"])
        self.tmdb = Tmdb(data["tmdb"])
        self.email_template = EmailTemplate(data["email_template"])
        self.email = Email(data["email"])
        self.recipients = data["recipients"]
        self.scheduler = Scheduler(data["scheduler"]) if "scheduler" in data else Scheduler([])


try:
    with open("./config/config.yml") as config_yml:
        try:
            raw_conf = yaml.safe_load(config_yml)
            conf = Config(raw_conf)

        except yaml.YAMLError as exc:
            raise Exception(exc)
except Exception as e:
    raise Exception(f"[FATAL] API will stop now. Error while checking config file, {e}")