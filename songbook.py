from trytond.model import ModelView, ModelSQL, fields
from trytond.report import Report
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.wizard import Wizard, StateView, Button, StateTransition
from sql import Table, As, Literal, Column, Desc, Asc, Expression, Flavor
from sql.conditionals import Coalesce
from sql.operators import Or, And, Concat, ILike, In, Operator
from nereid import (
    request, abort, render_template, login_required, url_for, flash, jsonify,
    current_app, route
)
from nereid.contrib.pagination import Pagination, BasePagination

__all__ = [
    'Songbook',
    'ExportTracks',
    'ExportTracksStart',
    'ExportTracksResult',
    'SongbookByArtist'
]


class Songbook(ModelSQL, ModelView):
    "Songbook"
    __name__ = "songbook.songbook"

    name = fields.Char('Name', 64, required=True, select=True)
    description = fields.Text('Description')
    albums = fields.One2Many(
        'songbook.album',
        'songbook',
        'Albums in This Songbook'
    )
    songs_title = fields.Function(
        fields.One2Many(
            'songbook.song',
            None,
            'Songs by Title in This Songbook'
        ), 'get_songs_title'
    )
    songs_artist = fields.Function(
        fields.One2Many(
            'songbook.song',
            None,
            'Songs by Artist in This Songbook'
        ), 'get_songs_artist'
    )

    @classmethod
    def __setup__(cls):
        super(Songbook, cls).__setup__()
        cls._sql_constraints = [
            ('name_uniq', 'UNIQUE(name)',
             'A songbook with that name already exists.')
        ]
        cls._order.insert(0, ('name', 'ASC'))

    def get_songs_title(self, name):
        songdict = {}
        songlist = []

        for album in self.albums:
            for track in album.tracks:
                if track.song.rec_name not in songdict:
                    songdict[track.song.rec_name] = track.song.id

        for song in sorted(songdict):
            songlist.append(songdict[song])

        return songlist

    def get_songs_artist(self, name):
        artdict = {}
        artlist = []

        for album in self.albums:
            for track in album.tracks:
                songkey = track.song.artist.rev_name + ' | ' + track.song.title
                if songkey not in artdict:
                    artdict[songkey] = track.song.id

        for artist in sorted(artdict):
            artlist.append(artdict[artist])

        return artlist

    @classmethod
    @route('/songbook/songbooks/<int:id>')
    def render_html(cls, id=1):
        """
        output songbook home page to client
        """
        songbook=cls.browse([id])[0]
        return render_template(
            'songbook_songbook-detail.jinja',
            songbook=songbook
        )

    @classmethod
    @route('/songbook/songbooks', methods=['GET', 'POST'])
    def render_html_index(cls):
        """
        output song list to web client
        """
        name_filter = '%' + request.args.get('namecontains', '') + '%'
        page = request.args.get('page', 1, int)
        domain = [
            ('name', 'ilike', name_filter)
        ]
        songbooks = Pagination(
            cls, domain, page, 25
        )

        return render_template(
            'songbook_songbook-list.jinja',
            songbooks=songbooks
        )

    @classmethod
    @route('/songbook')
    def render_html_home(cls):
        """
        output the home page of the songbook web app to client
        """

        return render_template('songbook_home.jinja')

class ExportTracks(Wizard):
    "Export Tracks in Songbook"
    __name__ = 'songbook.songbook.export_tracks'

    start = StateView(
        'songbook.songbook.export_tracks.start',
        'songbook.songbook_export_tracks_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Export', 'export', 'tryton-ok', default=True),
        ]
    )
    export = StateTransition()
    result = StateView(
        'songbook.songbook.export_tracks.result',
        'songbook.songbook_export_tracks_result_view_form', [
            Button('Close', 'end', 'tryton-cancel'),
        ]
    )

    def transition_export(self):
        """
        Delimited text file for import into CAVS or similar jukebox
        """
        pool = Pool()
        Song = pool.get('songbook.song')
        Artist = pool.get('songbook.artist')
        Publisher = pool.get('songbook.publisher')
        Album = pool.get('songbook.album')
        Track = pool.get('songbook.track')

        cursor = Transaction().cursor

        song = Song.__table__()
        artist = Artist.__table__()
        publisher = Publisher.__table__()
        album = Album.__table__()
        track = Track.__table__()

        songbook_ids = Transaction().context.get('active_ids')

        title_and_publisher = Concat(
            song.title, Concat(
                Literal(' .'), Concat(publisher.code, Literal('.'))
            )
        )

        artist_fullname = Concat(
            Coalesce(artist.first_name, Literal('')),
            Concat(
                Literal(' '),
                Coalesce(artist.last_name, Literal(''))
            )
        )

        export_select = track.join(
            album, condition=(album.id == track.album)
        ).join(
            publisher, condition=(publisher.id == album.publisher)
        ).join(
            song, condition=(song.id == track.song)
        ).join(
            artist, condition=(artist.id == song.artist)
        ).select(
            track.code, title_and_publisher, artist_fullname,
            where=In(album.songbook, songbook_ids)
        )
        export_select.order_by = Asc(track.code)

        cursor.execute(*export_select)

        rv_list = ['|'.join(x) for x in cursor.fetchall()]

        self.result.file = buffer(bytearray(u'\r\n'.join(rv_list), 'utf-8'))
        return 'result'

    def default_result(self, fields):
        file_ = self.result.file
        self.result.file = False  # No need to store it in session
        return {
            'file': file_,
        }

class ExportTracksStart(ModelView):
    "Export Tracks in Songbook"
    __name__ = 'songbook.songbook.export_tracks.start'

class ExportTracksResult(ModelView):
    "Export Tracks in Songbook"
    __name__ = 'songbook.songbook.export_tracks.result'

    file = fields.Binary('File', readonly=True)

class SongbookByArtist(Report):
    __name__ = 'songbook.songs_by_artist'

    @classmethod
    def parse(cls, report, objects, data, localcontext):
        artlist = dict((s.id, []) for s in objects)
        for songbook in objects:
            artdict = {}
            for album in songbook.albums:
                for track in album.tracks:
                    if track.song.artist.rev_name not in artdict:
                        artdict[track.song.artist.rev_name] = {}
                    if track.song.title not in artdict[
                        track.song.artist.rev_name
                    ]:
                        artdict[track.song.artist.rev_name][
                            track.song.title
                        ] = track.song.id

            for artkey in sorted(artdict):
                artlist[songbook.id].append({
                    'rev_name': artkey,
                    'songs': sorted(artdict[artkey]),
                })

        localcontext['artists'] = lambda songbook_id: artlist[songbook_id]
        res = super(SongbookByArtist, cls).parse(
            report, objects, data, localcontext
        )
        return res

