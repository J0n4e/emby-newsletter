from source import configuration, context, utils
import re

translation = {
    "en": {
        "discover_now": "Discover now",
        "new_film": "New movies:",
        "new_tvs": "New shows:",
        "currently_available": "Currently available in your server:",
        "movies_label": "Movies",
        "episodes_label": "Episodes",
        "footer_label": "You are recieving this email because you are using ${server_owner_name}'s media server. If you want to stop receiving these emails, you can unsubscribe by notifying ${unsubscribe_email}.",
        "added_on": "Added on",
        "episodes": "Episodes",
        "episode": "Episode",
    }
}


def populate_email_template(movies, series, total_tv, total_movie, total_movies_on_server, total_tv_on_server) -> str:
    include_overview = True
    if len(movies) + len(series) > 10:
        include_overview = False
        configuration.logging.info(
            "There are more than 10 new items, overview will not be included in the email template to avoid too much content.")

    with open("./template/new_media_notification.html", encoding='utf-8') as template_file:
        template = template_file.read()

        if configuration.conf.email_template.language in ["en"]:
            for key in translation[configuration.conf.email_template.language]:
                template = re.sub(
                    r"\${" + key + "}",
                    translation[configuration.conf.email_template.language][key],
                    template
                )
        else:
            raise Exception(
                f"[FATAL] Language {configuration.conf.email_template.language} not supported. Supported languages are en")

        custom_keys = [
            {"key": "title", "value": configuration.conf.email_template.title.format_map(context.placeholders)},
            {"key": "subtitle", "value": configuration.conf.email_template.subtitle.format_map(context.placeholders)},
            {"key": "server_url", "value": configuration.conf.email_template.server_url},
            {"key": "server_owner_name",
             "value": configuration.conf.email_template.server_owner_name.format_map(context.placeholders)},
            {"key": "unsubscribe_email",
             "value": configuration.conf.email_template.unsubscribe_email.format_map(context.placeholders)}
        ]

        # Also support old variable names for backward compatibility
        template = re.sub(r"\${jellyfin_url}", configuration.conf.email_template.server_url, template)
        template = re.sub(r"\${jellyfin_owner_name}", configuration.conf.email_template.server_owner_name, template)

        for key in custom_keys:
            template = re.sub(r"\${" + key["key"] + "}", key["value"], template)

        # Movies section
        if movies:
            template = re.sub(r"\${display_movies}", "", template)
            movies_html = ""

            for movie_title, movie_data in movies.items():
                added_date = movie_data["created_on"].split("T")[0] if movie_data["created_on"] else "Unknown"

                movies_html += f"""
                <div class="media-item">
                    <!--[if mso]><table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%"><tr><td width="25%" valign="top"><![endif]-->
                    <div class="column">
                        <img src="{movie_data['poster']}" alt="{movie_title}" style="width: 100%; height: auto; display: block; margin: 0 auto;" />
                    </div>
                    <!--[if mso]></td><td width="70%" valign="top"><![endif]-->
                    <div class="column content">
                        <div class="media-content">
                            <h3 class="media-title">{movie_title} ({movie_data['year']})</h3>
                            <div class="media-meta">{translation[configuration.conf.email_template.language]['added_on']} {added_date}</div>
                            <p class="media-description">{movie_data['description']}</p>
                            <p class="media-rating">Rating: {movie_data['rating'] if movie_data['rating'] != '0.0/10' else 'N/A'}</p>
                        </div>
                    </div>
                    <!--[if mso]></td></tr></table><![endif]-->
                </div>
                """

            template = re.sub(r"\${films}", movies_html, template)
        else:
            template = re.sub(r"\${display_movies}", "display:none", template)

        # TV Shows section
        if series:
            template = re.sub(r"\${display_tv}", "", template)
            series_html = ""

            for serie_title, serie_data in series.items():
                added_date = serie_data["created_on"].split("T")[0] if serie_data[
                                                                           "created_on"] != "undefined" else "Unknown"

                # Format episode/season information
                if len(serie_data["seasons"]) == 1:
                    if len(serie_data["episodes"]) == 1:
                        added_items_str = f"{serie_data['seasons'][0]}, {translation[configuration.conf.email_template.language]['episode']} {serie_data['episodes'][0]}"
                    else:
                        episodes_ranges = utils.summarize_ranges(serie_data["episodes"])
                        if len(episodes_ranges) == 1:
                            added_items_str = f"{serie_data['seasons'][0]}, {translation[configuration.conf.email_template.language]['episodes']} {episodes_ranges[0]}"
                        else:
                            added_items_str = f"{serie_data['seasons'][0]}, {translation[configuration.conf.email_template.language]['episodes']} {', '.join(episodes_ranges[:-1])} & {episodes_ranges[-1]}"
                else:
                    serie_data["seasons"].sort()
                    added_items_str = ", ".join(serie_data["seasons"])

                series_html += f"""
                <div class="media-item">
                    <!--[if mso]><table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%"><tr><td width="25%" valign="top"><![endif]-->
                    <div class="column">
                        <img src="{serie_data['poster']}" alt="{serie_title}" style="width: 100%; height: auto; display: block; margin: 0 auto;" />
                    </div>
                    <!--[if mso]></td><td width="70%" valign="top"><![endif]-->
                    <div class="column content">
                        <div class="media-content">
                            <h3 class="media-title">{serie_title}</h3>
                            <div class="media-meta">{translation[configuration.conf.email_template.language]['added_on']} {added_date}</div>
                            <p class="media-description">{serie_data['description']}</p>
                            <div class="media-meta">{added_items_str}</div>
                            <br>
                            <p class="media-rating">Rating: {serie_data['rating'] if serie_data['rating'] != '0.0/10' else 'N/A'}</p>
                        </div>
                    </div>
                    <!--[if mso]></td></tr></table><![endif]-->
                </div>
                """

            template = re.sub(r"\${tvs}", series_html, template)
        else:
            template = re.sub(r"\${display_tv}", "display:none", template)

        # Statistics section
        template = re.sub(r'\${series_count}', str(total_tv), template)
        template = re.sub(r'\${movies_count}', str(total_movie), template)
        template = re.sub(r'\${total_movies_on_server}', str(total_movies_on_server), template)
        template = re.sub(r'\${total_tv_on_server}', str(total_tv_on_server), template)

        return template