from source.configuration import conf, logging
import requests
import datetime as dt


def get_auth_header():
    if conf.server.type == "jellyfin":
        return {"Authorization": f'MediaBrowser Token="{conf.server.api_token}"'}
    else:  # emby
        return {"X-Emby-Token": conf.server.api_token}


def get_root_items():
    headers = get_auth_header()

    if conf.server.type == "jellyfin":
        url = f'{conf.server.url}/Items'
    else:  # emby
        url = f'{conf.server.url}/emby/Items'

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Error while getting the root items, status code: {response.status_code}.")
        raise Exception(
            f"Error while getting the root items, status code: {response.status_code}. Answer: {response.text}.")
    return response.json()["Items"]


def get_item_from_parent(parent_id, type, minimum_creation_date=None):
    if type not in ["movie", "tv"]:
        raise Exception(f"Error while retrieving a media from server. Type must be 'movie' or 'tv'. Got {type}")
    headers = get_auth_header()

    if conf.server.type == "jellyfin":
        url = f'{conf.server.url}/Items?ParentId={parent_id}&fields=DateCreated,ProviderIds&Recursive=true'
    else:  # emby
        url = f'{conf.server.url}/emby/Items?ParentId={parent_id}&fields=DateCreated,ProviderIds&Recursive=true'

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Error while getting the items from parent, status code: {response.status_code}.")
        raise Exception(
            f"Error while getting the items from parent, status code: {response.status_code}. Answer: {response.text}.")
    if not minimum_creation_date:
        return response.json()["Items"], response.json()["TotalRecordCount"]
    else:
        recent_items = []
        for item in response.json()["Items"]:
            if (item.get("Type") == "Episode" and item.get("LocationType") == "Virtual") or (
                    item.get("Type") == "Movie" and item.get("LocationType") == "Virtual"):
                logging.debug(f"Skipping item {item['Name']} because it is a virtual item. Item : {item}")
                continue
            creation_date = dt.datetime.strptime(item["DateCreated"].split("T")[0], "%Y-%m-%d")
            if creation_date > minimum_creation_date:
                logging.debug(
                    f"Item {item['Name']} is more recent than {minimum_creation_date} (added on {creation_date}). Adding it to the list.")
                logging.debug("Item details: " + str(item))
                recent_items.append(item)
        return recent_items, response.json()["TotalRecordCount"]


def get_item_from_parent_by_name(parent_id, name):
    headers = get_auth_header()

    if conf.server.type == "jellyfin":
        url = f'{conf.server.url}/Items?ParentId={parent_id}&fields=DateCreated,ProviderIds&Recursive=true'
    else:  # emby
        url = f'{conf.server.url}/emby/Items?ParentId={parent_id}&fields=DateCreated,ProviderIds&Recursive=true'

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Error while getting the items from parent, status code: {response.status_code}.")
        raise Exception(
            f"Error while getting the items from parent, status code: {response.status_code}. Answer: {response.text}.")
    for item in response.json()["Items"]:
        if "Name" in item.keys():
            if item["Name"] == name:
                return item