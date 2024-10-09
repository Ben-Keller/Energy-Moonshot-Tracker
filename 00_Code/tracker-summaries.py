import pandas as pd

directConversion=pd.read_csv("../01_Input/01_Methodology/Direct Conversion Factors.csv")


beneTiers={}
for index,row in directConversion.iterrows():
    if row["Tier"] not in beneTiers:
        beneTiers[row["Tier"]]=[]
    beneTiers[row["Tier"]].append(row["Beneficiary Category"])


summaryDfList=[]

def getBeneSums(row,df):

    row["Direct Beneficiaries"]=df["Direct Beneficiaries"].sum()
    row["Energy Access"]=df[df["Beneficiary Category"].isin(["Electricity Access","Energy (MW added)"])]["Direct Beneficiaries"].sum()
    row["Productive Use"]=df[df["Beneficiary Category"].isin(["Health Services","Water Services","Agricultural Services","Education Services"])]["Direct Beneficiaries"].sum()
    
    dfNoDuplicates=df.drop_duplicates(subset='Project ID') ##
    row["Budget Sum (M USD)"]=dfNoDuplicates["Budget"].sum()
    
    #row["Indirect Beneficiaries"]=df["Indirect Beneficiaries"].sum()
    
    #row["Energy Saved (MJ)"]=df["Energy Saved (MJ)"].sum()

    return row


def getProjectCounts(row,df):
    projectIds=df["Project ID"].unique().tolist()
    row["Project Count"]=len(projectIds)    
    return row

def getCountryCounts(row,df):
    countryCodes=df["Country Code"].unique().tolist()
    row["Country Count"]=len(countryCodes)    
    return row
    
    
def getSummaryInfo(row,df):
    row=getBeneSums(row,df)
    row=getProjectCounts(row,df)
    row=getCountryCounts(row,df)
    return row
    
    
#outputDfComplete=outputDfComplete[outputDfComplete["Region"]=="RBLAC"]
    
for projectType in ["Total","VF","Non-VF"]:
    
    if projectType=="Total":
        outputDfFiltered=outputDfComplete
    else:
        outputDfFiltered=outputDfComplete[outputDfComplete["VF or Non-VF"]==projectType]
    
    ##first add values for unfiltered 
    summaryDfList.append(getSummaryInfo({"Category":"All","Subcategory":"All","VF or Non-VF":projectType},outputDfFiltered))

    for grouping in ["SIDS","LDC","LLDC"]:
        summaryDfList.append(getSummaryInfo({"Category":"Grouping","Subcategory":grouping,"VF or Non-VF":projectType},outputDfFiltered[outputDfFiltered[grouping]==grouping]))

    for economy in outputDfFiltered["Economy"].dropna().unique().tolist():
        summaryDfList.append(getSummaryInfo({"Category":"Economy","Subcategory":economy,"VF or Non-VF":projectType},outputDfFiltered[outputDfFiltered["Economy"]==economy]))

    for hdi in outputDfFiltered["HDI"].dropna().unique().tolist():
        summaryDfList.append(getSummaryInfo({"Category":"HDI","Subcategory":hdi,"VF or Non-VF":projectType},outputDfFiltered[outputDfFiltered["HDI"]==hdi]))

    for region in outputDfFiltered["Region"].dropna().unique().tolist():
        summaryDfList.append(getSummaryInfo({"Category":"Region","Subcategory":region,"VF or Non-VF":projectType},outputDfFiltered[outputDfFiltered["Region"]==region]))

    #for donorCategory in ["Government","UN Agencies","Other","UN Pooled Funds","European Union","DFI","Private Sector"]:

    for beneTier in beneTiers:
        summaryDfList.append(getSummaryInfo({"Category":"Beneficiary Tier","Subcategory":beneTier,"VF or Non-VF":projectType},outputDfFiltered[outputDfFiltered["Beneficiary Category"].isin(beneTiers[beneTier])]))

    for beneCategory in outputDfFiltered["Beneficiary Category"].dropna().unique().tolist():
        df=outputDfFiltered[outputDfFiltered["Beneficiary Category"]==beneCategory]
#         if beneCategory=="Policy or Regulatory Framework":
#             for taxonomy in outputDfFiltered["Policy-taxonomy"].dropna().unique().tolist():     
#                 summaryDfList.append(getSummaryInfo({"Category":"Beneficiary Category","Subcategory":"Policy - "+taxonomy,"VF or Non-VF":projectType},df[df["Policy-taxonomy"]==taxonomy]))
#         else:
        summaryDfList.append(getSummaryInfo({"Category":"Beneficiary Category","Subcategory":beneCategory,"VF or Non-VF":projectType},df))

summaryDf=pd.DataFrame.from_records(summaryDfList)
summaryDf.to_csv("../02_Output/05_Summary/summaryDf.csv")
summaryDf
