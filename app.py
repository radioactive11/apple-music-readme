from base64 import b64encode
from dotenv import load_dotenv
from flask import Flask, Response, render_template
import os
from pprint import pprint
import random
import requests


class RenderCard:
    def __init__(self) -> None:
        load_dotenv()
        self.__token = os.getenv("AUTH_TOKEN")
        self.__cookie = os.getenv("COOKIE")
        self.__media_user_token = os.getenv("MEDIA_USER_TOKEN")

    def __apple_music_icon_b64(self):
        """
        Returns Base64 encoded Apple Music icon.
        """
        print(os.getcwd())
        with open("static/icon.png", "rb") as f:
            return b64encode(f.read()).decode("ascii")

    def __album_art_b64(self, img_url: str):
        """Converts album art to base64

        Args:
            img_url (str): CDN URL of the album_art
        """
        res = requests.get(img_url, headers={}, cookies={})
        return b64encode(res.content).decode("ascii")

    def __fetch_recent_albums(self):
        """
        Fetches recently played albums from Apple Music.
        """
        url = "https://amp-api.music.apple.com/v1/me/library/recently-added?art%5Burl%5D=f&fields%5Balbums%5D=artistName%2CartistUrl%2Cartwork%2CcontentRating%2CeditorialArtwork%2Cname%2CplayParams%2CreleaseDate%2Curl&fields%5Bartists%5D=name%2Curl&format%5Bresources%5D=map&includeOnly=catalog%2Cartists&include%5Blibrary-albums%5D=artists&include%5Blibrary-artists%5D=catalog&l=en-GB&limit=25&omit%5Bresource%5D=autos"
        headers = {
            "Authorization": f"Bearer {self.__token}",
            "Cookie": self.__cookie,
            "media-user-token": self.__media_user_token,
            "origin": "https://music.apple.com",
            "referer": "https://music.apple.com/",
        }

        response = requests.get(url, headers=headers)

        pprint(
            f"Response: {response.json()} | self.__token: {self.__token} | self.__cookie: {self.__cookie} | self.__media_user_token: {self.__media_user_token}"
        )

        response = response.json()

        resources = response["resources"]
        albums = list(resources["albums"].values())

        album_data = []

        for album in albums:
            album = album["attributes"]
            image_url = album["artwork"]["url"]
            image_url = album.get("artwork", {}).get("url", "")
            image_url = image_url.replace("{w}", "632")
            image_url = image_url.replace("{h}", "632")
            image_url = image_url.replace("{f}", "jpg")
            name = album.get("name", "Unknown")
            artist_name = album.get("artistName", "Unknown")

            album_dict = {
                "name": name,
                "artist_name": artist_name,
                "image_url": image_url,
            }

            album_data.append(album_dict)

        self.__data = random.choice(album_data)

    def generate_card(self):
        """Generates the SVG card

        Returns:
            str: SVG card
        """
        self.__fetch_recent_albums()
        image = self.__album_art_b64(self.__data["image_url"])
        album_name = self.__data["name"]
        artist_name = self.__data["artist_name"]

        album_name = (album_name[:20] + "...") if len(album_name) > 22 else album_name
        icon = self.__apple_music_icon_b64()

        svg = render_template(
            "card.html.j2",
            album_art=image,
            album_name=album_name,
            artist_name=artist_name,
            apple_icon=icon,
        )

        return svg


app = Flask(__name__, template_folder="templates")
rc = RenderCard()


@app.route("/", defaults={"path": ""}, methods=["GET"])
@app.route("/<path:path>")
def handle_all(path):
    svg = rc.generate_card()

    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "s-maxage=1"

    return resp


if __name__ == "__main__":
    app.run(debug=True, port=5050)
