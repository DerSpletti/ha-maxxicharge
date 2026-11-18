import sys,re
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFApp import XCAFApp_Application
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.collections import Sequence_TDF_Label as Seq
from OCP.TDF import TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from OCP.TopoDS import TopoDS
app=XCAFApp_Application.GetApplication_s()
doc=TDocStd_Document(TCollection_ExtendedString("d")); app.NewDocument(TCollection_ExtendedString("MDTV-XCAF"),doc)
r=STEPCAFControl_Reader(); r.ReadFile(sys.argv[1]); r.Transfer(doc)
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
fs=Seq(); st.GetFreeShapes(fs); top=st.GetShape_s(fs.Value(1))
pat=re.compile(sys.argv[2],re.I)
ex=TopExp_Explorer(top,TopAbs_SOLID); n=0
while ex.More():
    sol=ex.Current(); lab=TDF_Label()
    ok=st.Search(sol,lab,True,True,True) if hasattr(st,'Search') else False
    name='?'
    if ok:
        a=TDataStd_Name()
        if lab.FindAttribute(TDataStd_Name.GetID_s(),a): name=a.Get().ToExtString()
    bx=Bnd_Box(); BRepBndLib.Add_s(sol,bx); b=(bx.CornerMin().X(),bx.CornerMin().Y(),bx.CornerMin().Z(),bx.CornerMax().X(),bx.CornerMax().Y(),bx.CornerMax().Z())
    if pat.search(name): print(name,[round(v) for v in b],flush=True)
    n+=1; ex.Next()
print("solids",n)
