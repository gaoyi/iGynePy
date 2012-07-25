from __main__ import qt, ctk

from iGyneStep import *
from Helper import *
import PythonQt

class iGyneLoadModelStep( iGyneStep ) :

  def __init__( self, stepid ):
    self.initialize( stepid )
    self.setName( '3. Load the template' )
    self.setDescription( 'Load the template. From this template, auto-crop and registration functions will be processed' )
    self.__parent = super( iGyneLoadModelStep, self )

  def createUserInterface( self ):
 
    self.__layout = self.__parent.createUserInterface()
   
    baselineScanLabel = qt.QLabel( 'CT or MR scan:' )
    self.__baselineVolumeSelector = slicer.qMRMLNodeComboBox()
    self.__baselineVolumeSelector.toolTip = "Choose the baseline scan"
    self.__baselineVolumeSelector.nodeTypes = ['vtkMRMLScalarVolumeNode']
    self.__baselineVolumeSelector.setMRMLScene(slicer.mrmlScene)
    self.__baselineVolumeSelector.addEnabled = 0

    # followupScanLabel = qt.QLabel( 'Followup scan:' )
    # self.__followupVolumeSelector = slicer.qMRMLNodeComboBox()
    # self.__followupVolumeSelector.toolTip = "Choose the followup scan"
    # self.__followupVolumeSelector.nodeTypes = ['vtkMRMLScalarVolumeNode']
    # self.__followupVolumeSelector.setMRMLScene(slicer.mrmlScene)
    # self.__followupVolumeSelector.addEnabled = 0
   
    loadTemplateButton = qt.QPushButton('Load template')
    self.__layout.addRow(loadTemplateButton)
    loadTemplateButton.connect('clicked()', self.loadTemplate)

    loadDataButton = qt.QPushButton('Load Scan')
    self.__layout.addRow(loadDataButton)
    loadDataButton.connect('clicked()', self.loadData)
    
    self.__layout.addRow( baselineScanLabel, self.__baselineVolumeSelector )
    # # the ROI parameters
    # voiGroupBox = qt.QGroupBox()
    # voiGroupBox.setTitle( 'Define VOI' )
    # self.__layout.addRow( voiGroupBox )

    # voiGroupBoxLayout = qt.QFormLayout( voiGroupBox )

    # self.__roiWidget = PythonQt.qSlicerAnnotationsModuleWidgets.qMRMLAnnotationROIWidget()
    # voiGroupBoxLayout.addRow( self.__roiWidget )

    # the ROI parameters
    #voiGroupBox = qt.QGroupBox()
    #voiGroupBox.setTitle( 'Define VOI' )
    #self.__layout.addRow( voiGroupBox )

    #voiGroupBoxLayout = qt.QFormLayout( voiGroupBox )

    #self.__roiWidget = vtk.vtkSlicerFiducialListWidget.createWidget()
    #voiGroupBoxLayout.addRow( self.__roiWidget )


    # self.__layout.addRow( followupScanLabel, self.__followupVolumeSelector )

    # self.updateWidgetFromParameters(self.parameterNode())

    # qt.QTimer.singleShot(0, self.killButton)

  def updateWidgetFromParameters(self, parameterNode):
    baselineVolumeID = parameterNode.GetParameter('baselineVolumeID')
    # followupVolumeID = parameterNode.GetParameter('followupVolumeID')
    if baselineVolumeID != None:
      self.__baselineVolumeSelector.setCurrentNode(Helper.getNodeByID(baselineVolumeID))
    # if followupVolumeID != None:
      # self.__followupVolumeSelector.setCurrentNode(Helper.getNodeByID(followupVolumeID))

  def loadData(self):
    slicer.util.loadScene("C:\Users\Guillaume\Dropbox\scene-for-template-and-obturator\Template.mrml", True)
    
  def loadTemplate(self):
    pathToScene = slicer.modules.igynepy.path.replace("iGynePy.py","iGynePyTemplate/Template/Template.mrml")
    #slicer.util.loadScene( pathToScene, True)
    slicer.util.loadScene("/home/guillaume/Work/Template/Template.mrml",True)
    # vl = slicer.modules.volumes.logic()
    # vol1 = vl.AddArchetypeVolume('http://www.slicer.org/slicerWiki/images/5/59/RegLib_C01_1.nrrd', 'Meningioma1', 0)
    # vol2 = vl.AddArchetypeVolume('http://www.slicer.org/slicerWiki/images/e/e3/RegLib_C01_2.nrrd', 'Meningioma2', 0)
    # if vol1 != None and vol2 != None:
      # self.__baselineVolumeSelector.setCurrentNode(vol1)
      # self.__followupVolumeSelector.setCurrentNode(vol1)
      # Helper.SetBgFgVolumes(vol1.GetID(), vol2.GetID())


  def onEntry(self,comingFrom,transitionType):
  
    super(iGyneLoadModelStep, self).onEntry(comingFrom, transitionType)
    # setup the interface
    pNode = self.parameterNode()
    pNode.SetParameter('currentStep', self.stepid)    
    # self.updateWidgetFromParameterNode(pNode)
    # qt.QTimer.singleShot(0, self.killButton)

  def onExit(self, goingTo, transitionType):
    if goingTo.id() != 'SelectApplicator' and goingTo.id() != 'LoadModel':
      return
    pNode = self.parameterNode()
    # if goingTo.id() == 'LoadDiagnosticSeries':
      # self.doStepProcessing()

    super(iGyneLoadModelStep, self).onExit(goingTo, transitionType)

  def validate( self, desiredBranchId ):
    '''
    '''
    self.__parent.validate( desiredBranchId )    
    self.__parent.validationSucceeded(desiredBranchId)
