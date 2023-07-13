import numpy as np
from omni.audio2face.common import log_error, log_info, log_warn
from scipy.optimize import lsq_linear
from pythonosc import udp_client  


class FacsSolver:
    def __init__(self, neutral_mat, delta_mat):
        self.weightRegulCoeff = 3.5
        self.weightRegulCoeff_scale = 10.0
        self.prevRegulCoeff = 3.5
        self.prevRegulCoeff_scale = 100.0
        self.sparseRegulCoeff = 1.0
        self.sparseRegulCoeff_scale = 0.25
        self.symmetryRegulCoeff = 1.0
        self.symmetryRegulCoeff_scale = 10.0

        self.neutral_mat = neutral_mat
        self.delta_mat_orig = delta_mat
        self.delta_mat = delta_mat

        self.numPoses_orig = self.delta_mat_orig.shape[1]
        self.numPoses = self.numPoses_orig

        self.lb_orig = np.zeros(self.numPoses_orig)
        self.ub_orig = self.lb_orig + 1.0
        self.lb = self.lb_orig.copy()
        self.ub = self.ub_orig.copy()

        self.activeIdxMap = range(self.numPoses_orig)
        self.activePosesBool = np.array([True for pi in range(self.numPoses_orig)], dtype=bool)
        self.cancelPoseIndices = np.array([-1 for pi in range(self.numPoses_orig)], dtype=int)
        self.symmetryPoseIndices = np.array([-1 for pi in range(self.numPoses_orig)], dtype=int)
        self.cancelList = []
        self.symmetryList = []
        self.symShapeMat = np.zeros((self.numPoses_orig, self.numPoses_orig))
        self.prevWeights = np.zeros(self.numPoses_orig)
        # TODO L1 implementation
        l1RegulMat = np.ones((1, self.numPoses))
        self.l1RegulMat = np.dot(l1RegulMat.T, l1RegulMat)

        self.compute_A_mat()

    def compute_A_mat(self):
        self.A = (
            np.dot(self.delta_mat.T, self.delta_mat)
            + self.weightRegulCoeff * self.weightRegulCoeff_scale * np.eye(self.numPoses)
            + self.prevRegulCoeff * self.prevRegulCoeff_scale * np.eye(self.numPoses)
            + self.sparseRegulCoeff ** 2 * self.sparseRegulCoeff_scale * self.l1RegulMat
            + self.symmetryRegulCoeff * self.symmetryRegulCoeff_scale * self.symShapeMat
        )
        self.A = self.A.astype(np.float64)

    def set_activePoses(self, activePosesBool):
        self.activePosesBool = activePosesBool

        # 1 - simple approach
        # self.ub *= np.array(self.activePosesBool)

        # 2- less computation way
        self.delta_mat = self.delta_mat_orig[:, self.activePosesBool]
        self.numPoses = self.delta_mat.shape[1]
        self.lb = self.lb_orig[self.activePosesBool]
        self.ub = self.ub_orig[self.activePosesBool]
        self.prevWeights = np.zeros(self.numPoses)

        self.activeIdxMap = []
        cnt = 0
        for idx in range(self.numPoses_orig):
            if self.activePosesBool[idx]:
                self.activeIdxMap.append(cnt)
                cnt += 1
            else:
                self.activeIdxMap.append(-1)

        # update L1 regularization mat
        l1RegulMat = np.ones((1, self.numPoses))
        self.l1RegulMat = np.dot(l1RegulMat.T, l1RegulMat)

        # update cancel pair index
        self.set_cancelPoses(self.cancelPoseIndices)

        # update symmetry pair index
        self.set_symmetryPoses(self.symmetryPoseIndices)  # update self.A here

    def set_cancelPoses(self, cancelPoseIndices):
        self.cancelPoseIndices = cancelPoseIndices
        # filter out cancel shapes
        self.cancelList = []
        maxIdx = np.max(self.cancelPoseIndices)
        if maxIdx < 0:
            return

        for ci in range(maxIdx + 1):
            cancelIndices = np.where(self.cancelPoseIndices == ci)[0]
            if len(cancelIndices) > 2:
                log_warn("There is more than 2 poses for a cancel index %d" % ci)
                break
            elif len(cancelIndices) < 2:
                log_warn("There is less than 2 poses for a cancel index %d" % ci)
                break
            self.cancelList.append(cancelIndices)
        # print ('cancel shape list', self.cancelList)

        activeCancelList = []
        for pIdx1, pIdx2 in self.cancelList:
            if self.activePosesBool[pIdx1] and self.activePosesBool[pIdx2]:
                activeCancelList.append([self.activeIdxMap[pIdx1], self.activeIdxMap[pIdx2]])

        # print (activeCancelList)
        self.cancelList = activeCancelList

    def set_symmetryPoses(self, symmetryPoseIndices):
        self.symmetryPoseIndices = symmetryPoseIndices
        self.symmetryList = []

        maxIdx = np.max(self.symmetryPoseIndices)
        if maxIdx < 0:
            self.symShapeMat = np.zeros((self.numPoses, self.numPoses))
        else:
            for ci in range(maxIdx + 1):
                symmetryIndices = np.where(self.symmetryPoseIndices == ci)[0]
                if len(symmetryIndices) > 2:
                    log_warn("There is more than 2 poses for a cancel index %d" % ci)
                    break
                elif len(symmetryIndices) < 2:
                    log_warn("There is less than 2 poses for a cancel index %d" % ci)
                    break
                self.symmetryList.append(symmetryIndices)

            activeSymmetryList = []
            for pIdx1, pIdx2 in self.symmetryList:
                if self.activePosesBool[pIdx1] and self.activePosesBool[pIdx2]:
                    activeSymmetryList.append([self.activeIdxMap[pIdx1], self.activeIdxMap[pIdx2]])

            self.symmetryList = activeSymmetryList

            symShapeMat = np.zeros((len(self.symmetryList), self.numPoses))
            for si, [pose1Idx, pose2Idx] in enumerate(self.symmetryList):
                symShapeMat[si, pose1Idx] = 1.0
                symShapeMat[si, pose2Idx] = -1.0
            self.symShapeMat = np.dot(symShapeMat.T, symShapeMat)

        self.compute_A_mat()

    def set_l2_regularization(self, L2=3.5):
        self.weightRegulCoeff = L2
        self.compute_A_mat()

    def set_tempo_regularization(self, temporal=3.5):
        self.prevRegulCoeff = temporal
        self.compute_A_mat()

    def set_l1_regularization(self, L1=1.0):
        self.sparseRegulCoeff = L1
        self.compute_A_mat()

    def set_symmetry_regularization(self, value=1.0):
        self.symmetryRegulCoeff = value
        self.compute_A_mat()

    def computeFacsWeights(self, point_mat):
        target_delta_mat = point_mat - self.neutral_mat
        B = (
            np.dot(self.delta_mat.T, target_delta_mat).flatten()
            + self.prevRegulCoeff * self.prevRegulCoeff_scale * self.prevWeights
        )
        B = B.astype(np.float64)

        res = lsq_linear(self.A, B, bounds=(self.lb, self.ub), lsmr_tol="auto", verbose=0, method="bvls")

        # print ('first pass:', res.x)
        if len(self.cancelList) > 0:
            # check cancelling poses -
            ub = self.ub.copy()
            lb = self.lb.copy()

            for pose1Idx, pose2Idx in self.cancelList:
                if res.x[pose1Idx] >= res.x[pose2Idx]:
                    ub[pose2Idx] = 1e-10
                else:
                    ub[pose1Idx] = 1e-10

            res = lsq_linear(self.A, B, bounds=(lb, ub), lsmr_tol="auto", verbose=0, method="bvls")

        self.prevWeights = res.x
        # print ('second pass:', res.x)

        outWeight = np.zeros(self.numPoses_orig)
        outWeight[self.activePosesBool] = res.x

        outWeight = outWeight * (outWeight > 1.0e-9)
        # print (outWeight)

        blend = ["eyeBlinkLeft", "eyeLookDownLeft", "eyeLookInLeft", "eyeLookOutLeft", "eyeLookUpLeft", "eyeSquintLeft", "eyeWideLeft", "eyeBlinkRight", "eyeLookDownRight", "eyeLookInRight", "eyeLookOutRight", "eyeLookUpRight", "eyeSquintRight", "eyeWideRight", "jawForward", "jawLeft", "jawRight", "jawOpen", "mouthClose", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight", "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight", "mouthDimpleLeft", "mouthDimpleRight", "mouthStretchLeft", "mouthStretchRight", "mouthRollLower", "mouthRollUpper", "mouthShrugLower", "mouthShrugUpper", "mouthPressLeft", "mouthPressRight", "mouthLowerDownLeft", "mouthLowerDownRight", "mouthUpperUpLeft", "mouthUpperUpRight", "browDownLeft", "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight", "cheekPuff", "cheekSquintLeft", "cheekSquintRight", "noseSneerLeft", "noseSneerRight", "tongueOut"]

        try:
            client = udp_client.SimpleUDPClient('127.0.0.1', 27008)
            osc_array = outWeight.tolist()
            count = 0

            for i in osc_array:
                client.send_message('/' + str(blend[count]), i)
                count += 1
        except Exception as e:
            log_error(f"Error in OSC communication: {e}")