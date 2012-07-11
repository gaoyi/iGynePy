from __main__ import vtk, qt, ctk, slicer

import iGyneWizard

class iGyne:
  def __init__( self, parent ):
    parent.title = """iGyne"""
    parent.categories = ["""Wizards"""]
    parent.contributors = ["""Andrey Fedorov""", """Xiaojun Chen""", """Guillaume Pernelle""", """Ron Kikinis"""]
    parent.helpText = """
    Igyne help....""";
    parent.acknowledgementText = """This work is supported by NA-MIC, NAC, NCIGT, and the Slicer Community. See <a href="http://www.slicer.org">http://slicer.org</a> for details.  Module implemented by Andrey Fedorov. This work was partially supported by Brain Science Foundation and NIH U01 CA151261.
    """
    self.parent = parent

class iGyneWidget:
  def __init__( self, parent=None ):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout( qt.QVBoxLayout() )
      self.parent.setMRMLScene( slicer.mrmlScene )
    else:
      self.parent = parent
    self.layout = self.parent.layout()

    # this flag is 1 if there is an update in progress
    self.__updating = 1

    # the pointer to the logic and the mrmlManager
    self.__mrmlManager = None
    self.__logic = None

    if not parent:
      self.setup()

      # after setup, be ready for events
      self.__updating = 0

      self.parent.show()

    if slicer.mrmlScene.GetTagByClassName( "vtkMRMLScriptedModuleNode" ) != 'ScriptedModule':
      slicer.mrmlScene.RegisterNodeClass(vtkMRMLScriptedModuleNode())

    # register default slots
    #self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', self.onMRMLSceneChanged)      


  #def logic( self ):
    #if not self.__logic:
    #    self.__logic = slicer.modulelogic.vtkiGyneLogic()
    #    self.__logic.SetModuleName( "iGyne" )
    #    self.__logic.SetMRMLScene( slicer.mrmlScene )
    #    self.__logic.RegisterNodes()
    #    self.__logic.InitializeEventListeners()

    #return self.__logic

  #def mrmlManager( self ):
  #  if not self.__mrmlManager:
  #      self.__mrmlManager = self.logic().GetMRMLManager()
  #      self.__mrmlManager.SetMRMLScene( slicer.mrmlScene )
  #
  #  return self.__mrmlManager


  def setup( self ):
    '''
    Create and start the iGyne workflow.
    '''
    self.workflow = ctk.ctkWorkflow()

    workflowWidget = ctk.ctkWorkflowStackedWidget()
    workflowWidget.setWorkflow( self.workflow )

    workflowWidget.buttonBoxWidget().nextButtonDefaultText = ""
    workflowWidget.buttonBoxWidget().backButtonDefaultText = ""
    
    # create all wizard steps
    selectProcedureStep = iGyneWizard.iGyneSelectProcedureStep( 'SelectProcedure'  )
    selectModalityStep = iGyneWizard.iGyneSelectModalityStep( 'SelectModality'  )
    LoadDiagnosticSeriesSetp = iGyneWizard.iGyneLoadDiagnosticSeriesSetp( 'LoadDiagnosticSeries'  )
    segmentROIStep = iGyneWizard.iGyneSegmentROIStep( 'SegmentROI'  )
    registerROIStep = iGyneWizard.iGyneRegisterROIStep( 'RegisterROI'  )

    # add the wizard steps to an array for convenience
    allSteps = []

    allSteps.append( selectProcedureStep )
    allSteps.append( selectModalityStep )
    allSteps.append( LoadDiagnosticSeriesSetp )
    allSteps.append( segmentROIStep )
    allSteps.append( registerROIStep )

    # Add transition for the first step which let's the user choose between simple and advanced mode
    self.workflow.addTransition( selectProcedureStep, selectModalityStep )
    self.workflow.addTransition( selectModalityStep, LoadDiagnosticSeriesSetp )
    self.workflow.addTransition( LoadDiagnosticSeriesSetp, segmentROIStep )
    self.workflow.addTransition( segmentROIStep, registerROIStep )

    nNodes = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLScriptedModuleNode')

    self.parameterNode = None
    for n in xrange(nNodes):
      compNode = slicer.mrmlScene.GetNthNodeByClass(n, 'vtkMRMLScriptedModuleNode')
      nodeid = None
      if compNode.GetModuleName() == 'iGyne':
        self.parameterNode = compNode
        print 'Found existing iGyne parameter node'
        break
    if self.parameterNode == None:
      self.parameterNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLScriptedModuleNode')
      self.parameterNode.SetModuleName('iGyne')
      slicer.mrmlScene.AddNode(self.parameterNode)
 
    # Propagate the workflow, the logic and the MRML Manager to the steps
    for s in allSteps:
        s.setWorkflow( self.workflow )
        s.setParameterNode (self.parameterNode)
        #s.setLogic( self.logic() )
        #s.setMRMLManager( self.mrmlManager() )

    # restore workflow step
    currentStep = self.parameterNode.GetParameter('currentStep')
    if currentStep != '':
      print 'Restoring workflow step to ', currentStep
      if currentStep == 'SelectProcedure':
        self.workflow.setInitialStep(selectProcedureStep)
      if currentStep == 'SelectModality':
        self.workflow.setInitialStep(selectModalityStep)
      if currentStep == 'LoadDiaognosticSeries':
        self.workflow.setInitialStep(LoadDiagnosticSeriesSetp)
      if currentStep == 'SegmentROI':
        self.workflow.setInitialStep(segmentROIStep)
      if currentStep == 'RegisterROI':
        self.workflow.setInitialStep(registerROIStep)
    else:
      print 'currentStep in parameter node is empty!'
        
    # start the workflow and show the widget
    self.workflow.start()
    workflowWidget.visible = True
    self.layout.addWidget( workflowWidget )

    # enable global access to the dynamicFrames on step 2 and step 6
    #slicer.modules.emsegmentSimpleDynamicFrame = defineInputChannelsSimpleStep.dynamicFrame()
    #slicer.modules.emsegmentAdvancedDynamicFrame = definePreprocessingStep.dynamicFrame()

    # compress the layout
      #self.layout.addStretch(1)        
 
  def enter(self):
    print "iGyne: enter() called"
