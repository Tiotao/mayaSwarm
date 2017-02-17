import maya.cmds as cmds
import random
import functools

random.seed(1234)

# default values
TARGET_CENTER = [0, 0, 0]
INSTANCE_AMOUNT = 50

TARGET_AREA_GLOBAL_RANGE = [float(20), float(10), float(20)]
TARGET_GLOBAL_RANDOMNESS = 0.8
TARGET_GLOBAL_THRESHOLD = 0.8
TARGET_GLOBAL_MOVE_DURATION_MIN = 500
TARGET_GLOBAL_MOVE_DURATION_MAX = 1000

TARGET_AREA_LOCAL_RANGE = [float(0), float(0.2), float(0.2)]
TARGET_LOCAL_THRESHOLD = 0
TARGET_LOCAL_RANDOMNESS = 0.8
TARGET_LOCAL_MOVE_DURATION_MIN = 100
TARGET_LOCAL_MOVE_DURATION_MAX = 200


'''
detemmine instance's next position
'''
def determineNextPosition(targetAreaSize, targetCenter, randomness):
    # determine which area to go to
    areaNumber = random.randint(0, 7)
    binary = '{:03b}'.format(areaNumber)
    factorX = 1 if (int(binary[0]) == 0) else -1
    factorY = 1 if (int(binary[1]) == 0) else -1
    factorZ = 1 if (int(binary[2]) == 0) else -1

    # find center of the area
    targetAreaCenter = [targetCenter[0] + factorX * targetAreaSize[0] / 2, targetCenter[1] + factorY * targetAreaSize[1] / 2, targetCenter[2] + factorZ * targetAreaSize[2] / 2]
    # find exact position
    targetPosition = [ targetAreaCenter[0] + targetAreaSize[0] * random.uniform(-randomness, randomness), targetAreaCenter[1] + targetAreaSize[1] * random.uniform(-randomness, randomness), targetAreaCenter[2] + targetAreaSize[2] * random.uniform(-randomness, randomness)]

    return targetPosition

'''
move an instance in given time
'''
def moveObject(objectName, startTime, endTime, fromPosition, toPosition):
    cmds.cutKey(objectName, time=(startTime, endTime), attribute='translateX')
    cmds.cutKey(objectName, time=(startTime, endTime), attribute='translateY')
    cmds.cutKey(objectName, time=(startTime, endTime), attribute='translateZ')
    # at fromPosition at startTime
    cmds.setKeyframe(objectName, time=startTime, attribute='translateX', value=fromPosition[0])
    cmds.setKeyframe(objectName, time=startTime, attribute='translateY', value=fromPosition[1])
    cmds.setKeyframe(objectName, time=startTime, attribute='translateZ', value=fromPosition[2])
    # move to toPosition at endTime
    cmds.setKeyframe(objectName, time=endTime, attribute='translateX', value=toPosition[0])
    cmds.setKeyframe(objectName, time=endTime, attribute='translateY', value=toPosition[1])
    cmds.setKeyframe(objectName, time=endTime, attribute='translateZ', value=toPosition[2])

'''
create random movement of an instance
'''
def createRandomMovement(objectName, startTime, endTime, config, targetCenter):
    areaRange = config['areaRange']
    threshold = config['threshold']
    moveDurationMax = config['moveDurationMax']
    moveDurationMin = config['moveDurationMin']
    randomness = config['randomness']

    frameCount = startTime
    currentPosition = determineNextPosition(areaRange, targetCenter, randomness)
    initPosition = currentPosition
    for frame in range(startTime, endTime):
        if frame == frameCount:
            if (endTime - frameCount < moveDurationMax + moveDurationMin):
                frameCount = endTime
                nextPosition = initPosition
            else:
                frameCount = frameCount + random.randint(moveDurationMin, moveDurationMax)
                if (random.uniform(0, 1) > threshold):
                    nextPosition = determineNextPosition(areaRange, targetCenter, randomness)
                else:
                    nextPosition = currentPosition
            moveObject(objectName, frame, frameCount, currentPosition, nextPosition)
            currentPosition = nextPosition
            
'''
generate instances and create their local and global random movement
'''
def generateInstances(transformName, group, config):
    for i in range(0, config['meta']['instanceAmount']):
        instanceResult = cmds.instance(transformName, name=transformName + '_instance#')
        instanceWrapperName = cmds.group(empty=True, name=transformName+'_instance_wrapper#')
        cmds.parent(instanceResult, instanceWrapperName)
        cmds.parent(instanceWrapperName, group)
        # global random movement
        createRandomMovement(instanceWrapperName, startTime, endTime, config['global'], config['meta']['targetCenter'])
        # local random movement
        createRandomMovement(instanceResult, startTime, endTime, config['local'], config['meta']['targetCenter'])

'''
get settings from UI fields
'''
def getFieldData(configFields):
    config = {
        'meta': {
            'targetCenter': [cmds.floatField(x, query=True, value=True) for x in configFields['meta']['targetCenter']],
            'instanceAmount': cmds.intField(configFields['meta']['instanceAmount'], query=True, value=True)
        },
        'global': {
            'areaRange': [cmds.floatField(x, query=True, value=True) for x in configFields['global']['areaRange']],
            'randomness': cmds.floatSliderGrp(configFields['global']['randomness'], query=True, value=True),
            'threshold': cmds.floatSliderGrp(configFields['global']['threshold'], query=True, value=True),
            'moveDurationMax': cmds.intField(configFields['global']['moveDurationMax'], query=True, value=True),
            'moveDurationMin': cmds.intField(configFields['global']['moveDurationMin'], query=True, value=True)
        },
        'local': {
            'areaRange': [cmds.floatField(x, query=True, value=True) for x in configFields['local']['areaRange']],
            'randomness': cmds.floatSliderGrp(configFields['local']['randomness'], query=True, value=True),
            'threshold': cmds.floatSliderGrp(configFields['local']['threshold'], query=True, value=True),
            'moveDurationMax': cmds.intField(configFields['local']['moveDurationMax'], query=True, value=True),
            'moveDurationMin': cmds.intField(configFields['local']['moveDurationMin'], query=True, value=True)
        }
    }
    return config

'''
execuete script after APPLY is clicked
'''
def applyCallback(configFields, windowId, *args):
    config = getFieldData(configFields)
    startTime = int(cmds.playbackOptions(query=True, minTime=True))
    endTime = int(cmds.playbackOptions(query=True, maxTime=True))
    transformName = cmds.ls(selection=True, type='transform')[0]
    instanceGroupName = cmds.group(empty=True, name=transformName+'_instance_grp#')
    generateInstances(transformName, instanceGroupName, config)
    cmds.hide(transformName)
    cmds.xform(instanceGroupName, centerPivots=True)
    if cmds.window(windowId, exists=True):
        cmds.deleteUI(windowId)

'''
draw UI
'''
def createUI(windowTitle, callback):
    windowId = 'swarm'
    if cmds.window(windowId, exists=True):
        cmds.deleteUI(windowId)
    
    cmds.window(windowId, title=windowTitle, sizeable=False, resizeToFitChildren=True)
    cmds.columnLayout("wrapper", adjustableColumn = True)
    
    # meta information
    cmds.frameLayout ("metaFrame", label = "Meta", collapsable = True, borderStyle = "etchedIn", parent = "wrapper")
    cmds.rowColumnLayout("metaContent", numberOfColumns=4, parent="metaFrame", columnOffset=[1, 'right', 3], columnWidth=[(1, 100), (2, 100), (3, 100), (4, 100)])
    cmds.text(label='Target center: ')
    targetCenter = [cmds.floatField(value=TARGET_CENTER[0]), cmds.floatField(value=TARGET_CENTER[1]), cmds.floatField(value=TARGET_CENTER[2])]
    cmds.text(label='Instance amount: ')
    instanceAmount = cmds.intField(value=INSTANCE_AMOUNT)
    cmds.separator(h=10, style='none')
    cmds.separator(h=10, style='none')

    # global information
    cmds.frameLayout ("globalFrame", label = "Global", collapsable = True, borderStyle = "etchedIn", parent = "wrapper")
    cmds.rowColumnLayout("globalContent", numberOfColumns=4, parent="globalFrame", columnOffset=[1, 'right', 3], columnWidth=[(1, 100), (2, 100), (3, 100), (4, 100)])
    cmds.text(label='Area range: ')
    globalAreaRange = [cmds.floatField(value=TARGET_AREA_GLOBAL_RANGE[0]), cmds.floatField(value=TARGET_AREA_GLOBAL_RANGE[1]), cmds.floatField(value=TARGET_AREA_GLOBAL_RANGE[2])]
    cmds.text(label='Move Duration: ')
    globalMoveDurationMin = cmds.intField(value=TARGET_GLOBAL_MOVE_DURATION_MIN)
    cmds.text(label=' - ')
    globalMoveDurationMax = cmds.intField(value=TARGET_GLOBAL_MOVE_DURATION_MAX)
    cmds.columnLayout("globalSliders", adjustableColumn = True, parent = "globalFrame")
    globalRandomness = cmds.floatSliderGrp( label='Randomness: ', field=True, minValue=0.0, maxValue=1.0, fieldMinValue=0.0, fieldMaxValue=1.0, value=TARGET_GLOBAL_RANDOMNESS, columnWidth3=[100, 100, 100])
    globalThreshold = cmds.floatSliderGrp( label='Threshold: ', field=True, minValue=0.0, maxValue=1.0, fieldMinValue=0.0, fieldMaxValue=1.0, value=TARGET_GLOBAL_THRESHOLD , columnWidth3=[100, 100, 100])

    # local information
    cmds.frameLayout ("localFrame", label = "Local", collapsable = True, borderStyle = "etchedIn", parent = "wrapper")
    cmds.rowColumnLayout("localContent", numberOfColumns=4, parent="localFrame", columnOffset=[1, 'right', 3], columnWidth=[(1, 100), (2, 100), (3, 100), (4, 100)])
    cmds.text(label='Area range: ')
    localAreaRange = [cmds.floatField(value=TARGET_AREA_LOCAL_RANGE[0]), cmds.floatField(value=TARGET_AREA_LOCAL_RANGE[1]), cmds.floatField(value=TARGET_AREA_LOCAL_RANGE[2])]
    cmds.text(label='Move duration: ')
    localMoveDurationMin = cmds.intField(value=TARGET_LOCAL_MOVE_DURATION_MIN)
    cmds.text(label=' - ')
    localMoveDurationMax = cmds.intField(value=TARGET_LOCAL_MOVE_DURATION_MAX)
    cmds.columnLayout("localSliders", adjustableColumn = True, parent = "localFrame")
    localRandomness = cmds.floatSliderGrp( label='Randomness: ', field=True, minValue=0.0, maxValue=1.0, fieldMinValue=0.0, fieldMaxValue=1.0, value=TARGET_LOCAL_RANDOMNESS, columnWidth3=[100, 100, 100])
    localThreshold = cmds.floatSliderGrp( label='Threshold: ', field=True, minValue=0.0, maxValue=1.0, fieldMinValue=0.0, fieldMaxValue=1.0, value=TARGET_LOCAL_THRESHOLD , columnWidth3=[100, 100, 100])

    # action
    cmds.rowColumnLayout("action", numberOfColumns=2, parent="wrapper", columnWidth=[(1, 200), (2, 200)])

        
    configFields = {
        'meta': {
            'targetCenter': targetCenter,
            'instanceAmount': instanceAmount
        },
        'global': {
            'areaRange': globalAreaRange,
            'randomness': globalRandomness,
            'threshold': globalThreshold,
            'moveDurationMax': globalMoveDurationMax,
            'moveDurationMin': globalMoveDurationMin
        },
        'local': {
            'areaRange': localAreaRange,
            'randomness': localRandomness,
            'threshold': localThreshold,
            'moveDurationMax': localMoveDurationMax,
            'moveDurationMin': localMoveDurationMin
        }
    }

    cmds.button(label='Apply', command=functools.partial( callback,
                                                 configFields, windowId ) )
    
    def cancelCallback(*pArgs):
        if cmds.window(windowId, exists=True):
            cmds.deleteUI(windowId)
    
    cmds.button(label='Cancel', command=cancelCallback)
    
    cmds.showWindow()


createUI('Create Swarm Instances', applyCallback)