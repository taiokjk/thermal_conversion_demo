from os import mkdir, path, remove
import numpy as np
from thermal import Thermal
import matplotlib.pyplot as plt
from osgeo import gdal, ogr
import glob
import pathlib
import subprocess
import configparser

# Read config file
config = configparser.ConfigParser()
config.read('config.ini')

# General config
sdk_path = config['General']['dji_thermal_sdk_folder']
image_path = config['General']['image_path']
output_path = config['General']['output_path']

# Thermal config
distance = config['Thermal Metadata'].getfloat('distance')
humidity = config['Thermal Metadata'].getfloat('humidity')
emissivity = config['Thermal Metadata'].getfloat('emissivity')
reflection = config['Thermal Metadata'].getfloat('reflection')

#from https://github.com/SanNianYiSi/thermal_parser
thermal = Thermal(
    dirp_filename=f'plugins/{sdk_path}/windows/release_x64/libdirp.dll',
    dirp_sub_filename=f'plugins/{sdk_path}/windows/release_x64/libv_dirp.dll',
    iirp_filename=f'plugins/{sdk_path}/windows/release_x64/libv_iirp.dll',
    exif_filename=f'plugins/exiftool-12.35.exe',
    dtype=np.float32,
)

#get list of JPGs to convert
if not image_path:
    files = list(pathlib.Path('images').glob('*T.JPG'))
else:
    files = list(pathlib.Path(image_path).glob('*T.JPG'))

#iterate through JPGs, convert to temperature, and write out to TIFs
for i in files:    
    temperature = thermal.parse_dirp2(image_filename = i, 
                                        object_distance = distance,
                                        relative_humidity = humidity,
                                        emissivity = emissivity,
                                        reflected_apparent_temperature = reflection)
    filename = pathlib.Path(i).stem
    # create the output image
    driver = gdal.GetDriverByName('GTiff')
    outDs = driver.Create('images/' + filename + '.tif', temperature.shape[1], temperature.shape[0], 1, gdal.GDT_Float32)
    outband = outDs.GetRasterBand(1)
    #write temp to array
    outband.WriteArray(temperature)
    outDs = None

#use exiftool to append geodata from JPGs to TIFs
p = subprocess.Popen(['exiftool','-tagsfromfile','%d%f.JPG' , "'-gps*'", '-ext', 'tif', "images" ], stdout=None)
#kill subprocess 
p.wait()
p.kill()

#remove redundant files
for orig in glob.iglob(path.join('./images', '*.tif_original')):
    remove(orig)

print("Done processing")