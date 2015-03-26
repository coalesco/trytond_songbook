from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from nereid import (
    request, abort, render_template, login_required, url_for, flash, jsonify,
    current_app, route
)
from nereid.contrib.pagination import Pagination, BasePagination
from nereid.ctx import has_request_context

__all__ = ['Track']


class Track(ModelSQL, ModelView):
    "Track"
    __name__ = "songbook.track"

    album = fields.Many2One("songbook.album", 'Album', required=True)
    code = fields.Char('Code', 16, required=True, select=True)
    song = fields.Many2One("songbook.song", 'Song', required=True)

    @classmethod
    def __setup__(cls):
        super(Track, cls).__setup__()
        cls._sql_constraints = [
            ('album_code_uniq', 'UNIQUE(album, code)',
             'This track code already exists in the specified album.')
        ]
        cls._order.insert(0, ('code', 'ASC'))


