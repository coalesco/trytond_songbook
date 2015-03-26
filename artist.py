from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool

from sql import Table, Column, Literal, Desc, Asc, Expression, Flavor
from sql.functions import Now, Extract
from sql.operators import Or, And, Concat, ILike, Operator
from sql.conditionals import Coalesce
from sql.aggregate import Count, Max

from nereid import (
    request, abort, render_template, login_required, url_for, flash, jsonify,
    current_app, route
)
from nereid.contrib.pagination import Pagination, BasePagination
from nereid.ctx import has_request_context

__all__ = ['Artist']


class Artist(ModelSQL, ModelView):
    "Artist"
    __name__ = "songbook.artist"
    _rec_name = 'full_name'

    last_name = fields.Char('Last Name', required=True, select=True)
    first_name = fields.Char('First Name', select=True)
    full_name = fields.Function(
        fields.Char('Full Name'), 'get_full_name',
        searcher='search_full_name'
    )
    rev_name = fields.Function(
        fields.Char('Reversed Name'), 'get_rev_name'
    )
    songs = fields.One2Many(
        "songbook.song",
        'artist',
        'Songs by This Artist'
    )

    def serialize(self):
        """
        Serialize the artist object and return a dictionary.
        """
        object_json = {
            "url": url_for(
                'songbook.artist.render_html',
                id=self.id,
            ),
            "objectType": self.__name__,
            "id": self.id,
            "lastName": self.last_name,
            "firstName": self.first_name,
            "fullName": self.full_name,
        }
        return object_json

    @classmethod
    def __setup__(cls):
        super(Artist, cls).__setup__()
        cls._sql_constraints = [
            ('name_uniq', 'UNIQUE(last_name, first_name)',
             'An artist with that name already exists.')
        ]
        cls._order.insert(0, ('last_name', 'ASC'))
        cls._order.insert(1, ('first_name', 'ASC'))

    @classmethod
    def search_full_name(cls, name, clause):
        "Search Full Name"
        _, operator, value = clause
        Operator = fields.SQL_OPERATORS[operator]
        table = cls.__table__()
        fullname = Concat(
            Coalesce(table.first_name, Literal('')),
            Concat(
                Literal(' '),
                Coalesce(table.last_name, Literal(''))
            )
        )

        query = table.select(table.id, where=Operator(fullname, value))
        return [('id', 'in', query)] 

    def get_full_name(self, name):
        if self.first_name is None:
            fullname = self.last_name
        else:
            fullname = "%s %s" % (self.first_name, self.last_name) 
        return fullname.strip(" ")

    def get_rev_name(self, name):
        if self.first_name is None:
            revname = self.last_name
        else:
            revname = "%s, %s" % (self.last_name, self.first_name) 
        return revname.strip(", ")

    @classmethod
    @route('/songbook/api/artists', methods=['GET', 'POST'])
    def call_api_index(cls):
        """
        JSON-formatted REST API to support 3rd party integration, apps
        and web page javascript such as search-as-you-type.
        """
        name_filter = '%' + request.args.get('namecontains', '') + '%'
        domain = [
            ('full_name', 'ilike', name_filter)
        ]
        artists = cls.search(domain, limit=int(request.args.get('limit', '5')))
        return jsonify(
            artists=[a.serialize() for a in artists]
        )

    @classmethod
    @route('/songbook/artists/<int:id>', methods=['GET'])
    def render_html(cls, id=0):
        """
        output details of a selected artist to web client
        """
        artist=cls.browse([id])[0]
        return render_template(
            'songbook_artist-detail.jinja',
            artist=artist
        )

    @classmethod
    @route('/songbook/artists', methods=['GET', 'POST'])
    def render_html_index(cls):
        """
        output artist list to web client
        """
        name_filter = '%' + request.args.get('namecontains', '') + '%'
        page = request.args.get('page', 1, int)
        domain = [
            ('full_name', 'ilike', name_filter)
        ]
        artists = Pagination(
            cls, domain, page, 25
        )

        return render_template(
            'songbook_artist-list.jinja',
            artists=artists
        )

