from __main__ import qt, ctk, slicer

from iGyneStep import *
from Helper import *
import PythonQt
import string

class iGyneFirstRegistrationStep( iGyneStep ) :

  def __init__( self, stepid ):
    self.initialize( stepid )
    self.setName( '4. Register the template' )
    self.setDescription( 'Register the template based on 3 fiducial points. Choose the points counterclockwise, starting from the one in the middle.' )
    self.__parent = super( iGyneFirstRegistrationStep, self )
    self.interactorObserverTags = []    
    self.styleObserverTags = []
    self.volume = None
    self.fixedLandmarks = None
    self.movingLandmarks = None
    self.__vrDisplayNode = None
    self.__roiTransformNode = None
    self.__baselineVolume = None
    self.__roi = None
    self.__roiObserverTag = None
    self.RMS = 0
    self.OutputMessage =""
    self.__vrDisplayNode = None
    self.__threshold = [ -1, -1 ]  
    # initialize VR stuff
    self.__vrLogic = slicer.modules.volumerendering.logic()
    self.__vrOpacityMap = None
    self.__roiSegmentationNode = None
    self.__roiVolume = None
    
    

  def createUserInterface( self ):
    '''
    '''
    self.__layout = self.__parent.createUserInterface()
     
    self.loadTemplateButton = qt.QPushButton('Choose Fiducial Points')
    self.loadTemplateButton.checkable = True
    self.__layout.addRow(self.loadTemplateButton)
    self.loadTemplateButton.connect('toggled(bool)', self.onRunButtonToggled)
	
    self.firstRegButton = qt.QPushButton('Run Registration')
    self.__registrationStatus = qt.QLabel('Register Template and Scan')
    self.__layout.addRow(self.__registrationStatus, self.firstRegButton)
    self.firstRegButton.checkable = False
    self.__layout.addRow(self.firstRegButton)
    self.firstRegButton.connect('clicked()', self.firstRegistration)
    
     #ROI
    roiLabel = qt.QLabel( 'Select ROI:' )
    self.__roiSelector = slicer.qMRMLNodeComboBox()
    self.__roiSelector.nodeTypes = ['vtkMRMLAnnotationROINode']
    self.__roiSelector.toolTip = "ROI defining the structure of interest"
    self.__roiSelector.setMRMLScene(slicer.mrmlScene)
    self.__roiSelector.addEnabled = 1
    self.__layout.addRow( roiLabel, self.__roiSelector )
    self.__roiSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onROIChanged)

    # the ROI parameters
    voiGroupBox = qt.QGroupBox()
    voiGroupBox.setTitle( 'Define VOI' )
    self.__layout.addRow( voiGroupBox )
    voiGroupBoxLayout = qt.QFormLayout( voiGroupBox )
    self.__roiWidget = PythonQt.qSlicerAnnotationsModuleWidgets.qMRMLAnnotationROIWidget()
    voiGroupBoxLayout.addRow( self.__roiWidget )
    
    # initialize VR stuff
    self.__vrLogic = slicer.modules.volumerendering.logic()

  def onROIChanged(self):
    roi = self.__roiSelector.currentNode()

    if roi != None:
    
      pNode = self.parameterNode()
      # create VR node first time a valid ROI is selected
      if self.__vrDisplayNode == None:
        self.__vrDisplayNode = self.__vrLogic.CreateVolumeRenderingDisplayNode()
        viewNode = slicer.util.getNode('vtkMRMLViewNode1')
        self.__vrDisplayNode.SetCurrentVolumeMapper(0)
        self.__vrDisplayNode.AddViewNodeID(viewNode.GetID())

        v = slicer.mrmlScene.GetNodeByID(pNode.GetParameter('baselineVolumeID'))
        self.__vrDisplayNode.SetAndObserveVolumeNodeID(v.GetID())
        self.__vrLogic.UpdateDisplayNodeFromVolumeNode(self.__vrDisplayNode, v)
        self.__vrOpacityMap = self.__vrDisplayNode.GetVolumePropertyNode().GetVolumeProperty().GetScalarOpacity()
        self.__vrColorMap = self.__vrDisplayNode.GetVolumePropertyNode().GetVolumeProperty().GetRGBTransferFunction()

        # setup color transfer function once
        self.__vrColorMap.RemoveAllPoints()
        self.__vrColorMap.AddRGBPoint(0, 0.8, 0.8, 0)
        self.__vrColorMap.AddRGBPoint(500, 0.8, 0.8, 0)


      # update VR settings each time ROI changes
      v = slicer.mrmlScene.GetNodeByID(pNode.GetParameter('baselineVolumeID'))
      self.__vrDisplayNode.SetAndObserveROINodeID(roi.GetID())
      self.__vrDisplayNode.SetCroppingEnabled(1)
      self.__vrDisplayNode.VisibilityOn()

      roi.SetAndObserveTransformNodeID(self.__roiTransformNode.GetID())

      # TODO: update opacity function based on ROI content
      # self.__vrOpacityMap.RemoveAllPoints()

      if self.__roiObserverTag != None:
        self.__roi.RemoveObserver(self.__roiObserverTag)

      self.__roi = slicer.mrmlScene.GetNodeByID(roi.GetID())
      self.__roiObserverTag = self.__roi.AddObserver('ModifiedEvent', self.processROIEvents)

      roi.SetInteractiveMode(1)

      self.__roiWidget.setMRMLAnnotationROINode(roi)
      self.__roi.VisibleOn()
     
  def processROIEvents(self,node,event):
    # get the range of intensities inside the ROI

    # get the IJK bounding box of the voxels inside ROI
    roiCenter = [0,0,0]
    roiRadius = [0,0,0]
    self.__roi.GetXYZ(roiCenter)
    self.__roi.GetRadiusXYZ(roiRadius)

    roiCorner1 = [roiCenter[0]+roiRadius[0],roiCenter[1]+roiRadius[1],roiCenter[2]+roiRadius[2],1]
    roiCorner2 = [roiCenter[0]+roiRadius[0],roiCenter[1]+roiRadius[1],roiCenter[2]-roiRadius[2],1]
    roiCorner3 = [roiCenter[0]+roiRadius[0],roiCenter[1]-roiRadius[1],roiCenter[2]+roiRadius[2],1]
    roiCorner4 = [roiCenter[0]+roiRadius[0],roiCenter[1]-roiRadius[1],roiCenter[2]-roiRadius[2],1]
    roiCorner5 = [roiCenter[0]-roiRadius[0],roiCenter[1]+roiRadius[1],roiCenter[2]+roiRadius[2],1]
    roiCorner6 = [roiCenter[0]-roiRadius[0],roiCenter[1]+roiRadius[1],roiCenter[2]-roiRadius[2],1]
    roiCorner7 = [roiCenter[0]-roiRadius[0],roiCenter[1]-roiRadius[1],roiCenter[2]+roiRadius[2],1]
    roiCorner8 = [roiCenter[0]-roiRadius[0],roiCenter[1]-roiRadius[1],roiCenter[2]-roiRadius[2],1]

    ras2ijk = vtk.vtkMatrix4x4()
    self.__baselineVolume.GetRASToIJKMatrix(ras2ijk)

    roiCorner1ijk = ras2ijk.MultiplyPoint(roiCorner1)
    roiCorner2ijk = ras2ijk.MultiplyPoint(roiCorner2)
    roiCorner3ijk = ras2ijk.MultiplyPoint(roiCorner3)
    roiCorner4ijk = ras2ijk.MultiplyPoint(roiCorner4)
    roiCorner5ijk = ras2ijk.MultiplyPoint(roiCorner5)
    roiCorner6ijk = ras2ijk.MultiplyPoint(roiCorner6)
    roiCorner7ijk = ras2ijk.MultiplyPoint(roiCorner7)
    roiCorner8ijk = ras2ijk.MultiplyPoint(roiCorner8)

    lowerIJK = [0, 0, 0]
    upperIJK = [0, 0, 0]

    lowerIJK[0] = min(roiCorner1ijk[0],roiCorner2ijk[0],roiCorner3ijk[0],roiCorner4ijk[0],roiCorner5ijk[0],roiCorner6ijk[0],roiCorner7ijk[0],roiCorner8ijk[0])
    lowerIJK[1] = min(roiCorner1ijk[1],roiCorner2ijk[1],roiCorner3ijk[1],roiCorner4ijk[1],roiCorner5ijk[1],roiCorner6ijk[1],roiCorner7ijk[1],roiCorner8ijk[1])
    lowerIJK[2] = min(roiCorner1ijk[2],roiCorner2ijk[2],roiCorner3ijk[2],roiCorner4ijk[2],roiCorner5ijk[2],roiCorner6ijk[2],roiCorner7ijk[2],roiCorner8ijk[2])

    upperIJK[0] = max(roiCorner1ijk[0],roiCorner2ijk[0],roiCorner3ijk[0],roiCorner4ijk[0],roiCorner5ijk[0],roiCorner6ijk[0],roiCorner7ijk[0],roiCorner8ijk[0])
    upperIJK[1] = max(roiCorner1ijk[1],roiCorner2ijk[1],roiCorner3ijk[1],roiCorner4ijk[1],roiCorner5ijk[1],roiCorner6ijk[1],roiCorner7ijk[1],roiCorner8ijk[1])
    upperIJK[2] = max(roiCorner1ijk[2],roiCorner2ijk[2],roiCorner3ijk[2],roiCorner4ijk[2],roiCorner5ijk[2],roiCorner6ijk[2],roiCorner7ijk[2],roiCorner8ijk[2])

    image = self.__baselineVolume.GetImageData()
    clipper = vtk.vtkImageClip()
    clipper.ClipDataOn()
    clipper.SetOutputWholeExtent(int(lowerIJK[0]),int(upperIJK[0]),int(lowerIJK[1]),int(upperIJK[1]),int(lowerIJK[2]),int(upperIJK[2]))
    clipper.SetInput(image)
    clipper.Update()

    roiImageRegion = clipper.GetOutput()
    intRange = roiImageRegion.GetScalarRange()
    lThresh = 0.4*(intRange[0]+intRange[1])
    uThresh = intRange[1]

    self.__vrOpacityMap.RemoveAllPoints()
    self.__vrOpacityMap.AddPoint(0,0)
    self.__vrOpacityMap.AddPoint(lThresh-1,0)
    self.__vrOpacityMap.AddPoint(lThresh,1)
    self.__vrOpacityMap.AddPoint(uThresh,1)
    self.__vrOpacityMap.AddPoint(uThresh+1,0)

    # finally, update the focal point to be the center of ROI
    # Don't do this actually -- this breaks volume rendering
    camera = slicer.mrmlScene.GetNodeByID('vtkMRMLCameraNode1')
    camera.SetFocalPoint(roiCenter)
    
  def onRunButtonToggled(self, checked):
    if checked:
      self.start()
      self.loadTemplateButton.text = "Stop"  
    else:
      self.stop()
      self.loadTemplateButton.text = "Choose Fiducial Points"

  def firstRegistration(self):
    print("firstreg")
    # rigidly register followup to baseline
    # TODO: do this in a separate step and allow manual adjustment?
    # TODO: add progress reporting (BRAINSfit does not report progress though)
    pNode = self.parameterNode()
    baselineVolumeID = pNode.GetParameter('baselineVolumeID')
    followupVolumeID = pNode.GetParameter('followupVolumeID')
    self.__followupTransform = slicer.mrmlScene.CreateNodeByClass('vtkMRMLLinearTransformNode')
    slicer.mrmlScene.AddNode(self.__followupTransform)
    sliceNodeCount = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLAnnotationHierarchyNode')
    self.movingLandmarks = vtk.vtkCollection()
    for nodeIndex in xrange(sliceNodeCount):
      sliceNode = slicer.mrmlScene.GetNthNodeByClass(nodeIndex, 'vtkMRMLAnnotationHierarchyNode') 
      if sliceNode.GetName() == "Fiducial List_moved":
        sliceNode.GetAssociatedChildrenNodes(self.movingLandmarks)
    
    

    parameters = {}
    parameters["fixedLandmarks"] = slicer.mrmlScene.GetNodeByID("vtkMRMLAnnotationHierarchyNode4")
    parameters["movingLandmarks"] = slicer.mrmlScene.GetNodeByID("vtkMRMLAnnotationHierarchyNode2")
    parameters["saveTransform"] = self.__followupTransform
    parameters["transformType"] = "Rigid"
    parameters["rms"] = self.RMS
    parameters["outputMessage"] = self.OutputMessage


    # self.__cliNode = None
    # self.__cliNode = slicer.cli.run(slicer.modules.brainsfit, self.__cliNode, parameters)
    
    fidreg = slicer.modules.fiducialregistration
    print(self.OutputMessage)
    print(self.RMS)
    self.__cliNode = None
    self.__cliNode = slicer.cli.run(fidreg, self.__cliNode, parameters)
    print(self.OutputMessage)
    print(self.RMS)
    
    self.__cliObserverTag = self.__cliNode.AddObserver('ModifiedEvent', self.processRegistrationCompletion)
    self.__registrationStatus.setText('Wait ...')
    self.firstRegButton.setEnabled(0)


  def processRegistrationCompletion(self, node, event):
    status = node.GetStatusString()
    self.__registrationStatus.setText('Registration '+status)
    if status == 'Completed':
      self.firstRegButton.setEnabled(1)
  
      pNode = self.parameterNode()
      followupNode = slicer.mrmlScene.GetNodeByID(pNode.GetParameter('followupVolumeID'))
      obturatorNode = slicer.mrmlScene.GetNodeByID(pNode.GetParameter('obturatorID'))
      followupNode.SetAndObserveTransformNodeID(self.__followupTransform.GetID())
      obturatorNode.SetAndObserveTransformNodeID(self.__followupTransform.GetID())
  
  
      Helper.SetBgFgVolumes(pNode.GetParameter('baselineVolumeID'),pNode.GetParameter('followupVolumeID'))

      pNode.SetParameter('followupTransformID', self.__followupTransform.GetID())
    

    
  
  
  def start(self):
    
    self.removeObservers()
    # get new slice nodes
    layoutManager = slicer.app.layoutManager()
    sliceNodeCount = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLSliceNode')
    for nodeIndex in xrange(sliceNodeCount):
      # find the widget for each node in scene
      sliceNode = slicer.mrmlScene.GetNthNodeByClass(nodeIndex, 'vtkMRMLSliceNode')
      sliceWidget = layoutManager.sliceWidget(sliceNode.GetLayoutName())      
      if sliceWidget:     
        # add obserservers and keep track of tags
        style = sliceWidget.sliceView().interactorStyle()
        self.sliceWidgetsPerStyle[style] = sliceWidget
        events = ("LeftButtonPressEvent","LeftButtonReleaseEvent","MouseMoveEvent", "KeyPressEvent","KeyReleaseEvent","EnterEvent", "LeaveEvent")
        for event in events:
          tag = style.AddObserver(event, self.processEvent)   
          self.styleObserverTags.append([style,tag])
		  
  def stop(self):

    print("here")
    self.removeObservers() 
	
  def removeObservers(self):
    # remove observers and reset
    for observee,tag in self.styleObserverTags:
      observee.RemoveObserver(tag)
    self.styleObserverTags = []
    self.sliceWidgetsPerStyle = {}
	
  def processEvent(self,observee,event=None):
    if self.fixedLandmarks == None :
      self.fixedLandmarks = vtk.vtkCollection()

    if self.sliceWidgetsPerStyle.has_key(observee) and event == "LeftButtonPressEvent":
      sliceWidget = self.sliceWidgetsPerStyle[observee]
      style = sliceWidget.sliceView().interactorStyle()          
      xy = style.GetInteractor().GetEventPosition()
      xyz = sliceWidget.convertDeviceToXYZ(xy)
      ras = sliceWidget.convertXYZToRAS(xyz)
      logic = slicer.modules.annotations.logic()
      logic.SetActiveHierarchyNodeID("vtkMRMLAnnotationHierarchyNode4")
      fiducial = slicer.mrmlScene.CreateNodeByClass('vtkMRMLAnnotationFiducialNode')
      fiducial.SetReferenceCount(fiducial.GetReferenceCount()-1)
      fiducial.SetFiducialCoordinates(ras)
      fiducial.Initialize(slicer.mrmlScene)
      # adding to hierarchy is handled by the Reporting logic
      self.fixedLandmarks.AddItem(fiducial)

      
  def validate( self, desiredBranchId ):
    '''
    '''
    self.__parent.validate( desiredBranchId )    
    self.__parent.validationSucceeded(desiredBranchId)  

  def onEntry(self,comingFrom,transitionType):
    super(iGyneFirstRegistrationStep, self).onEntry(comingFrom, transitionType)

    # setup the interface
    lm = slicer.app.layoutManager()
    lm.setLayout(3)
    pNode = self.parameterNode()

    # use this transform node to align ROI with the axes of the baseline
    # volume
    roiTfmNodeID = pNode.GetParameter('roiTransformID')
    if roiTfmNodeID != '':
      self.__roiTransformNode = Helper.getNodeByID(roiTfmNodeID)
    else:
      Helper.Error('Internal error! Error code CT-S2-NRT, please report!')
    baselineVolume = slicer.mrmlScene.GetNodeByID(pNode.GetParameter('baselineVolumeID'))
    self.__baselineVolume = slicer.mrmlScene.GetNodeByID(pNode.GetParameter('baselineVolumeID'))
    # get the roiNode from parameters node, if it exists, and initialize the
    # GUI
    self.updateWidgetFromParameterNode(pNode)
    if self.__roi != None:
      self.__roi.VisibleOn()
    pNode.SetParameter('currentStep', self.stepid)

  def onExit(self, goingTo, transitionType):
    if goingTo.id() != 'LoadModel' and goingTo.id() != 'SecondRegistration':
      return
      
    if self.__roi != None:
      self.__roi.RemoveObserver(self.__roiObserverTag)
      self.__roi.VisibleOff()
    
    pNode = self.parameterNode()
    if self.__vrDisplayNode != None:
      self.__vrDisplayNode.VisibilityOff()
      pNode.SetParameter('vrDisplayNodeID', self.__vrDisplayNode.GetID())

    pNode.SetParameter('roiNodeID', self.__roiSelector.currentNode().GetID())

    if goingTo.id() == 'SecondRegistration':
      self.doStepProcessing()

    super(iGyneFirstRegistrationStep, self).onExit(goingTo, transitionType)

  def updateWidgetFromParameterNode(self, parameterNode):
    roiNodeID = parameterNode.GetParameter('roiNodeID')

    if roiNodeID != '':
      self.__roi = slicer.mrmlScene.GetNodeByID(roiNodeID)
      self.__roiSelector.setCurrentNode(Helper.getNodeByID(self.__roi.GetID()))
    else:
      roi = slicer.mrmlScene.CreateNodeByClass('vtkMRMLAnnotationROINode')
      slicer.mrmlScene.AddNode(roi)
      parameterNode.SetParameter('roiNodeID', roi.GetID())
      self.__roiSelector.setCurrentNode(roi)
    
    self.onROIChanged()

   
  def doStepProcessing(self):
    '''
    prepare roi image for the next step
    '''
    pNode = self.parameterNode()
    cropVolumeNode =slicer.mrmlScene.CreateNodeByClass('vtkMRMLCropVolumeParametersNode')
    cropVolumeNode.SetScene(slicer.mrmlScene)
    cropVolumeNode.SetName('iGyne_CropVolume_node')
    cropVolumeNode.SetIsotropicResampling(True)
    cropVolumeNode.SetSpacingScalingConst(0.5)
    slicer.mrmlScene.AddNode(cropVolumeNode)
    # TODO hide from MRML tree

    cropVolumeNode.SetInputVolumeNodeID(pNode.GetParameter('baselineVolumeID'))
    cropVolumeNode.SetROINodeID(pNode.GetParameter('roiNodeID'))
    # cropVolumeNode.SetAndObserveOutputVolumeNodeID(outputVolume.GetID())

    cropVolumeLogic = slicer.modules.cropvolume.logic()
    cropVolumeLogic.Apply(cropVolumeNode)

    # TODO: cropvolume error checking
    outputVolume = slicer.mrmlScene.GetNodeByID(cropVolumeNode.GetOutputVolumeNodeID())
    outputVolume.SetName("baselineROI")
    pNode.SetParameter('croppedBaselineVolumeID',cropVolumeNode.GetOutputVolumeNodeID())

    roiSegmentationID = pNode.GetParameter('croppedBaselineVolumeSegmentationID') 
    if roiSegmentationID == '':
      roiRange = outputVolume.GetImageData().GetScalarRange()

      # default threshold is half-way of the range
      thresholdParameter = str(0.5*(roiRange[0]+roiRange[1]))+','+str(roiRange[1])
      pNode.SetParameter('thresholdRange', thresholdParameter)
      pNode.SetParameter('useSegmentationThresholds', 'True')

    # even if the seg. volume exists, it needs to be updated, because ROI
    # could have changed
    vl = slicer.modules.volumes.logic()
    roiSegmentation = vl.CreateLabelVolume(slicer.mrmlScene, outputVolume, 'baselineROI_segmentation')
    pNode.SetParameter('croppedBaselineVolumeSegmentationID', roiSegmentation.GetID())