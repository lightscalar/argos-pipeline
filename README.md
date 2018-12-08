# ARGOS Pipeline

This document summarizes the current state of the Automated RecoGnition Of
Species (ARGOS) processing pipeline.


## File Structure

The ARGOS systems presumes that data is stored according to a very particular
file structure. The `config.py` file defines the `ARGOS_ROOT` variable, which
specifies the top of the ARGOS file system. This allows the system to easily
run on multiple systems. All data is then arranged according to the following
schema:

```unix
ARGOS_ROOT/year/month/day/site_name/obliques
ARGOS_ROOT/year/month/day/site_name/altitude/images/...
ARGOS_ROOT/year/month/day/site_name/altitude/maps/...
```

The obliques folder contains all oblique images and videos captured for a given
site. The `images/` directory contains all high resolution images captured at
the given site at the specified altitude. The `maps/` directory contains the
high-resolution georeferenced map file, `map.tif`, as well as a
lower-resolution map called `map_small.jpg`. As additional species maps are
generated for this flight, these will also be stored at this location.

As a concrete example, here is the location of the first image taken during the
St. John"s 66 ft flight on 03 August 2018:

```unix
ARGOS_ROOT/2018/08/03/st_johns_marsh/66/images/DJI_0001.JPG
```


## Annotation Targets

Annotation targets include plant species that the ARGOS system should learn to
classify, including plant targets such as *Frangula alnus*, but also other features
such as sand, water, rocks, and man-made features such as asphalt.

Viable Annotation Targets (ATs) are stored in the MongoDB database in the
`targets` collection. They are available via the `database.py` module by
calling `get_targets()`.  The AT objects contain six fields: `scientific_name`,
`codes`, `common_name`, `physiognomy`, `category`, and `color_code`.

As an example:

```json
{"scientific_name": "Achillea millifolium",
"codes": ["AM"], 
"common_name": "Yarrow",
"physiognomy": "Forb",  
"category": "Native",
"color_code": "#0cb577"
}
```



## API

The ARGOS API provides


