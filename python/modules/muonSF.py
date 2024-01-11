###
# Compute muon SFs using correctionlib, and store in new branch.
# Load as
#  muSF = muonSF("POG/MUO/2016postVFP_UL/muon_Z.json.gz")
#  muSF.addCorrection("NUM_TrackerMuons_DEN_genTracks", "2016postVFP_UL", "sf")
#  muSF.addCorrection("NUM_MediumID_DEN_TrackerMuons", "2016postVFP_UL", "systdown", "sfsysdn")
#  muSF.addCorrection("NUM_MediumID_DEN_TrackerMuons", "2016postVFP_UL", "systup", "sfsysup")
###
from __future__ import print_function
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from correctionlib import CorrectionSet

class MuonSF(Module):
    def __init__(self, json, collection="Muon"):
        """Muon SF correction module.
        Parameters:
            json: the correction file
            collection: name of the collection to be corrected
        Use addCorrection() to set which factors should be added.
        """
        self.collection = collection
        self.names = [ ]
        self.scenarios = [ ]
        self.valtypes = [ ]
        self.varnames = [ ]
        self.evaluators = [ ]
        self.evaluator = CorrectionSet.from_file(json)
    
    def addCorrection(self, name, scenario, valtype, varname=None):
        """
        Call this method to add a correction factor.
        Parameters:
            name: name of the corrections, e.g. 'NUM_TrackerMuons_DEN_genTracks'
            scenario: year/scenario, e.g. '2016postVFP_UL'
            valtype: type of factor, e.g. 'sf', 'systup', ...
            varname: branch name suffix (defaults to valtype)
        """
        if varname==None: # default suffix
          varname = valtype
        self.names.append(name)
        self.scenarios.append(scenario)
        self.valtypes.append(valtype)
        self.varnames.append(f"{self.collection}_{varname}") # branch name
        self.evaluators.append(self.evaluator[name])
    
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        """Add branch for every correction to output file."""
        self.out = wrappedOutputTree        
        for varname in self.varnames:
            self.out.branch(varname, 'F', lenVar='nMuon')
    
    def analyze(self, event):
        pts  = [max(15.001,event.Muon_pt[i]) for i in range(event.nMuon)]
        etas = [min(2.39999,abs(event.Muon_eta[i])) for i in range(event.nMuon)]
        for ic in range(len(self.evaluators)):
            # We cannot make a single call to evaluate passing eta, pt as arrays
            # since POG JSONS are currently provided with flow="error", so we
            # have to loop to protect for values out of binning range.
            sfs = [1.]*event.nMuon
            for iMu in range(event.nMuon):
                try:
                    sfs[iMu] = self.evaluators[ic].evaluate(self.scenarios[ic], etas[iMu], pts[iMu], self.valtypes[ic])
                except:
                    print(f"MuonSF.analyze: Exception for {self.scenarios[ic]}, eta={etas[iMu]:6.4f}, pt={pts[iMu]:6.4f}, {self.valtypes[ic]}")
                    pass # default sf = 1
            self.out.fillBranch(self.varnames[ic], sfs)
        return True
    
