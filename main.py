import sys
from source import configuration, TmdbAPI, email_template, email_controller
import datetime as dt
from source.configuration import logging
from source.configuration_checker import check_configuration
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Import the correct API based on server type
if configuration.conf.server.type == "emby":
    from source import EmbyAPI as ServerAPI
else:
    from source import JellyfinAPI as ServerAPI


def populate_series_item_from_episode(series_items, item):
    """
    Populate the series item with required information to build the email content.
    It takes an episode, populate the serie item with the episode information, and add the episode to the series item.
    series_items format :
    {
        "SeriesName": {
            "created_on": "2023-10-01T12:00:00Z", # Creation date of the series item, i.e. of added season or the added episode, or the series itfself
            "description": "This is a series description.", # Since episode rarely includes TMBD id, even if the episode is alone, we will use the series description.
            "year": 2023, # Production year of the series, provided by server
            "poster": "", # Poster of the series, provided by TMDB
            "seasons": [""] # List of seasons in the series, provided by server
            "episodes" : [""]
        }
    }
    """

    if "SeriesName" not in item.keys():
        logging.warning(f"Item {item['Name']} has no SeriesName. Skipping.")
        return
    if item["SeriesName"] not in series_items.keys():
        series_items[item["SeriesName"]] = {
            "episodes": [],
            "seasons": [],
            "created_on": "undefined",
            "description": "No description available.",  # will be populated later, when parsing the series item
            "year": "undefined",  # will be populated later, when parsing the series item
            "rating": 0,
            "poster": "https://redthread.uoregon.edu/files/original/affd16fd5264cab9197da4cd1a996f820e601ee4.png"
            # will be populated later, when parsing the series item
        }
    if item["SeasonName"] not in series_items[item["SeriesName"]]["seasons"]:
        series_items[item["SeriesName"]]["seasons"].append(item["SeasonName"])
    series_items[item["SeriesName"]]["episodes"].append(item.get('IndexNumber'))
    if series_items[item["SeriesName"]]["created_on"] != "undefined" or series_items[item["SeriesName"]][
        "created_on"] is not None:
        try:
            if dt.datetime.fromisoformat(series_items[item["SeriesName"]]["created_on"]) < dt.datetime.fromisoformat(
                    item["DateCreated"]):
                series_items[item["SeriesName"]]["created_on"] = item["DateCreated"]
        except:
            pass
    series_items[item["SeriesName"]]["created_on"] = item.get("DateCreated", "undefined")


def populate_series_item_with_series_related_information(series_items, watched_tv_folders_id):
    """
    populate_series_item_from_episode will populate the series item with the episode information, but it will not include the series information (description, year, poster).
    This function will populate the series item with the series information.
    """
    for folder_id in watched_tv_folders_id:
        for serie_name in series_items.keys():
            item = ServerAPI.get_item_from_parent_by_name(parent_id=folder_id, name=serie_name)
            if item is not None:
                series_year = item.get("ProductionYear")
                if series_year == 0 or series_year is None:
                    series_year_for_tmdb = None
                    series_year_for_display = "N/A"
                else:
                    series_year_for_tmdb = series_year
                    series_year_for_display = series_year
                series_items[item['Name']]["year"] = series_year_for_display
                tmdb_id = None
                if "ProviderIds" in item.keys():
                    if "Tmdb" in item["ProviderIds"].keys():
                        tmdb_id = item["ProviderIds"]["Tmdb"]

                if tmdb_id is not None:  # id provided by server
                    tmdb_info = TmdbAPI.get_media_detail_from_id(id=tmdb_id, type="tv")
                else:
                    logging.info(f"Item {item['Name']} has no TMDB id, searching by title.")
                    tmdb_info = TmdbAPI.get_media_detail_from_title(title=item["Name"], type="tv",
                                                                    year=series_year_for_tmdb)

                if tmdb_info is None:
                    logging.warning(f"Item {item['Name']} has not been found on TMDB. Skipping.")
                else:
                    if "overview" not in tmdb_info.keys():
                        logging.warning(f"Item {item['Name']} has no overview.")
                        tmdb_info["overview"] = "No overview available."
                    series_items[item['Name']]["description"] = tmdb_info["overview"]
                    series_items[item['Name']]["rating"] = f"{tmdb_info.get('vote_average', 0):.1f}/10"
                    series_items[item['Name']][
                        "poster"] = f"https://image.tmdb.org/t/p/w500{tmdb_info['poster_path']}" if tmdb_info[
                        "poster_path"] else "https://redthread.uoregon.edu/files/original/affd16fd5264cab9197da4cd1a996f820e601ee4.png"
            else:
                logging.warning(f"Item {serie_name} has not been found in server. Skipping.")


def send_newsletter():
    logging.info("Sending newsletter ...")
    folders = ServerAPI.get_root_items()
    watched_film_folders_id = []
    watched_tv_folders_id = []
    for item in folders:
        if item["Name"] in configuration.conf.server.watched_film_folders:
            watched_film_folders_id.append(item["Id"])
            logging.info(f"Folder {item['Name']} is watched for films.")
        elif item["Name"] in configuration.conf.server.watched_tv_folders:
            watched_tv_folders_id.append(item["Id"])
            logging.info(f"Folder {item['Name']} is watched for TV series.")
        else:
            logging.warning(
                f"Folder {item['Name']} is not watched. Skipping. Add \"{item['Name']}\" in your watched folder to include it.")

    total_movie = 0
    total_tv = 0
    movie_items = {}
    series_items = {}

    for folder_id in watched_film_folders_id:
        items, total_count = ServerAPI.get_item_from_parent(parent_id=folder_id, type="movie",
                                                            minimum_creation_date=dt.datetime.now() - dt.timedelta(
                                                                days=configuration.conf.server.observed_period_days))
        total_movie += total_count
        for item in items:
            logging.debug(f"Processing movie item: {item}")
            tmdb_id = None
            movie_year = item.get("ProductionYear")
            if movie_year == 0 or movie_year is None:
                movie_year_for_tmdb = None
                movie_year_for_display = "N/A"
            else:
                movie_year_for_tmdb = movie_year
                movie_year_for_display = movie_year

            if "DateCreated" not in item.keys():
                logging.warning(f"Item {item['Name']} has no creation date.")
                item["DateCreated"] = None
            if "ProviderIds" in item.keys():
                if "Tmdb" in item["ProviderIds"].keys():
                    tmdb_id = item["ProviderIds"]["Tmdb"]

            if tmdb_id is not None:  # id provided by server
                tmdb_info = TmdbAPI.get_media_detail_from_id(id=tmdb_id, type="movie")
            else:
                logging.info(f"Item {item['Name']} has no TMDB id, searching by title.")
                tmdb_info = TmdbAPI.get_media_detail_from_title(title=item["Name"], type="movie",
                                                                year=movie_year_for_tmdb)

            if tmdb_info is None:
                logging.warning(f"Item {item['Name']} has not been found on TMDb. Skipping.")
                movie_items[item["Name"]] = {
                    "year": movie_year_for_display,
                    "created_on": item["DateCreated"],
                    "description": "No description available.",
                    "rating": "N/A",
                    "poster": "https://redthread.uoregon.edu/files/original/affd16fd5264cab9197da4cd1a996f820e601ee4.png"
                }
            else:
                if "overview" not in tmdb_info.keys():
                    logging.warning(f"Item {item['Name']} has no overview.")
                    tmdb_info["overview"] = "No overview available."

                movie_items[item["Name"]] = {
                    "year": movie_year_for_display,
                    "created_on": item["DateCreated"],
                    "description": tmdb_info["overview"],
                    "rating": f"{tmdb_info.get('vote_average', 0):.1f}/10",
                    "poster": f"https://image.tmdb.org/t/p/w500{tmdb_info['poster_path']}" if tmdb_info[
                        "poster_path"] else "https://redthread.uoregon.edu/files/original/affd16fd5264cab9197da4cd1a996f820e601ee4.png"
                }

    for folder_id in watched_tv_folders_id:
        items, total_count = ServerAPI.get_item_from_parent(parent_id=folder_id, type="tv",
                                                            minimum_creation_date=dt.datetime.now() - dt.timedelta(
                                                                days=configuration.conf.server.observed_period_days))
        total_tv += total_count
        for item in items:
            if item["Type"] == "Episode":
                populate_series_item_from_episode(series_items, item)

    populate_series_item_with_series_related_information(series_items=series_items,
                                                         watched_tv_folders_id=watched_tv_folders_id)
    logging.debug("Series populated : " + str(series_items))
    if len(movie_items) + len(series_items) > 0:
        total_movies_on_server, total_tv_on_server = ServerAPI.get_server_statistics(watched_film_folders_id, watched_tv_folders_id)
        template = email_template.populate_email_template(movies=movie_items, series=series_items, total_tv=total_tv,
                                                          total_movie=total_movie, total_movies_on_server=total_movies_on_server, total_tv_on_server=total_tv_on_server)

        email_controller.send_email(template)

        logging.info("All emails sent.")
    else:
        logging.warning("No new items found in watched folders. No email sent.")

    server_name = "Jellyfin" if configuration.conf.server.type == "jellyfin" else "Emby"
    logging.info(f"""


##############################################
Newsletter sent. 
Thanks for using {server_name} Newsletter!
Developed by Seaweedbrain, under MIT License.""")


def newsletter_job():
    """
    Used to run the newsletter, called by scheduler.
    Used to handle exceptions and logging.
    """
    try:
        send_newsletter()
    except Exception as e:
        logging.error(f"[FATAL] An error occurred while sending the newsletter: {e}")
        logging.error("Sending newsletter failed. Program will continue to run and retry at the next scheduled time.")


if __name__ == "__main__":
    server_name = "Jellyfin" if configuration.conf.server.type == "jellyfin" else "Emby"
    logging.info(f"""

{server_name} Newsletter is starting ....
##############################################



""")
    logging.info("Checking configuration ...")
    try:
        check_configuration()
    except Exception as e:
        logging.error(f"[FATAL] Configuration check failed: {e}")
        sys.exit(1)
    logging.info("Configuration check passed.")

    if configuration.conf.scheduler.enabled:
        try:
            scheduler = BlockingScheduler()
            trigger = CronTrigger().from_crontab(configuration.conf.scheduler.cron)
        except Exception as e:
            logging.error(f"[FATAL] Failed to initialize scheduler: {e}")
            sys.exit(1)

        scheduler.add_job(newsletter_job, trigger)
        logging.info(
            f"Newsletter scheduler started. Next run at {trigger.get_next_fire_time(None, dt.datetime.now()).isoformat()}")
        scheduler.start()

    else:
        logging.info("Scheduler is disabled. Newsletter will run once, now.")
        send_newsletter()