# -*- coding: utf-8 -*-
from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsFields, QgsVectorFileWriter
from PyQt4.QtCore import *

from osgeo import gdal
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
import pghstore
import tempfile
import os

class OsmParser(QObject):
    '''
    Parse an OSM file with OGR
    '''
    
    #Signal pourcentage
    signalPourcentage = pyqtSignal(int, name='emitPourcentage')
    
    #Signal text
    signalText = pyqtSignal(str, name='emitText')
    
    #Layers available in the OGR driver for OSM
    OSM_LAYERS = ['points','lines','multilinestrings','multipolygons','other_relations']
    
    #Dict to build the full ID of an object
    DIC_OSM_TYPE = {'node':'n', 'way':'w', 'relation':'r'}
    
    #Whitle list for the attribute table, if set to None all the keys will be keep
    WHITE_LIST = {'multilinestrings': None, 'points': None, 'lines': None, 'multipolygons': None}
    
    def __init__(self,osmFile, layers = OSM_LAYERS, whiteListColumn = WHITE_LIST, deleteEmptyLayers = False):
        self.__osmFile = osmFile
        self.__layers = layers
        self.__whiteListColumn = whiteListColumn
        self.__deleteEmptyLayers = deleteEmptyLayers
        QObject.__init__(self)
        
    def parse(self):
        '''
        Start parsing the osm file
        '''
        
        #Configuration for OGR
        current_dir = os.path.dirname(os.path.realpath(__file__))
        osmconf = current_dir + '/osmconf.ini'
        gdal.SetConfigOption('OSM_CONFIG_FILE', osmconf)
        gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', 'NO')
        
        if not os.path.isfile(self.__osmFile):
            raise GeoAlgorithmExecutionException, "File doesn't exist"
        
        uri = self.__osmFile + "|layername="
        layers = {}
        
        #Foreach layers
        for layer in self.__layers:
            self.signalText.emit("Parsing layer : " + layer)
            layers[layer] = {}
            
            #Reading it with a QgsVectorLayer
            layers[layer]['vectorLayer'] = QgsVectorLayer(uri + layer, "test_" + layer,"ogr")
            
            if layers[layer]['vectorLayer'].isValid() == False:
                raise GeoAlgorithmExecutionException, "Error on the layer", layers[layer]['vectorLayer'].lastError()
            
            #Set some default tags
            layers[layer]['tags'] = ['id_full','osm_id','osm_type']
            
            #Save the geometry type of the layer
            layers[layer]['geomType'] = layers[layer]['vectorLayer'].wkbType()
            
            #Set a featureCount
            layers[layer]['featureCount'] = 0
            
            for feature in layers[layer]['vectorLayer'].getFeatures():
                layers[layer]['featureCount'] += 1
                
                #Get the "others_tags" field
                attrs = None
                if layer in ['points','lines','multilinestrings','other_relations']:
                    attrs = feature.attributes()[1:]
                else:
                    #In the multipolygons layer, there is one more column before "other_tags"
                    attrs = feature.attributes()[2:]
                
                if attrs[0]:
                    hstore = pghstore.loads(attrs[0])
                    for key in hstore:
                        if key not in layers[layer]['tags']: #If the key in OSM is not already in the table
                            if self.__whiteListColumn[layer]:
                                if key in self.__whiteListColumn[layer]:
                                    layers[layer]['tags'].append(key)
                            else:
                                layers[layer]['tags'].append(key)
        
        #Delete empty layers if this option is set to True
        if self.__deleteEmptyLayers:
            deleteLayers = []
            for keys,values in layers.iteritems() :
                if values['featureCount'] < 1:
                    deleteLayers.append(keys)
            for layer in deleteLayers:
                del layers[layer]

        #Creating GeoJSON files for each layers
        for layer in self.__layers:
            self.signalText.emit("Creating GeoJSON file : " + layer)
            tf = tempfile.NamedTemporaryFile(delete=False,suffix="_"+layer+".geojson")
            layers[layer]['geojsonFile'] = tf.name
            tf.flush()
            tf.close()
            
            #Adding the attribute table
            fields = QgsFields()
            for key in layers[layer]['tags']:
                fields.append(QgsField(key, QVariant.String))
            fileWriter = QgsVectorFileWriter(layers[layer]['geojsonFile'],'UTF-8',fields,layers[layer]['geomType'],layers[layer]['vectorLayer'].crs(),'GeoJSON')
            
            #Foreach feature in the layer
            for feature in layers[layer]['vectorLayer'].getFeatures():
                fet = QgsFeature()
                fet.setGeometry(feature.geometry())
                
                newAttrs= []
                attrs = feature.attributes()
                
                if layer in ['points','lines','multilinestrings']:
                    if layer == 'points':
                        osmType = "node"
                    elif layer == 'lines':
                        osmType = "way"
                    elif layer == 'multilinestrings':
                        osmType = 'relation'
                    
                    newAttrs.append(self.DIC_OSM_TYPE[osmType]+str(attrs[0]))
                    newAttrs.append(attrs[0])
                    newAttrs.append(osmType)
                    
                    if attrs[1]:
                        hstore = pghstore.loads(attrs[1])
                        for tag in layers[layer]['tags'][3:]:
                            if unicode(tag) in hstore:
                                newAttrs.append(hstore[tag])
                            else:
                                newAttrs.append("")
                        fet.setAttributes(newAttrs)
                        fileWriter.addFeature(fet)
                    
                elif layer == 'multipolygons':
                    if attrs[0]:
                        osmType = "relation"
                        newAttrs.append(self.DIC_OSM_TYPE[osmType]+str(attrs[0]))
                        newAttrs.append(self.DIC_OSM_TYPE[osmType]+str(attrs[0]))
                    else:
                        osmType = "way"
                        newAttrs.append(self.DIC_OSM_TYPE[osmType]+str(attrs[1]))
                        newAttrs.append(attrs[1])
                    newAttrs.append(osmType)
                    
                    hstore = pghstore.loads(attrs[2])
                    for tag in layers[layer]['tags'][3:]:
                        if unicode(tag) in hstore:
                            newAttrs.append(hstore[tag])
                        else:
                            newAttrs.append("")
                    fet.setAttributes(newAttrs)
                    fileWriter.addFeature(fet)
                    
            del fileWriter      
        return layers