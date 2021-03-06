from NN_Models import Region_Filter as rFilter
import Region_Detector as detector
import os
import cv2
import numpy as np
class Target(object):
    def __init__(self):
        self.encodingString = "0,30 1.0 delta_30,100 1.0 minArea_31,400 1.0 maxArea_0,3.0 1.0 maxVariation_0,1.0 1.0 minDiversity_" \
                              "0,1000 1.0 maxEvolution_0,10 1.0 areaThreshold_0,1.0 1.0 minMargin_0,15 1.0 edgeBlurSize"
        self.rFilter = rFilter.filter_CNN()
        self.params = None
        self.canAdd = False
        self.canRemove = False
        self.initializationType = "sequential"
        self.encodingTable = None
    def build_from_genome(self,genome):
        assert genome != None, "Null genome passed to MSER target!"
        delta = genome[0][1]
        minArea = genome[1][1]
        maxArea = genome[2][1]
        maxVariation = genome[3][1]
        minDiversity = genome[4][1]
        maxEvolution = genome[5][1]
        areaThreshold = genome[6][1]
        minMargin = genome[7][1]
        edgeBlurSize = genome[8][1]
        #build parameter list from this genome
        self.params = [delta,minArea,maxArea,maxVariation,minDiversity,maxEvolution,areaThreshold,minMargin,edgeBlurSize]
    def runCondition(self,cycles):
        return cycles<10000
    def evaluate(self):
        workingDirectory = "samples_for_optimization"
        fitness = 0
        for fileName in os.listdir(workingDirectory):
            if ".png" in fileName and "ref" not in fileName:
                src = ''.join([workingDirectory,'/',fileName])
                if "625" in fileName:
                    ref = ''.join([workingDirectory,'/ref_625.png'])
                else:
                    ref = ''.join([workingDirectory,'/ref_470.png'])
                sourceImg = cv2.imread(src,cv2.IMREAD_ANYDEPTH)
                reference = cv2.imread(ref,cv2.IMREAD_ANYDEPTH)
                imName = "genome_test.png"
                regions, cells, computeTime = detector.extract_regions(sourceImg, reference, self.params, imName, cellName="a0",
                                                          flter=self.rFilter, show=False, classify=True)
                if len(regions) == 0 or len(cells)/len(regions)<=0.75 or computeTime>=175:
                    fitness =-computeTime*100
                    break
                elif len(cells)>100:
                    fitness += - computeTime/10 + len(cells) / np.power(10,int(np.log(len(cells))) - 1)
                else:
                    fitness+=len(cells)/len(regions)-computeTime
        print("\nFITNESS:",fitness,"\n")
        return fitness
    def display(self):
        print("MSER display function...")
    def validate_genome(self,genome):
        #validate genome
        return True


