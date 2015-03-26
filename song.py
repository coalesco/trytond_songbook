from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from nereid import (
    request, abort, render_template, login_required, url_for, flash, jsonify,
    current_app, route
)
from nereid.contrib.pagination import Pagination, BasePagination
from nereid.ctx import has_request_context

__all__ = ['Song']


class Song(ModelSQL, ModelView):
    "Song"
    __name__ = "songbook.song"

    title = fields.Char('Title', 64, required=True, select=True)
    artist = fields.Many2One("songbook.artist", 'Artist', required=True)
    tracks = fields.One2Many(
        "songbook.track",
        'song',
        'Tracks of This Song'
    )

    def get_rec_name(self, name):
        return " | ".join(
            x for x in [self.title, self.artist.full_name] if x
        )

    def serialize(self):
        """
        Serialize the song object and return a dictionary.
        """
        object_json = {
            "url": url_for(
                'songbook.song.render_html',
                id=self.id,
            ),
            "objectType": self.__name__,
            "id": self.id,
            "title": self.title,
            "artist": self.artist.full_name,
        }
        return object_json

    @classmethod
    def __setup__(cls):
        super(Song, cls).__setup__()
        cls._sql_constraints = [
            ('name_artist_uniq', 'UNIQUE(title, artist)',
             'This song by this artist already exists in the system.')
        ]
        cls._order.insert(0, ('title', 'ASC'))

    @classmethod
    @route('/songbook/api/songs', methods=['GET', 'POST'])
    def call_api_index(cls):
        """
        JSON-formatted REST API to support 3rd party integration, apps
        and web page javascript such as search-as-you-type.
        """
        artist_filter = '%' + request.args.get('artistcontains', '') + '%'
        title_filter = request.args.get('titlestartswith', '') \
            + '%' + request.args.get('titlecontains', '') + '%'
        domain = [
            ('title', 'ilike', title_filter),
            ('artist.full_name', 'ilike', artist_filter)
        ]
        songs = cls.search(domain, limit=int(request.args.get('limit', '5')))
        return jsonify(
            songs=[s.serialize() for s in songs]
        )

    @classmethod
    @route('/songbook/songs/<int:id>', methods=['GET'])
    def render_html(cls, id=0):
        """
        output details of a selected song to web client
        """
        song=cls.browse([id])[0]
        return render_template(
            'songbook_song-detail.jinja',
            song=song
        )

    @classmethod
    @route('/songbook/songs', methods=['GET', 'POST'])
    def render_html_index(cls):
        """
        output song list to web client
        """
        artist_filter = '%' + request.args.get('artistcontains', '') + '%'
        title_filter = request.args.get('titlestartswith', '') \
            + '%' + request.args.get('titlecontains', '') + '%'
        page = request.args.get('page', 1, int)
        domain = [
            ('title', 'ilike', title_filter),
            ('artist.full_name', 'ilike', artist_filter)
        ]
        songs = Pagination(
            cls, domain, page, 25
        )

        return render_template(
            'songbook_song-list.jinja',
            songs=songs
        )

