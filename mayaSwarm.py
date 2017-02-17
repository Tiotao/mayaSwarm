import maya.cmds as cmds
import random



random.seed(1234)

def determineNextPosition(targetAreaSize, targetCenter, randomness):

    print targetAreaSize
    print targetCenter

    areaNumber = random.randint(0, 7)
    binary = '{:03b}'.format(areaNumber)
    
    factorX = 1 if (int(binary[0]) == 0) else -1
    factorY = 1 if (int(binary[1]) == 0) else -1
    factorZ = 1 if (int(binary[2]) == 0) else -1
    print factorX, factorY, factorZ
    # find center of the area
    targetAreaCenter = [targetCenter[0] + factorX * targetAreaSize[0] / 2, targetCenter[1] + factorY * targetAreaSize[1] / 2, targetCenter[2] + factorZ * targetAreaSize[2] / 2]

    targetPosition = [ targetAreaCenter[0] + targetAreaSize[0] * random.uniform(-randomness, randomness), targetAreaCenter[1] + targetAreaSize[1] * random.uniform(-randomness, randomness), targetAreaCenter[2] + targetAreaSize[2] * random.uniform(-randomness, randomness)]

    return targetPosition


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


# def createSubtleMovement(objectName, startTime, endTime):
#     frameCount = startTime
#     currentPosition = determineNextPosition(TARGET_AREA_LOCAL_RANGE)
#     initPosition = currentPosition
#     for frame in range(startTime, endTime):
#         if frame == frameCount:
#             if (endTime - frameCount < TARGET_GLOBAL_MOVE_DURATION_MAX/5):
#                 frameCount = endTime
#                 nextPosition = initPosition
#             else:
#                 frameCount = frameCount + random.randint(TARGET_LOCAL_MOVE_DURATION_MIN, TARGET_LOCAL_MOVE_DURATION_MAX)
#                 if (random.uniform(0, 1) > TARGET_LOCAL_THRESHOLD):
#                     nextPosition = determineNextPosition(TARGET_AREA_LOCAL_RANGE)
#                 else:
#                     nextPosition = currentPosition
            
#             moveObject(objectName, frame, frameCount, currentPosition, nextPosition)
#             currentPosition = nextPosition



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

            if (endTime - frameCount < moveDurationMax):
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
            

def generateInstances(transformName, group, config):

    for i in range(0, config['meta']['instanceAmount']):
        instanceResult = cmds.instance(transformName, name=transformName + '_instance#')
        instanceWrapperName = cmds.group(empty=True, name=transformName+'_instance_wrapper#')
        cmds.parent(instanceResult, instanceWrapperName)
        cmds.parent(instanceWrapperName, group)
        createRandomMovement(instanceWrapperName, startTime, endTime, config['global'], config['meta']['targetCenter'])
        createRandomMovement(instanceResult, startTime, endTime, config['local'], config['meta']['targetCenter'])


startTime = int(cmds.playbackOptions(query=True, minTime=True))
endTime = int(cmds.playbackOptions(query=True, maxTime=True))
transformName = cmds.ls(selection=True, type='transform')[0]

instanceGroupName = cmds.group(empty=True, name=transformName+'_instance_grp#')


# constant

TARGET_CENTER = [0, 0, 0]

# configurations
TARGET_AREA_GLOBAL_RANGE = [float(20), float(10), float(20)]

TARGET_GLOBAL_RANDOMNESS = 0.8

TARGET_GLOBAL_THRESHOLD = 0.8
TARGET_GLOBAL_MOVE_DURATION_MIN = 500
TARGET_GLOBAL_MOVE_DURATION_MAX = 1000

TARGET_LOCAL_THRESHOLD = 0
TARGET_AREA_LOCAL_RANGE = [float(0), float(0.2), float(0.2)]

TARGET_LOCAL_MOVE_DURATION_MIN = 100
TARGET_LOCAL_MOVE_DURATION_MAX = 200

INSTANCE_AMOUNT = 50


config = {
    'meta': {
        'targetCenter': TARGET_CENTER,
        'instanceAmount': INSTANCE_AMOUNT
    },
    'global': {
        'areaRange': TARGET_AREA_GLOBAL_RANGE,
        'randomness': TARGET_GLOBAL_RANDOMNESS,
        'threshold': TARGET_GLOBAL_THRESHOLD,
        'moveDurationMax': TARGET_GLOBAL_MOVE_DURATION_MAX,
        'moveDurationMin': TARGET_GLOBAL_MOVE_DURATION_MIN
    },
    'local': {
        'areaRange': TARGET_AREA_LOCAL_RANGE,
        'randomness': TARGET_GLOBAL_RANDOMNESS,
        'threshold': TARGET_LOCAL_THRESHOLD,
        'moveDurationMax': TARGET_LOCAL_MOVE_DURATION_MAX,
        'moveDurationMin': TARGET_LOCAL_MOVE_DURATION_MIN
    }
}



generateInstances(transformName, instanceGroupName, config)
cmds.hide(transformName)
cmds.xform(instanceGroupName, centerPivots=True)



