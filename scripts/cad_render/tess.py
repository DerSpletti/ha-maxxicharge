import sys, json, numpy as np
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFApp import XCAFApp_Application
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorGen, XCAFDoc_ColorSurf
from OCP.collections import Sequence_TDF_Label as TDF_LabelSequence
from OCP.Quantity import Quantity_Color
from OCP.IFSelect import IFSelect_RetDone
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_SOLID, TopAbs_REVERSED
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
inp,out,defl=sys.argv[1],sys.argv[2],float(sys.argv[3])
app=XCAFApp_Application.GetApplication_s()
doc=TDocStd_Document(TCollection_ExtendedString("d")); app.NewDocument(TCollection_ExtendedString("MDTV-XCAF"),doc)
r=STEPCAFControl_Reader(); r.SetColorMode(True)
assert r.ReadFile(inp)==IFSelect_RetDone; r.Transfer(doc)
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); ct=XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
fs=TDF_LabelSequence(); st.GetFreeShapes(fs)
shapes=[st.GetShape_s(fs.Value(i)) for i in range(1,fs.Length()+1)]
print("free shapes",len(shapes),flush=True)
BRepMesh_IncrementalMesh(shapes[0],defl,False,0.5,True)
res=[]; 
def col(s):
    c=Quantity_Color()
    for t in (XCAFDoc_ColorSurf,XCAFDoc_ColorGen):
        if ct.GetColor(s,t,c): return [round(c.Red(),3),round(c.Green(),3),round(c.Blue(),3)]
    return None
ex=TopExp_Explorer(shapes[0],TopAbs_SOLID); n=0
while ex.More():
    sol=ex.Current(); sc=col(sol); P=[];I=[];off=0
    fe=TopExp_Explorer(sol,TopAbs_FACE)
    while fe.More():
        f=TopoDS.Face(fe.Current()); loc=TopLoc_Location()
        t=BRep_Tool.Triangulation_s(f,loc)
        if t is not None:
            tr=loc.Transformation(); rev=f.Orientation()==TopAbs_REVERSED
            for k in range(1,t.NbNodes()+1):
                p=t.Node(k).Transformed(tr); P+= [p.X(),p.Y(),p.Z()]
            for k in range(1,t.NbTriangles()+1):
                a,b,c=t.Triangle(k).Get(); a+=off-1;b+=off-1;c+=off-1
                I+= [a,c,b] if rev else [a,b,c]
            off+=t.NbNodes()
        fe.Next()
    if I: res.append({"p":[round(x,2) for x in P],"i":I,"c":sc})
    n+=1; ex.Next()
tri=sum(len(m["i"])//3 for m in res)
allp=np.concatenate([np.array(m["p"]).reshape(-1,3) for m in res])
print("solids",n,"meshes",len(res),"tris",tri,"bbox",(allp.max(0)-allp.min(0)).round(0),flush=True)
json.dump(res,open(out,"w"))
