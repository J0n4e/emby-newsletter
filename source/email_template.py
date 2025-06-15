from source import configuration
import re

translation = {
    "en":{
        "discover_now": "Discover now",
        "new_film": "New movies:",
        "new_tvs": "New shows:",
        "currently_available": "Currently available in Jellyfin:",
        "movies_label": "Movies",
        "episodes_label": "Episodes",
        "footer_label":"You are recieving this email because you are using ${jellyfin_owner_name}'s Jellyfin server. If you want to stop receiving these emails, you can unsubscribe by notifying ${unsubscribe_email}.",
        "added_on": "Added on"
    },
    "fr":{
        "discover_now": "Découvrir maintenant",
        "new_film": "Nouveaux films :",
        "new_tvs": "Nouvelles séries :",
        "currently_available": "Actuellement disponible sur Jellyfin :",
        "movies_label": "Films",
        "episodes_label": "Épisodes",
        "footer_label":"Vous recevez cet email car vous utilisez le serveur Jellyfin de ${jellyfin_owner_name}. Si vous ne souhaitez plus recevoir ces emails, vous pouvez vous désinscrire en notifiant ${unsubscribe_email}.",
        "added_on": "Ajouté le"
    }
}

def populate_email_template(movies, series, total_tv, total_movie) -> str:
    with open("./template/new_media_notification.html") as template_file:
        template = template_file.read()
        
        if configuration.conf.email_template.language in ["fr", "en"]:
            for key in translation[configuration.conf.email_template.language]:
                template = re.sub(
                    r"\${" + key + "}", 
                    translation[configuration.conf.email_template.language][key], 
                    template
                )
        else:
            raise Exception(f"[FATAL] Language {configuration.conf.email_template.language} not supported. Supported languages are fr and en")

        custom_keys = [
            {"key": "title", "value": configuration.conf.email_template.title}, 
            {"key": "subtitle", "value": configuration.conf.email_template.subtitle},
            {"key": "jellyfin_url", "value": configuration.conf.email_template.jellyfin_url},
            {"key": "jellyfin_owner_name", "value": configuration.conf.email_template.jellyfin_owner_name},
            {"key": "unsubscribe_email", "value": configuration.conf.email_template.unsubscribe_email}
        ]
        
        for key in custom_keys:
            template = re.sub(r"\${" + key["key"] + "}", key["value"], template)

        # Movies section
        if movies:
            template = re.sub(r"\${display_movies}", "", template)
            movies_html = ""
            
            for movie_title, movie_data in movies.items():
                added_date = movie_data["created_on"].split("T")[0]
                movies_html += f"""
                <div class="movie-card">
                    <table class="movie-card-table" width="100%" role="presentation" cellpadding="0" cellspacing="0">
                        <tr>
                            <td class="movie-image" valign="top">
                                <img src="{movie_data['poster']}" alt="{movie_title}" style="max-width: 100px; height: auto;">
                            </td>
                            <td class="movie-content-cell" valign="top" style="padding: 15px;">
                                <h3 class="movie-title" style="color: #ffffff !important; margin: 0 0 5px !important; font-size: 18px !important;">{movie_title}</h3>
                                <div class="movie-date" style="color: #dddddd !important; font-size: 14px !important; margin: 0 0 10px !important;">
                                    {translation[configuration.conf.email_template.language]['added_on']} {added_date}
                                </div>
                                <div class="movie-description" style="color: #dddddd !important; font-size: 14px !important; line-height: 1.4 !important;">
                                    {movie_data['description']}
                                </div>
                            </td>
                        </tr>
                    </table>
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
                added_date = serie_data["created_on"].split("T")[0]
                seasons_str = ", ".join(serie_data["seasons"])
                series_html += f"""
                <div class="movie-card">
                    <table class="movie-card-table" width="100%" role="presentation" cellpadding="0" cellspacing="0">
                        <tr>
                            <td class="movie-image" valign="top">
                                <img src="{serie_data['poster']}" alt="{serie_title}" style="max-width: 100px; height: auto;">
                            </td>
                            <td class="movie-content-cell" valign="top" style="padding: 15px;">
                                <h3 class="movie-title" style="color: #ffffff !important; margin: 0 0 5px !important; font-size: 18px !important;">{serie_title} {seasons_str}</h3>
                                <div class="movie-date" style="color: #dddddd !important; font-size: 14px !important; margin: 0 0 10px !important;">
                                    {translation[configuration.conf.email_template.language]['added_on']} {added_date}
                                </div>
                                <div class="movie-description" style="color: #dddddd !important; font-size: 14px !important; line-height: 1.4 !important;">
                                    {serie_data['description']}
                                </div>
                            </td>
                        </tr>
                    </table>
                </div>
                """
                
            template = re.sub(r"\${tvs}", series_html, template)
        else:
            template = re.sub(r"\${display_tv}", "display:none", template)

        # Statistics section
        template = re.sub(r"\${series_count}", str(total_tv), template)
        template = re.sub(r"\${movies_count}", str(total_movie), template)
        
        return template