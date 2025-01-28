# Contains all your FIELD_INSTRUCTIONS and FIELD_GROUPS definitions
# (Keep the existing field definitions as they are, just move them to this file)

FIELD_INSTRUCTIONS = {
    "Legal_Extract_Level": {
        "description": "Level of legal extract",
        "format": "String",
        "datatype": "varchar",
        "max_length": 1
    },
    "Legal_Type": {
        "description": "Specifies the type of legal documentation associated with a property",
        "format": "MP, BMP, SE, RS, PM, SD, SB, DO, MCP, SF, TR",
        "datatype": "String",
        "max_length": 20
    },
    "Map_Book": {
        "description": "Reference book containing the detailed map information for navigation purpose",
        "format": "Integer or alphanumeric optionally including hypens",
        "datatype": "Alphanumeric",
        "max_length": 30
    },
    "Map_Page_From": {
        "description": "Starting page number in map book",
        "format": "Integer",
        "datatype": "String",
        "max_length": 5
    },
    "Map_Page_Thru": {
        "description": "Ending page number in map book",
        "format": "Integer",
        "datatype": "String",
        "max_length": 5
    },
    "Map_Date": {
        "description": "Date of the map",
        "format": "Date",
        "datatype": "String",
        "max_length": 10
    },
    "Map_Name": {
        "description": "Name of the map or subdivision",
        "format": "String",
        "datatype": "varchar",
        "max_length": 254
    },
    "Map_Number": {
        "description": "Number assigned to the map",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 15
    },
    "TractNumber": {
        "description": "Tract identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 4
    },
    "PhaseValue": {
        "description": "Phase of development",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 4
    },
    "CaseNo": {
        "description": "Case number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "Meridian": {
        "description": "Meridian identifier",
        "format": "Alphanumeric",
        "datatype": "varchar",
        "max_length": 30
    },
    "SectionNumber": {
        "description": "Section number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 4
    },
    "Township": {
        "description": "Township identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 10
    },
    "Range": {
        "description": "Range identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 5
    },
    "Government_TractNO": {
        "description": "Government tract number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "Government_LotNO": {
        "description": "Government lot number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 4
    },
    "Areavalue": {
        "description": "Area value",
        "format": "Numeric",
        "datatype": "String",
        "max_length": 20
    },
    "Rack": {
        "description": "Storage rack identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 10
    },
    "Arb_Tract": {
        "description": "Arbitration tract identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 10
    },
    "Plat_Document_Number": {
        "description": "Plat document number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "Lot_Tract_Number": {
        "description": "Lot or tract number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 15
    },
    "APN_Section": {
        "description": "APN section identifier",
        "format": "String",
        "datatype": "varchar",
        "max_length": 20
    },
    "Timeshare_reserve_for_future": {
        "description": "Reserved field for future use",
        "format": "String",
        "datatype": "varchar",
        "max_length": 50
    },
    "Quarters": {
        "description": "Quarter section identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 10
    },
    "Block": {
        "description": "Block identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 10
    },
    "Legal_Extract_Complete_Flag": {
        "description": "Flag indicating complete legal extract",
        "format": "Y/N",
        "datatype": "char",
        "max_length": 1
    },
    "Common_Area_Lot": {
        "description": "Common area lot identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 10
    },
    "LotNumber": {
        "description": "Lot number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 4
    },
    "Building": {
        "description": "Building identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "UnitNumber": {
        "description": "Unit number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 4
    },
    "Share": {
        "description": "Share identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 10
    },
    "Other": {
        "description": "Other information",
        "format": "String",
        "datatype": "varchar",
        "max_length": 100
    },
    "Parking_Space_Garage_Seperately_conveyed": {
        "description": "Separately conveyed parking space",
        "format": "String",
        "datatype": "varchar",
        "max_length": 50
    },
    "Parcel": {
        "description": "Parcel identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "Sub_Parcel": {
        "description": "Sub-parcel identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "Parking_Space_Garage_apartment": {
        "description": "Parking space identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "Fee_Easment": {
        "description": "Fee easement information",
        "format": "String",
        "datatype": "varchar",
        "max_length": 50
    },
    "Condo_Timeshare_Flag": {
        "description": "Condo timeshare flag",
        "format": "C or blank",
        "datatype": "varchar",
        "max_length": 1
    },
    "APN_AIN": {
        "description": "APN/AIN identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 50
    },
    "Arb": {
        "description": "Arbitration identifier",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "Portion": {
        "description": "Portion identifier",
        "format": "Alphanumeric",
        "datatype": "varchar",
        "max_length": 25
    },
    "Filler": {
        "description": "Filler field",
        "format": "String",
        "datatype": "varchar",
        "max_length": 50
    },
    "Condo_Time_Share_Plan_Book": {
        "description": "Condo time share plan book",
        "format": "String",
        "datatype": "varchar",
        "max_length": 20
    },
    "Condo_Time_Share_Plan_Date": {
        "description": "Condo time share plan date",
        "format": "Date",
        "datatype": "String",
        "max_length": 10
    },
    "Condo_Time_Share_Plan_Number": {
        "description": "Condo time share plan number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "Condo_Time_Share_Plan_Page_From": {
        "description": "Starting page of condo time share plan",
        "format": "Integer",
        "datatype": "String",
        "max_length": 5
    },
    "Condo_Time_Share_Plan_Page_Thru": {
        "description": "Ending page of condo time share plan",
        "format": "Integer",
        "datatype": "String",
        "max_length": 5
    },
    "Condo_Timeshare_Parcel_Description_#": {
        "description": "Condo timeshare parcel description number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "Other_Common_Lots": {
        "description": "Other common lots",
        "format": "String",
        "datatype": "varchar",
        "max_length": 100
    },
    "Other_Share_Numbers": {
        "description": "Other share numbers",
        "format": "String",
        "datatype": "varchar",
        "max_length": 100
    },
    "Plant_Name": {
        "description": "Plant name",
        "format": "String",
        "datatype": "varchar",
        "max_length": 100
    },
    "Timeshare_Half_Interest_#": {
        "description": "Timeshare half interest number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "Timeshare_Interval_Number": {
        "description": "Timeshare interval number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "Timeshare_Inventory_Control_Number": {
        "description": "Timeshare inventory control number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "Timeshare_reserve_for_future1": {
        "description": "Reserved field 1 for future use",
        "format": "String",
        "datatype": "varchar",
        "max_length": 50
    },
    "Timeshare_reserve_for_future2": {
        "description": "Reserved field 2 for future use",
        "format": "String",
        "datatype": "varchar",
        "max_length": 50
    },
    "Timeshare_reserve_for_future3": {
        "description": "Reserved field 3 for future use",
        "format": "String",
        "datatype": "varchar",
        "max_length": 50
    },
    "Timeshare_Resort_Estate#": {
        "description": "Timeshare resort estate number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "Timeshare_Unit_Type": {
        "description": "Timeshare unit type",
        "format": "String",
        "datatype": "varchar",
        "max_length": 20
    },
    "Timeshare_Use_Period": {
        "description": "Timeshare use period",
        "format": "String",
        "datatype": "varchar",
        "max_length": 20
    },
    "Timeshare_Use_Week_#": {
        "description": "Timeshare use week number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 10
    },
    "Timeshare_Vacation_Ownership_#": {
        "description": "Timeshare vacation ownership number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    },
    "Timeshare_Vacation_Ownership_Interest_#": {
        "description": "Timeshare vacation ownership interest number",
        "format": "Alphanumeric",
        "datatype": "String",
        "max_length": 20
    }
}

FIELD_GROUPS = list(FIELD_INSTRUCTIONS.keys()) 