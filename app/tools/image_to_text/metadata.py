from PIL import Image, ExifTags
from pillow_heif import register_heif_opener
from datetime import datetime
import json
from typing import Any, Dict, Optional




def dms_to_decimal(dms, ref) -> float:
    try:
        deg, minute, sec = dms
        
        val = deg + minute / 60 + sec / 3600
        if ref in ["S", "W"]:
            val = -val
        return round(float(val), 7)
    except Exception:
        return None


def normalize_exif(exif: Dict[int, Any]) -> Dict[str, Any]:
    if not exif:
        return {}
    
    device_data = 34665 in exif
    geo_data = 34853 in exif
    
    if device_data:
        exif_offset_named = gps_named = {ExifTags.TAGS.get(k, k): v for k, v in exif[34665].items()}
    if geo_data:
        gps_named = {ExifTags.GPSTAGS.get(k, k): v for k, v in exif[34853].items()}

    if geo_data:
        gps = {}
        lat = gps_named.get("GPSLatitude")
        lat_ref = gps_named.get("GPSLatitudeRef")
        lon = gps_named.get("GPSLongitude")
        lon_ref = gps_named.get("GPSLongitudeRef")

        if lat and lat_ref:
            gps["latitude"] = dms_to_decimal(lat, lat_ref)

        if lon and lon_ref:
            gps["longitude"] = dms_to_decimal(lon, lon_ref)

        if "GPSAltitude" in gps_named:
            gps["altitude_m"] = float(gps_named["GPSAltitude"])

        if "GPSSpeed" in gps_named:
            gps["speed"] = float(gps_named["GPSSpeed"])

        if "GPSTrack" in gps_named:
            gps["track_deg"] = gps_named["GPSTrack"]

        if "GPSDateStamp" in gps_named:
            gps["date"] = gps_named["GPSDateStamp"]
    else:
        gps = {} #macaroni code =)

    if device_data:
        device = {
            "device": {
            "manufacturer": exif_offset_named.get("Make"),
            "model": exif_offset_named.get("Model"),
            "software": exif_offset_named.get("Software"),
            "lens": exif_offset_named.get("LensModel"),
            },
            "capture": {
                "datetime_original":
                    exif_offset_named.get("DateTimeOriginal") if exif_offset_named.get("DateTimeOriginal") else None,
                "datetime_digitized": exif_offset_named.get("DateTimeDigitized") if exif_offset_named.get("DateTimeDigitized") else None,
            },
            "camera": {
                "f_number": str(exif_offset_named.get("FNumber")),
                "exposure_time_s": str(exif_offset_named.get("ExposureTime")),
                "iso": str(exif_offset_named.get("ISOSpeedRatings")),
                "focal_length_mm": str(exif_offset_named.get("FocalLength")),
                "exposure_bias": str(exif_offset_named.get("ExposureBiasValue")),
            },
            "image": {
                "width": exif_offset_named.get("ExifImageWidth"),
                "height": exif_offset_named.get("ExifImageHeight"),
                "orientation": exif_offset_named.get("Orientation"),
                "x_resolution": str(exif_offset_named.get("XResolution")),
                "y_resolution": str(exif_offset_named.get("YResolution")),
            }
        }
    else:
        device_data = {}
    
    result = device | gps


    def clean(d):
        if isinstance(d, dict):
            return {k: clean(v) for k, v in d.items() if v not in [None, {}, []]}
        return d

    return clean(result)


def extract_image_metadata_for_agent(image_path: str) -> Dict[str, Any]:
    is_heif = image_path[-4:] == "HEIC" 
    exif_keys = [34853, 34665]
    
    if is_heif:
        register_heif_opener()
    img = Image.open(image_path)


    raw = {}
    img_exif = img.getexif()
    for key in exif_keys:
        exifcode = img_exif.get_ifd(key)
        if exifcode:
            raw[key] = exifcode
    
    normalized = normalize_exif(raw)

    if normalized:
        return {
            "image_metadata": normalized,
            "agent_notes": {
                "treat_metadata_as_probabilistic": True,
                "gps_can_be_spoofed": True,
                "timestamps_can_be_modified": True
            }
        }
    
    return {}

#testing
if __name__ == "__main__":

    path = "./app/tools/image_to_text/norway2.HEIC"
    data = extract_image_metadata_for_agent(path)

    print(json.dumps(data, indent=2))
