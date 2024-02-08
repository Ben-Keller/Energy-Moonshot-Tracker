moonshotDashboardJson={
    "text":{
        "header":"The <b>UNDP Energy Moonshot</b> endeavors to catalyse unprecedented actions and partnerships to support provision of access to <b>sustainable, affordable, and reliable energy</b> to <b>500 million more people by 2025</b> and <b>accelerate the transition to renewable energy</b> through systemic changes that lead to inclusive green economies.",
        "opening":"Select output categories and filters to analyze the <b>UNDP energy portfolio</b> during the period of the <b>Strategic Plan 2022-2025</b>:"
    },
    "categories":[
        {
            "outputCategory":"All" ## note that "All" needs to remove filter by category
        },
        {
            "outputCategory":"Energy Access",
            "outputSubcategories":[
                {
                    "outputSubcategory":"Clean Electricity",
                    "outputSubSubcategories":[
                        "All", ##All
                        "Solar",
                        "Wind",
                        "Geothermal",
                        "Biomass"],
                    "displayText":"Clean Electricity"
                },
                {
                    "outputSubcategory":"Clean Cooking",
                    "displayText":"Clean Cooking"
                }
                
            ]
        },
        {
            "outputCategory":"Energy Transition",
            "outputSubcategories":[
                {
                    "outputSubcategory":"Energy Transition",###just to keep same structure as above, this row should be hidden
                    "outputSubSubcategories":[
                        "All", ##All
                        "Solar",
                        "Wind",
                        "Geothermal",
                        "Biomass"],
                    "displayText":"Clean Cooking"
                }
                
            ]
        },
        {
            "outputCategory":"Productive Use",
            "outputSubcategories":[
                {
                    "outputSubcategory":"All", ##All
                    "displayText":"All"
                },
                {
                    "outputSubcategory":"Health Services",
                    "displayText":"Health"
                },
                {
                    "outputSubcategory":"Education Services",
                    "displayText":"Education"
                },
                {
                    "outputSubcategory":"Agriculture and Food Systems",
                    "displayText":"Agriculture"
                },
                {
                    "outputSubcategory":"Water Services",
                    "displayText":"Water"
                }
                
            ]
        }
    ],
    "filters":[
        {
            "filterId":"countryGroupings",
            "categories":[
                {
                    "category":"All Country Groupings", ##All
                    "dataKey":"None"
                },
                {
                    "category":"Regional Bureaus",
                    "dataKey":"region",
                    "subcategories":[
                        "RBLAC",
                        "RBA",
                        "RBAP",
                        "RBEC",
                        "RBAS"
                    ]
                },
                {
                    "category":"Income Groups",
                    "dataKey":"incomeGrouping",
                    "subcategories":[
                        "High income",
                        "Upper middle income",
                        "Lower middle income",
                        "Low income"
                    ]
                },
                {
                    "category":"HDI Tiers",
                    "dataKey":"hdiTier",
                    "subcategories":[
                        "Very High",
                        "High",
                        "Medium",
                        "Low"
                    ]
                },
                {
                    "category":"Special Groupings",
                    "dataKey":"specialGroupings",
                    "subcategories":[
                        "SIDS",
                        "LLDCs",
                        "LDCs"
                    ]
                }
            ]
        },
        {
            "filterId":"taxonomies",
            "categories":[
                {
                    "category":"All Taxonomies", ##All
                    "dataKey":"None"
                },
                {
                    "category":"UNDP Flagships",
                    "dataKey":"flagship",
                    "subcategories":[
                        "All", ##All
                        "AMP",
                        "Solar for Health",
                        "PUDC",
                        "Action Opportunities"
                    ]
                },
                {
                    "category":"Thematics",
                    "dataKey":"thematic",
                    "subcategories":[
                        "Energy Finance",
                        "Gender Equality",
                        "Energy Governance"
                    ]
                }
            ]
        },
                {
            "filterId":"fundingSources",
            "categories":[
                {
                    "category":"Funding Sources",
                    "dataKey":"fundingSources",
                    "subcategories":[
                        "All Funding Sources", ##All
                        "VF",
                        "Non-VF"
                    ]
                }
            ]
        }
        
    ],
    "indicators":[
        {
            "indicator": "Direct Beneficiaries", 
            "indicatorDescription": "The total number of people directly benefiting",
            "dataKey": "outputValue",
            "binningRangeLarge": [100, 500, 1000, 10000, 50000, 100000, 1000000],
            "aggregationLevel":"outputs"

        },
        {
            "indicator": "Project Budget Totals", 
            "indicatorDescription": "Project Budget Totals (US)",
            "dataKey": "budget",
            "binningRangeLarge": [100, 500, 1000, 10000, 50000, 100000, 1000000],
            "aggregationLevel":"projects"

        },
        {
            "indicator": "Energy Saved (MJ)", 
            "indicatorDescription": "Energy Saved (MJ)",
            "dataKey": "energySaved",
            "binningRangeLarge": [100, 500, 1000, 10000, 50000, 100000, 1000000],
            "aggregationLevel":"projects"

        },
        {
            "indicator": "GHG Emissions Reduction", 
            "indicatorDescription": "GHG Emissions Reduction (tonnes CO2)",
            "dataKey": "ghgReduction",
            "binningRangeLarge": [100, 500, 1000, 10000, 50000, 100000, 1000000],
            "aggregationLevel":"projects"
        },
        {
            "indicator": "Number of Projects", 
            "indicatorDescription": "Number or Projects",
            "dataKey": "None",
            "binningRangeLarge": [100, 500, 1000, 10000, 50000, 100000, 1000000],
            "aggregationLevel":"projects"
        }
    ]
}

moonshotProjectsJson=[
    {
        "projectId": "4018",
        "countryCode":"IRN",
        "projectTitle": "Energy Efficient Buildings",
        "link":"......",
        "budget": 4000000,
        "energySaved":1234,
        "ghgReduction":123456
    },
    ...
]


moonshotOutputsJson=[
    {
        "projectId":"1234",
        "outputCategory":"Electricity Access",
        "outputSubcategory":"Clean Electricity",
        "technology":"Solar",
        "directBeneficiaries":123456,
        "fundingSource":"VF",
        "region":"RBLAC",
        "thematic":"Energy Governance",
        "flagship":"None",
        "hdiTier":"Low",
        "incomeGroup":"Low",
        "specialGroupings":"SIDS",
        "percentFemale":50      
    },
    ...
]
