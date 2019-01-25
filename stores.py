"""Loads big things into memory once, so playing around is faster."""
from vessel import Vessel


print("> Loading map positions.")
# phrag = Vessel(
#     "maps/2018-08-03-st_johns_marsh-66_phragmites_australis_subsp_australis.dat"
# )
frangula_07 = Vessel("maps/2018-07-06-st_johns_marsh-66_frangula_alnus.dat")
frangula_08 = Vessel("maps/2018-08-03-st_johns_marsh-66_frangula_alnus.dat")
elberta_centaurea_06 = Vessel("maps/2018-06-27-elberta_site_1-66_centaurea_stoebe.dat")
