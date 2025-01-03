from geopy.exc import GeocoderUnavailable
from geopy.geocoders import Nominatim


def get_addr(location: list) -> str:
    try:
        geo_loc = Nominatim(user_agent="GetLoc")
        loc_name = geo_loc.reverse(location)
        loc = reversed(loc_name.address.split(', ')[:3])
        rev_loc = ', '.join(loc)
        return rev_loc
    except GeocoderUnavailable:
        return 'Unknown'
