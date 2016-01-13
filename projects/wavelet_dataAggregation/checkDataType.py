# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

from os import listdir
from os.path import isfile, join, exists
import csv
import numpy as np
from datetime import datetime
from runDataAggregationExperiment import readCSVfiles

import urllib2

def downloadExampleData():
  """
  Download A few example data files from river-view
  :return: lists of filename, filepath and datatype
  """
  exampleDataURL = [
    'http://data.numenta.org/nypd-motor-vehicle-collisions/nypd-motor-vehicle-collisions/data.csv',
    'http://data.numenta.org/sfpd-incidents/sfpd-incidents/data.csv',
    'http://data.numenta.org/usgs-earthquakes/usgs-earthquakes/data.csv',
    'http://data.numenta.org/portland-911/portland-911/data.csv',
    'http://data.numenta.org/planetlabs-ephemerides/DOVE%203/data.csv?limit=500',
    'http://data.numenta.org/nyc-traffic/1/data.csv?limit=500',
    'http://data.numenta.org/mn-traffic-sensors/10/data.csv?limit=500',
    'http://data.numenta.org/chicago-beach-water-quality/63rd%20Street%20Beach/data.csv?limit=500'
  ]
  dataTypeList = [
    'transactional',
    'transactional',
    'transactional',
    'transactional',
    'non-transactional',
    'non-transactional',
    'non-transactional',
    'non-transactional',
  ]
  fileNameList = []
  filePathList = []
  for url in exampleDataURL:
    fileName = url.split('/')[3]
    filePath = 'example_data/' + fileName + '.csv'

    fileNameList.append(fileName)
    filePathList.append(filePath)

    print "Downloading file " + str(fileName) + " from " + url
    response = urllib2.urlopen(url)

    data = response.read()
    rows = data.split('\n')
    # with open(filePath, 'wb') as f:
    #     f.write(data)
    #
    # fileReader = csv.reader(open(filePath, 'r'))
    # rows = []
    # headerRow = fileReader.next() # skip header line
    # rows.append(headerRow)
    newRows = []
    newRows.append(rows[0])
    for i in range(1, len(rows)-1):
      row = rows[i].split(',')
      row[0] = str(datetime.strptime(row[0], '%Y/%m/%d %H:%M:%S'))
      newRows.append(row)

    fileWriter = csv.writer(open(filePath, 'wb'))
    fileWriter.writerows(newRows)

  return fileNameList, filePathList, dataTypeList


def estimateMedianAbsoluteDeviation(timestamp):
  """
  Estimate median sampling interval and the median absolute deviation (MAD)
  of sampling interval
  @param timestamp: numpy array of datetime that stores timestamp
  @return medianSamplingInterval: median sampling interval
          medianAbsoluteDev: median absolute deviation of sampling interval
  """
  samplingIntervals = np.diff(timestamp)
  samplingIntervals = samplingIntervals.astype('float32')
  samplingIntervals = samplingIntervals[samplingIntervals > 0]
  medianSamplingInterval = np.median(samplingIntervals)
  medianAbsoluteDev = np.median(np.abs(samplingIntervals - medianSamplingInterval))
  return medianSamplingInterval, medianAbsoluteDev
  # meanSamplingInterval = np.mean(samplingIntervals)
  # samplingIntervalsStd = np.std(samplingIntervals)
  # return meanSamplingInterval, samplingIntervalsStd


def checkDataType(dataFilePath):
  """
  Return the data type (transactional or non-transactional)
  The data type is determined via an data type indicator, defined as the
  ratio between median absolute deviation and median of the sampling interval.

  @param dataFilePath: Name of a csv file, the file must have two columns
  with header "timestamp", and "value"
  @return dataType: a string with value "transactional" or "non-transactional"
  """
  (timestamp, sig) = readCSVfiles(dataFilePath)
  medianSamplingInterval, medianAbsoluteDev = estimateMedianAbsoluteDeviation(timestamp)

  dataTypeIndicator = medianAbsoluteDev/medianSamplingInterval
  if dataTypeIndicator > 0.2:
    dataType = "transactional"
  else:
    dataType = "non-transactional"

  return dataType, dataTypeIndicator


def checkAlgorithmPerformance(dataTypeList, predictedDataTypeList, dataTypeIndicatorList):
  """
  Check the performance of the data type detection algorithm
  :param dataTypeList: List of data type
  :param predictedDataTypeList: List of predicted data type
  :param dataTypeIndicator: List of the datatype indicator
  """

  numCorrect = 0
  for i in xrange(len(dataTypeList)):
    if dataTypeList[i] == predictedDataTypeList[i]:
      numCorrect += 1

  correctRate = float(numCorrect)/len(dataTypeList)
  print "correct rate: ", str(correctRate)


if __name__ == "__main__":

  print "Test algorithm on river-view data streams ..."
  fileNameList, filePathList, dataTypeList = downloadExampleData()
  dataTypeIndicatorList = []
  predictedDataTypeList = []
  for i in xrange(len(filePathList)):
    filePath = filePathList[i]
    predictedDataType, dataTypeIndicator = checkDataType(filePath)
    print " File: ", fileNameList[i], " DataType: ", dataTypeList[i], \
          " predicted Data Type: ", predictedDataType
    predictedDataTypeList.append(predictedDataType)
    dataTypeIndicatorList.append(dataTypeIndicator)
  checkAlgorithmPerformance(dataTypeList, predictedDataTypeList, dataTypeIndicatorList)


  print "Test algorithm on NAB data ..."
  NABPath = '/Users/ycui/nta/NAB/'
  dataPath=NABPath+'data/'
  dataDirs = [join(dataPath, f) for f in listdir(dataPath) if not isfile(join(dataPath, f))]

  dataTypeList = []
  predictedDataTypeList = []
  dataTypeIndicatorList = []
  for dir in dataDirs:
    dataFileList = [join(dir, f) for f in listdir(dir) if isfile(join(dir, f))]

    for dataFile in dataFileList:
      predictedDataType, dataTypeIndicator = checkDataType(dataFile)

      predictedDataTypeList.append(predictedDataType)
      dataTypeIndicatorList.append(dataTypeIndicator)
      dataTypeList.append('non-transactional')

      print " File: ", dataFile[i], " DataType: ", 'non-transactional', \
            " predicted Data Type: ", predictedDataType

  checkAlgorithmPerformance(dataTypeList, predictedDataTypeList, dataTypeIndicatorList)



