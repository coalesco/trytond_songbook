from trytond.pool import Pool
from .songbook import *
from .publisher import *
from .album import *
from .artist import *
from .song import *
from .track import *

def register():
    Pool.register(
        Songbook,
        Publisher,
        Album,
        Artist,
        Song,
        Track,
        ExportTracksStart,
        ExportTracksResult,
        module='songbook', type_='model')
    Pool.register(
        ExportTracks,
        module='songbook', type_='wizard')
    Pool.register(
        SongbookByArtist,
        module='songbook', type_='report')

