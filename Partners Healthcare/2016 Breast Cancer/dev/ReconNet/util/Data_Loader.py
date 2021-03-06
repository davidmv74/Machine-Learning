"""
Copyright 2017 Matthew W. Allen
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import cv2
import numpy as np
import keras
from util import Image_Excel_Wrapper as cell_reader
"""
    Function to walk through all sub-folders in a given directory and return a list containing the full file path of
    every file found in each sub-folder. The file path is given in "workingDir/folder1/folder2/.../file.extension" format.
"""
def list_files(workingDirectory):
    filePaths = []

    for root, dirs, files in os.walk(workingDirectory):
        for name in files:
            filePaths.append(os.path.join(root, name).replace("\\","/"))
    return filePaths
"""Function to load and process all available training images."""
def load_data(path,numClasses=None):
    #Get images sized to 64x64x1 and fill xTrain, yTrain tuples with them.
    trainingData = get_images(path,(64,64))
    trainingSets = []
    validationSets = []
    inputShapes = []
    if numClasses is None:
        bins470 = [0,0.1,0.2,0.3,0.4,0.5,0.6]
        bins625 = [0,0.125,0.25,0.375,0.5,0.625,0.75]
        #bins470 = [0, 0.2, 0.35, 0.45, 0.6]
        #bins625 = [0, 0.2, 0.375, 0.5, 0.75]
        num470Classes = len(bins470)-1
        num625Classes = len(bins625)-1
        trainingData = bin_data(trainingData,bins=[bins470,bins625])
    else:
        num470Classes = numClasses
        num625Classes = numClasses
        bins = create_bins_for_data(trainingData,numClasses)
        print(bins)
        trainingData = bin_data(trainingData,bins)
    classes = [num470Classes,num625Classes]
    for channel in range(len(trainingData[0]["x"])):
        x = []
        y = []
        for sample in trainingData:
            x.append(sample["x"][channel])
            y.append(sample["y"][channel])
        train, val, inputShape = process_training_set(x,y,classes[channel])
        trainingSets.append(train)
        validationSets.append(val)
        inputShapes.append(inputShape)
    return trainingSets, validationSets, inputShapes, classes

def process_training_set(xTrain, yTrain, numClasses):
    xTrain = np.asarray(xTrain)
    yTrain = np.asarray(yTrain)
    print("Processing training set, input shape:",xTrain.shape)
    # Shuffle training set and split for training and validation.
    xTrain, yTrain = shuffle(xTrain, yTrain)
    xTrain, yTrain, xVal, yVal = split(xTrain, yTrain)
    rows, cols = xTrain.shape[1:]

    # Reshape x arrays to (batches,rows,cols,channels).
    xTrain = xTrain.reshape(xTrain.shape[0], rows, cols, 1)
    xVal = xVal.reshape(xVal.shape[0], rows, cols, 1)

    # Determine input shape (64x64x1).
    inputShape = (rows, cols, 1)

    xTrain = xTrain.astype('float32')
    xVal = xVal.astype('float32')

    # Calculate channel-wise image mean and subtract it from x arrays.
    mean = np.mean(xTrain)
    print("CHANNEL-WISE IMAGE MEAN: ", mean)
    xTrain -= mean
    xVal -= mean

    # Normalize x arrays to be within 0,1.
    xTrain = np.divide(xTrain, np.power(2, 16) - 1)
    xVal = np.divide(xVal, np.power(2, 16) - 1)

    print('xTrain shape:', xTrain.shape)
    print("yTrain shape:", yTrain.shape)
    print(xTrain.shape[0], 'train samples')
    print(xVal.shape[0], 'test samples')
    # Convert class vectors to binary class matrices.
    y = [y for y in yTrain]
    vy = [y  for y in yVal]

    y = keras.utils.to_categorical(y, numClasses)
    vy = keras.utils.to_categorical(vy, numClasses)
    yTrain = np.asarray(y)
    yVal = np.asarray(vy)
    print(yTrain.shape,yVal.shape)
    return (xTrain, yTrain), (xVal, yVal), inputShape

"""
    Function to load, reshape and return all available images in the training set.
    @param path: The file path to all sub-folders for each class of training data.
    @param size: The desired shape for each image.
"""
def get_images(path,shape):
    print("Getting images...")
    #File paths for training data.
    samples = cell_reader.load_cell_images(''.join([path,'/','cells']))
    noise = cell_reader.load_noise_images(''.join([path,'/','non_cells']))
    trainingSamples = []
    for sample in samples:
        if sample["625"]["coordinates"][0] == -1 or sample["470"]["coordinates"][0] == -1:
            continue
        sampleDict = {}
        img1 = cv2.resize(sample["470"]["pixels"],shape,cv2.INTER_CUBIC)
        img2 = cv2.resize(sample["625"]["pixels"],shape,cv2.INTER_CUBIC)
        sampleDict["x"] = [img1,img2]
        sampleDict["y"] = [sample["470"]["intensities"][0],sample["625"]["intensities"][0]]
        trainingSamples.append(sampleDict)
    for sample in noise:
        if sample["625"]["coordinates"][0] == -1 or sample["470"]["coordinates"][0] == -1:
            continue
        sampleDict = {}
        img1 = cv2.resize(sample["470"]["pixels"],shape,cv2.INTER_CUBIC)
        img2 = cv2.resize(sample["625"]["pixels"],shape,cv2.INTER_CUBIC)
        sampleDict["x"] = [img1,img2]
        sampleDict["y"] = [-1,-1]
        trainingSamples.append(sampleDict)
    return trainingSamples
def create_bins_for_data(data,numBins):
    bins = []
    for i in range(len(data[0]["y"])):
        currentBin = [0]
        dataRange = []
        dat = [[entry["x"][i], entry["y"][i]] for entry in data]
        dat.sort(key=lambda x: x[1])
        dat = np.asarray(dat)
        for j in range(numBins):
            step = len(dat) // numBins
            dataRange.append(dat[j * step:step + j * step])
        for entry in dataRange:
            minVal = entry[0][1]
            maxVal = minVal
            for arg in entry:
                if arg[1] < minVal:
                    minVal = arg[1]
                if arg[1] > maxVal:
                    maxVal = arg[1]
            currentBin.append(maxVal)
        bins.append(currentBin)
    return bins
def bin_data(data,bins):
    print("Sorting data set into bins...")
    trainingData = []
    for i in range(len(data)):
        for j in range(len(bins)):
            foundBin = False
            for k in range(len(bins[j])-1):
                #print(k)
                if data[i]["y"][j] >= bins[j][k] and data[i]["y"][j] < bins[j][k+1]:
                    foundBin = True
                    data[i]["y"][j] = k
            if not foundBin:
                data[i]["y"][j] = len(bins[j]) - 2
        trainingData.append(data[i])
    trainingData = np.asarray(trainingData)
    return trainingData


"""
    Function to split training data into training and validation data sets.
    @param x: Tuple containing all x training data.
    @param y: Tuple containing all y training data.
    @param splitRatio: Ratio of validation data to training data
"""
def split(x,y,splitRatio=1/3):
    val = int(round(len(y)*splitRatio))
    xv = x[:val]
    yv = y[:val]
    nx = x[val:]
    ny = y[val:]
    return np.asarray(nx),np.asarray(ny),np.asarray(xv),np.asarray(yv)

"""Function to shuffle two tuples of equal length."""
def shuffle(x,y):
    print("Shuffling training set...")
    #Create new tuples that will contain shuffled data.
    nx = []
    ny = []

    indicesToSelect = [i for i in range(len(y))]
    while(len(indicesToSelect)>0):
        idx = np.random.randint(0,len(indicesToSelect))
        val = indicesToSelect[idx]
        nx.append(x[val])
        ny.append(y[val])
        indicesToSelect.pop(idx)
    return np.asarray(nx),np.asarray(ny)