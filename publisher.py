from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool

__all__ = ['Publisher']


class Publisher(ModelSQL, ModelView):
    "Publisher"
    __name__ = "songbook.publisher"

    code = fields.Char('Code', 4, required=True, select=True)
    name = fields.Char('Name', 64, required=True, select=True)
    description = fields.Text('Description')
    albums = fields.One2Many(
        "songbook.album",
        'publisher',
        'Albums from This Publisher'
    )

    @classmethod
    def __setup__(cls):
        super(Publisher, cls).__setup__()
        cls._sql_constraints = [
            ('code_uniq', 'UNIQUE(code)',
             'This publisher code already exists.')
        ]
        cls._order.insert(0, ('name', 'ASC'))

