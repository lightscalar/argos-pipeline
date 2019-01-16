"""Loads big things into memory once, so playing around is faster."""
from vessel import Vessel


print("> Loading Phragmites positions.")
phrag = Vessel(
    "maps/2018-08-03-st_johns_marsh-66_phragmites_australis_subsp_australis.dat"
)
