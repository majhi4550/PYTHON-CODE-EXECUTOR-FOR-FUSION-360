import adsk.core, adsk.fusion, adsk.cam, traceback

_app = None
_ui = None
_handlers = []

adsk.autoTerminate(False)

def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

        # Clean up any previous command if present
        existing_cmd = _ui.commandDefinitions.itemById('CodeExecutorPro')
        if existing_cmd:
            existing_cmd.deleteMe()

        cmdDef = _ui.commandDefinitions.addButtonDefinition(
            'CodeExecutorPro',
            'Code Executor Pro',
            'Advanced Python script editor and executor for Fusion 360'
        )

        onCommandCreated = CommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)

        # Add to Tools tab
        toolsTab = _ui.allToolbarTabs.itemById('ToolsTab')
        if toolsTab:
            customPanel = toolsTab.toolbarPanels.itemById('CodeExecutorProPanel')
            if not customPanel:
                customPanel = toolsTab.toolbarPanels.add('CodeExecutorProPanel', 'Code Executor Pro')
            customPanel.controls.addCommand(cmdDef)

    except:
        if _ui:
            _ui.messageBox('Add-In start failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    global _ui
    try:
        toolsTab = _ui.allToolbarTabs.itemById('ToolsTab')
        if toolsTab:
            customPanel = toolsTab.toolbarPanels.itemById('CodeExecutorProPanel')
            if customPanel:
                ctrl = customPanel.controls.itemById('CodeExecutorPro')
                if ctrl:
                    ctrl.deleteMe()
                customPanel.deleteMe()

        cmdDef = _ui.commandDefinitions.itemById('CodeExecutorPro')
        if cmdDef:
            cmdDef.deleteMe()

    except:
        if _ui:
            _ui.messageBox('Add-In stop failed:\n{}'.format(traceback.format_exc()))

def find_input_by_id(inputs, target_id):
    """Recursively search for an input by ID in groups and subgroups"""
    for i in range(inputs.count):
        input_item = inputs.item(i)
        if input_item.id == target_id:
            return input_item
        elif hasattr(input_item, 'children'):
            # Recursively search in group children
            found = find_input_by_id(input_item.children, target_id)
            if found:
                return found
    return None

class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command
            cmd.isRepeatable = False
            inputs = cmd.commandInputs

            # Title section
            titleGroup = inputs.addGroupCommandInput('titleGroup', 'Code Executor Pro - Python Script Editor')
            titleGroup.isExpanded = True
            titleChildren = titleGroup.children

            # Info text
            titleChildren.addTextBoxCommandInput('infoText', '', 
                'Write and execute Python scripts directly in Fusion 360.\n'
                'Access Fusion 360 API through global variables: app, ui, design, rootComp', 
                2, True)

            # Code editor section
            codeGroup = inputs.addGroupCommandInput('codeGroup', 'Script Editor')
            codeGroup.isExpanded = True
            codeChildren = codeGroup.children

            # Sample code with useful examples
            sample_code = '''# Fusion 360 Python Script Editor
# Global variables available: app, ui, design, rootComp

# Example 1: Simple message
ui.messageBox("Hello from Code Executor Pro!")

# Example 2: Create a box
try:
    # Get the root component
    rootComp = design.rootComponent
    
    # Create a new sketch
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    
    # Draw a rectangle
    lines = sketch.sketchCurves.sketchLines
    rect = lines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(5, 3, 0)
    )
    
    # Create extrusion
    prof = sketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2))
    extrude = extrudes.add(extInput)
    
    ui.messageBox("Box created successfully!")
    
except Exception as e:
    ui.messageBox(f"Error creating box: {str(e)}")'''

            # Large multiline text box for code
            codeChildren.addTextBoxCommandInput('scriptInput', 'Python Code:', sample_code, 20, False)

            # Execution controls section
            controlsGroup = inputs.addGroupCommandInput('controlsGroup', 'Execution Controls')
            controlsGroup.isExpanded = True
            controlsChildren = controlsGroup.children

            # Add buttons in a row
            executeBtn = controlsChildren.addBoolValueInput('executeButton', 'Execute Script', False, '', False)
            executeBtn.tooltip = 'Run the Python script above'
            
            clearBtn = controlsChildren.addBoolValueInput('clearButton', 'Clear Editor', False, '', False)
            clearBtn.tooltip = 'Clear the code editor'
            
            # Output section
            outputGroup = inputs.addGroupCommandInput('outputGroup', 'Output/Results')
            outputGroup.isExpanded = False
            outputChildren = outputGroup.children

            outputChildren.addTextBoxCommandInput('outputText', 'Execution Results:', 
                'Script output will appear here...', 5, True)

            # Template section
            templateGroup = inputs.addGroupCommandInput('templateGroup', 'Code Templates')
            templateGroup.isExpanded = False
            templateChildren = templateGroup.children

            # Template dropdown
            templateDropdown = templateChildren.addDropDownCommandInput('templateSelect', 'Select Template:', 
                                                                       adsk.core.DropDownStyles.TextListDropDownStyle)
            templateDropdown.listItems.add('Custom Code', True)
            templateDropdown.listItems.add('Create Box', False)
            templateDropdown.listItems.add('Create Cylinder', False)
            templateDropdown.listItems.add('Create Sketch', False)
            templateDropdown.listItems.add('Component Info', False)
            templateDropdown.listItems.add('Material Properties', False)

            loadTemplateBtn = templateChildren.addBoolValueInput('loadTemplateButton', 'Load Template', False, '', False)
            loadTemplateBtn.tooltip = 'Load the selected template into the editor'

            # Event handlers
            onExecute = CommandExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)

            onInputChanged = InputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)

            onDestroy = CommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            _handlers.append(onDestroy)

        except:
            if _ui:
                _ui.messageBox('Command creation failed:\n{}'.format(traceback.format_exc()))

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        # Main execution handled in InputChangedHandler
        pass

class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            inputs = eventArgs.inputs
            changed_input = eventArgs.input

            if changed_input.id == 'executeButton' and changed_input.value:
                changed_input.value = False  # Reset button
                self.execute_script(inputs)
                
            elif changed_input.id == 'clearButton' and changed_input.value:
                changed_input.value = False  # Reset button
                
                # Find script input and output text using helper method
                script_input = find_input_by_id(inputs, 'scriptInput')
                output_text = find_input_by_id(inputs, 'outputText')
                
                if script_input:
                    script_input.text = '# Write your Python code here\n\n'
                if output_text:
                    output_text.text = 'Editor cleared. Ready for new code...'
                
            elif changed_input.id == 'loadTemplateButton' and changed_input.value:
                changed_input.value = False  # Reset button
                self.load_template(inputs)

        except:
            if _ui:
                _ui.messageBox('Input change handling failed:\n{}'.format(traceback.format_exc()))

    def execute_script(self, inputs):
        try:
            # Find inputs by searching through all inputs recursively
            script_input = find_input_by_id(inputs, 'scriptInput')
            output_text = find_input_by_id(inputs, 'outputText')
            
            if not script_input:
                _ui.messageBox('Error: Script input not found!')
                return
                
            if not output_text:
                _ui.messageBox('Error: Output text not found!')
                return
                
            code = script_input.text.strip()

            if not code:
                output_text.text = 'Error: No code to execute!'
                return

            # Prepare execution environment
            execution_globals = {
                'app': _app,
                'ui': _ui,
                'design': _app.activeProduct,
                'rootComp': _app.activeProduct.rootComponent if _app.activeProduct else None,
                'adsk': adsk,
                'traceback': traceback,
                '__builtins__': __builtins__
            }

            # Capture output
            output_text.text = 'Executing script...'
            
            try:
                # Execute the code
                exec(code, execution_globals)
                output_text.text = 'Script executed successfully!\nCheck Fusion 360 for results.'
                
            except Exception as e:
                error_msg = f'Script execution failed:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}'
                output_text.text = error_msg
                _ui.messageBox(f'Script Error:\n{str(e)}')

        except Exception as e:
            if _ui:
                _ui.messageBox(f'Execution handler failed:\n{str(e)}')

    def load_template(self, inputs):
        try:
            # Find inputs using the helper method
            template_select = find_input_by_id(inputs, 'templateSelect')
            script_input = find_input_by_id(inputs, 'scriptInput')
            output_text = find_input_by_id(inputs, 'outputText')
            
            if not template_select or not script_input or not output_text:
                _ui.messageBox('Error: Could not find required UI elements!')
                return
            
            selected_template = template_select.selectedItem.name
            
            templates = {
                'Create Box': '''# Create a simple box
try:
    # Get the root component
    rootComp = design.rootComponent
    
    # Create a new sketch on XY plane
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    
    # Draw a rectangle
    lines = sketch.sketchCurves.sketchLines
    rect = lines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(5, 3, 0)
    )
    
    # Create extrusion
    prof = sketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2))
    extrude = extrudes.add(extInput)
    
    ui.messageBox("Box created successfully!")
    
except Exception as e:
    ui.messageBox(f"Error creating box: {str(e)}")''',

                'Create Cylinder': '''# Create a cylinder
try:
    # Get the root component
    rootComp = design.rootComponent
    
    # Create a new sketch on XY plane
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    
    # Draw a circle
    circles = sketch.sketchCurves.sketchCircles
    centerPoint = adsk.core.Point3D.create(0, 0, 0)
    circle = circles.addByCenterRadius(centerPoint, 2.5)
    
    # Create extrusion
    prof = sketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(5))
    extrude = extrudes.add(extInput)
    
    ui.messageBox("Cylinder created successfully!")
    
except Exception as e:
    ui.messageBox(f"Error creating cylinder: {str(e)}")''',

                'Create Sketch': '''# Create a complex sketch
try:
    # Get the root component
    rootComp = design.rootComponent
    
    # Create a new sketch on XY plane
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    
    # Draw multiple shapes
    lines = sketch.sketchCurves.sketchLines
    circles = sketch.sketchCurves.sketchCircles
    
    # Draw a rectangle
    rect = lines.addTwoPointRectangle(
        adsk.core.Point3D.create(-2, -2, 0),
        adsk.core.Point3D.create(2, 2, 0)
    )
    
    # Draw a circle
    centerPoint = adsk.core.Point3D.create(0, 0, 0)
    circle = circles.addByCenterRadius(centerPoint, 1)
    
    # Add dimensions
    sketch.sketchDimensions.addDistanceDimension(
        rect.item(0).startSketchPoint,
        rect.item(2).startSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(0, -3, 0)
    )
    
    ui.messageBox("Complex sketch created successfully!")
    
except Exception as e:
    ui.messageBox(f"Error creating sketch: {str(e)}")''',

                'Component Info': '''# Get component information
try:
    # Get the root component
    rootComp = design.rootComponent
    
    # Collect information
    info = []
    info.append(f"Design name: {design.parentDocument.name}")
    info.append(f"Root component: {rootComp.name}")
    info.append(f"Bodies count: {rootComp.bRepBodies.count}")
    info.append(f"Sketches count: {rootComp.sketches.count}")
    info.append(f"Features count: {rootComp.features.count}")
    info.append(f"Components count: {rootComp.occurrences.count}")
    
    # Display information
    ui.messageBox("\\n".join(info))
    
except Exception as e:
    ui.messageBox(f"Error getting component info: {str(e)}")''',

                'Material Properties': '''# Get material properties
try:
    # Get the root component
    rootComp = design.rootComponent
    
    info = []
    
    # Check if there are any bodies
    if rootComp.bRepBodies.count > 0:
        for i in range(rootComp.bRepBodies.count):
            body = rootComp.bRepBodies.item(i)
            info.append(f"Body {i+1}: {body.name}")
            
            if body.material:
                material = body.material
                info.append(f"  Material: {material.name}")
                info.append(f"  Density: {material.density}")
                info.append(f"  Thermal conductivity: {material.thermalConductivity}")
            else:
                info.append(f"  No material assigned")
            
            # Physical properties
            props = body.physicalProperties
            info.append(f"  Volume: {props.volume:.4f} cm³")
            info.append(f"  Mass: {props.mass:.4f} g")
            info.append("")
    else:
        info.append("No bodies found in the design")
    
    ui.messageBox("\\n".join(info))
    
except Exception as e:
    ui.messageBox(f"Error getting material properties: {str(e)}")'''
            }
            
            if selected_template in templates:
                script_input.text = templates[selected_template]
                output_text.text = f'Template "{selected_template}" loaded successfully!'
            else:
                output_text.text = 'Please select a template first.'

        except Exception as e:
            if _ui:
                _ui.messageBox(f'Template loading failed:\n{str(e)}')

class CommandDestroyHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            global _handlers
            _handlers = []
        except:
            if _ui:
                _ui.messageBox('Command destroy failed:\n{}'.format(traceback.format_exc()))