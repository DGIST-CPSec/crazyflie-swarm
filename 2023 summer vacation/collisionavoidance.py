import math

class Vec3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class Vec:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

def vec2svec(v):
    return Vec(v.x, v.y, v.z)

def svec2vec(v):
    return Vec3(v.x, v.y, v.z)

def vadd(a, b):
    return Vec3(a.x + b.x, a.y + b.y, a.z + b.z)

def vsub(a, b):
    return Vec3(a.x - b.x, a.y - b.y, a.z - b.z)

def vmag(v):
    return math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)

def vdiv(v, s):
    return Vec3(v.x / s, v.y / s, v.z / s)

def vcross(a, b):
    return Vec3(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x)

def vindex(v, idx):
    if idx == 0:
        return v.x
    elif idx == 1:
        return v.y
    elif idx == 2:
        return v.z
    else:
        raise ValueError("Invalid index")

def fminf(a, b):
    return min(a, b)

def fmaxf(a, b):
    return max(a, b)

def fsqr(a):
    return a * a

def veltmul(v1, v2):
    return Vec3(v1.x * v2.x, v1.y * v2.y, v1.z * v2.z)

def veltrecip(v):
    return Vec3(1.0 / v.x, 1.0 / v.y, 1.0 / v.z)

def vscl(s, v):
    return Vec3(s * v.x, s * v.y, s * v.z)

def vclampnorm(v, s):
    mag = vmag(v)
    if mag > s:
        return vscl(s / mag, v)
    return v

def rayintersectpolytope(origin, direction, A, B, nRows, _):
    rayScale = float('inf')
    for i in range(nRows):
        numerator = B[i] - A[i * 3] * origin.x - A[i * 3 + 1] * origin.y - A[i * 3 + 2] * origin.z
        denominator = A[i * 3] * direction.x + A[i * 3 + 1] * direction.y + A[i * 3 + 2] * direction.z
        if denominator != 0.0:
            scale = numerator / denominator
            if scale >= 0.0 and scale < rayScale:
                rayScale = scale
    return rayScale

def vprojectpolytope(v, A, B, projectionWorkspace, nRows, tolerance, maxIters):
    projection = Vec3(v.x, v.y, v.z)
    for _ in range(maxIters):
        violation = False
        for i in range(nRows):
            dotprod = A[i * 3] * projection.x + A[i * 3 + 1] * projection.y + A[i * 3 + 2] * projection.z
            if dotprod > B[i] + tolerance:
                violation = True
                projection = vsub(projection, vscl(dotprod - B[i] - tolerance, Vec3(A[i * 3], A[i * 3 + 1], A[i * 3 + 2])))
        if not violation:
            return projection
    return projection

class Setpoint:
    def __init__(self, position, velocity, mode):
        self.position = position
        self.velocity = velocity
        self.mode = mode

class CollisionAvoidanceParams:
    def __init__(self):
        self.ellipsoidRadii = Vec(0.3, 0.3, 0.9)
        self.bboxMin = Vec(-float('inf'), -float('inf'), -float('inf'))
        self.bboxMax = Vec(float('inf'), float('inf'), float('inf'))
        self.horizonSecs = 1.0
        self.maxSpeed = 0.5
        self.sidestepThreshold = 0.25
        self.maxPeerLocAgeMillis = 5000
        self.voronoiProjectionTolerance = 1e-5
        self.voronoiProjectionMaxIters = 100

class CollisionAvoidanceState:
    def __init__(self):
        self.lastFeasibleSetPosition = Vec3(float('nan'), float('nan'), float('nan'))

def sidestepGoal(params, goal, modifyIfInside, A, B, projectionWorkspace, nRows):
    rayScale = rayintersectpolytope(Vec3(0, 0, 0), goal, A, B, nRows, None)
    if rayScale >= 1.0 and not modifyIfInside:
        return goal
    distance = vmag(goal)
    distFromWall = rayScale * distance
    if distFromWall <= params.sidestepThreshold:
        sidestepDir = vcross(goal, Vec(0, 0, 1))
        sidestepAmount = fsqr(1.0 - distFromWall / params.sidestepThreshold)
        goal = vadd(goal, vscl(sidestepAmount, sidestepDir))
    return vprojectpolytope(goal, A, B, projectionWorkspace, nRows, params.voronoiProjectionTolerance, params.voronoiProjectionMaxIters)

def collisionAvoidanceUpdateSetpointCore(params, collisionState, nOthers, otherPositions, workspace, setpoint, sensorData, state):
    nRows = nOthers + 6
    A = workspace[:3*nRows]
    B = workspace[3*nRows:6*nRows]
    projectionWorkspace = workspace[6*nRows:10*nRows]

    radiiInv = veltrecip(params.ellipsoidRadii)
    ourPos = vec2svec(state.position)

    for i in range(nOthers):
        peerPos = Vec(otherPositions[3*i], otherPositions[3*i + 1], otherPositions[3*i + 2])
        toPeerStretched = veltmul(vsub(peerPos, ourPos), radiiInv)
        dist = vmag(toPeerStretched)
        a = vdiv(veltmul(toPeerStretched, radiiInv), dist)
        b = dist / 2.0 - 1.0
        scale = 1.0 / vmag(a)
        A[3*i] = scale * a.x
        A[3*i + 1] = scale * a.y
        A[3*i + 2] = scale * a.z
        B[i] = scale * b

    maxDist = params.horizonSecs * params.maxSpeed

    for dim in range(3):
        boxMax = vindex(params.bboxMax, dim) - vindex(ourPos, dim)
        A[3 * (nOthers + dim) + dim] = 1.0
        B[nOthers + dim] = fminf(maxDist, boxMax)

        boxMin = vindex(params.bboxMin, dim) - vindex(ourPos, dim)
        A[3 * (nOthers + dim + 3) + dim] = -1.0
        B[nOthers + dim + 3] = -fmaxf(-maxDist, boxMin)

    inPolytopeTolerance = 10.0 * params.voronoiProjectionTolerance
    setPos = vec2svec(setpoint.position)
    setVel = vec2svec(setpoint.velocity)

    if setpoint.mode.x == modeVelocity:
        pseudoGoal = vscl(params.horizonSecs, setVel)
        pseudoGoal = sidestepGoal(params, pseudoGoal, True, A, B, projectionWorkspace, nRows)
        if vindex(pseudoGoal, 0) != 0.0 or vindex(pseudoGoal, 1) != 0.0 or vindex(pseudoGoal, 2) != 0.0:
            setVel = vdiv(pseudoGoal, params.horizonSecs)
        else:
            setVel = Vec(0, 0, 0)
        collisionState.lastFeasibleSetPosition = ourPos
    elif setpoint.mode.x == modeAbs:
        setPosRelative = vsub(setPos, ourPos)
        setPosRelativeNew = sidestepGoal(params, setPosRelative, False, A, B, projectionWorkspace, nRows)

        if (vindex(setPosRelativeNew, 0) != vindex(setPosRelative, 0) or
                vindex(setPosRelativeNew, 1) != vindex(setPosRelative, 1) or
                vindex(setPosRelativeNew, 2) != vindex(setPosRelative, 2)):
            setPos = vadd(ourPos, setPosRelativeNew)
            setVel = Vec(0, 0, 0)
        elif setVel.x == 0.0 and setVel.y == 0.0 and setVel.z == 0.0:
            setPos = vadd(ourPos, setPosRelativeNew)
        else:
            scale = rayintersectpolytope(setPosRelative, setVel, A, B, nRows, None)
            if scale < 1.0:
                setVel = vscl(scale, setVel)
    else:
        pass  # Unsupported control mode, do nothing.

    setpoint.position = svec2vec(setPos)
    setpoint.velocity = svec2vec(setVel)

class Mode:
    def __init__(self, x):
        self.x = x

modeVelocity = Mode(0)
modeAbs = Mode(1)

collisionAvoidanceEnable = False
params = CollisionAvoidanceParams()
collisionState = CollisionAvoidanceState()
latency = 0

def collisionAvoidanceInit():
    pass

def collisionAvoidanceTest():
    return True

def collisionAvoidanceUpdateSetpoint(setpoint, sensorData, state, tick):
    global latency, collisionAvoidanceEnable, params, collisionState
    if not collisionAvoidanceEnable:
        return

    time = tick
    doAgeFilter = params.maxPeerLocAgeMillis >= 0
    nOthers = 0

    for i in range(PEER_LOCALIZATION_MAX_NEIGHBORS):
        otherPos = peerLocalizationGetPositionByIdx(i)

        if otherPos is None or otherPos.id == 0:
            continue

        if doAgeFilter and (time - otherPos.pos.timestamp > params.maxPeerLocAgeMillis):
            continue

        workspace[3 * nOthers] = otherPos.pos.x
        workspace[3 * nOthers + 1] = otherPos.pos.y
        workspace[3 * nOthers + 2] = otherPos.pos.z
        nOthers += 1

    collisionAvoidanceUpdateSetpointCore(params, collisionState, nOthers, workspace, workspace, setpoint, sensorData, state)
    latency = time - tick

class PeerLocalizationOtherPosition:
    def __init__(self, id, pos):
        self.id = id
        self.pos = pos

PEER_LOCALIZATION_MAX_NEIGHBORS = 10

def peerLocalizationGetPositionByIdx(idx):
    # Replace this function with your actual peer localization implementation
    # For the sake of this example, we'll return some dummy values.
    if idx == 0:
        return PeerLocalizationOtherPosition(1, Vec(1, 1, 1))
    elif idx == 1:
        return PeerLocalizationOtherPosition(2, Vec(2, 2, 2))
    else:
        return None

def log_add(*args):
    pass

def log_group_start(*args):
    pass

def log_group_stop(*args):
    pass

def main():
    # Example usage
    setpoint = Setpoint(Vec3(0, 0, 0), Vec3(0, 0, 0), modeVelocity)
    sensorData = None  # Replace this with actual sensor data
    state = None  # Replace this with actual state data
    tick = 0  # Replace this with actual time/tick value
    collisionAvoidanceUpdateSetpoint(setpoint, sensorData, state, tick)
    print(f"Modified Setpoint: Position: ({setpoint.position.x}, {setpoint.position.y}, {setpoint.position.z}), "
          f"Velocity: ({setpoint.velocity.x}, {setpoint.velocity.y}, {setpoint.velocity.z})")

if __name__ == "__main__":
    main()
