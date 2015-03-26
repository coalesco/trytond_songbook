from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from nereid import (
    request, abort, render_template, login_required, url_for, flash, jsonify,
    current_app, route
)

__all__ = ['Album']


class Album(ModelSQL, ModelView):
    "Album"
    __name__ = "songbook.album"

    songbook = fields.Many2One("songbook.songbook", 'Songbook', required=True)
    code = fields.Char('Code', 16, required=True, select=True)
    name = fields.Char('Name', 64, required=True, select=True)
    publisher = fields.Many2One("songbook.publisher", 'Publisher', required=True)
    description = fields.Text('Description')
    tracks = fields.One2Many(
        "songbook.track",
        'album',
        'Tracks in This Album'
    )

    @classmethod
    def __setup__(cls):
        super(Album, cls).__setup__()
        cls._sql_constraints = [
            ('songbook_code_uniq', 'UNIQUE(songbook, code)',
             'This album code already exists in the specified songbook.')
        ]
        cls._order.insert(0, ('songbook', 'ASC'))
        cls._order.insert(1, ('code', 'ASC'))

    @classmethod
    @route('/songbook/albums/<code>.txt', methods=['GET'])
    def call_api_index(cls, code):
        """
        Delimited text file via website
        """
        album=cls.search([('code', '=', code)])[0]
        return render_template(
            'songbook_songlist-txt.jinja',
            tracks = album.tracks
        )

