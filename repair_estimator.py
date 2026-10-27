"""
CivicLens AI - Municipal Repair Cost & Timeline Estimator
Provides realistic civil maintenance benchmarks (based on CPWD / Municipal standard schedule of rates).
Translates AI-detected obstacles into actionable repair budgets, timelines, and equipment requirements.
"""

from typing import Dict, Any

# Standard Municipal Repair Benchmarks
REPAIR_BENCHMARKS = {
    "open_drainage_pothole": {
        "title_en": "Pothole Patching & Drain Cover Replacement",
        "title_hi": "सड़क का गड्ढा भरना और नाली का ढक्कन लगाना",
        "cost_inr": "₹3,500 – ₹7,000",
        "cost_usd": "$42 – $85",
        "sla_hours": 24,
        "materials_en": ["Cold mix asphalt / Ready-mix concrete", "Heavy-duty cast iron or SFRC cover", "Reflective safety barricades"],
        "materials_hi": ["कोल्ड मिक्स डामर या कंक्रीट", "मजबूत लोहे या सीमेंट का ढक्कन", "चमकने वाला लाल सुरक्षा बैरिकेड"],
        "crew": "PWD Road Maintenance Crew (सड़क मरम्मत दल)",
        "action_en": "Seal cavity with compacted bituminous mixture, install flush drain slab, and secure with reflective caution tape.",
        "action_hi": "गड्ढे को डामर व गिट्टी से दबाकर भरें, नाली पर मजबूत ढक्कन लगाएं और चेतावनी पट्टी लगाएं।"
    },
    "broken_footpath": {
        "title_en": "Sidewalk Paver Repair & Leveling",
        "title_hi": "टूटे फुटपाथ की मरम्मत और टाइल्स लगाना",
        "cost_inr": "₹4,000 – ₹9,500",
        "cost_usd": "$48 – $115",
        "sla_hours": 48,
        "materials_en": ["Interlocking concrete pavers (60mm)", "Coarse bedding sand", "Cement mortar edging"],
        "materials_hi": ["मजबूत इंटरलॉकिंग टाइल्स (पेवर ब्लॉक)", "रेत व सीमेंट का मसाला", "किनारे की पक्की बाउंड्री"],
        "crew": "Municipal Civil Engineering Division (नगर निगम निर्माण शाखा)",
        "action_en": "Excavate fractured surface, lay leveled sand bed, install anti-skid interlocking pavers flush with curb.",
        "action_hi": "टूटा हुआ पत्थर हटाकर जमीन समतल करें, नई फिसलन-मुक्त टाइल्स लगाएं ताकि कोई ठोकर न खाए।"
    },
    "missing_ramp": {
        "title_en": "Accessible Curb Ramp Construction (1:12 Gradient)",
        "title_hi": "व्हीलचेयर व बुजुर्गों के लिए ढलानदार रैंप का निर्माण",
        "cost_inr": "₹6,000 – ₹12,000",
        "cost_usd": "$72 – $145",
        "sla_hours": 72,
        "materials_en": ["M20 grade concrete", "Yellow tactile hazard warning pavers", "Flared curb transition stones"],
        "materials_hi": ["पक्का कंक्रीट मसाला", "पीली उभरी हुई चेतावनी टाइल्स (दृष्टिबाधितों हेतु)", "सपाट ढलानदार पत्थर"],
        "crew": "Accessibility Infrastructure Team (सुगम्य भारत अभियान दल)",
        "action_en": "Construct ADA/CPWD compliant 1:12 slope ramp with yellow tactile warning surface for white cane users.",
        "action_hi": "सड़क और फुटपाथ के बीच ढलान बनाएं और पीली स्पर्श टाइल लगाएं ताकि व्हीलचेयर और दृष्टिबाधित आसानी से चढ़ सकें।"
    },
    "standing_water": {
        "title_en": "Stormwater Drainage De-clogging & Regrading",
        "title_hi": "जलभराव निकासी और नाली की सफाई",
        "cost_inr": "₹2,500 – ₹5,000",
        "cost_usd": "$30 – $60",
        "sla_hours": 24,
        "materials_en": ["Suction pump machinery", "Drain jetting hose", "Micro-drainage channel pipe"],
        "materials_hi": ["पानी निकालने वाला सक्शन पंप", "नाली सफाई जेट मशीन", "पानी निकासी का छोटा पाइप"],
        "crew": "Drainage & Sewerage Board (जल एवं सीवर बोर्ड)",
        "action_en": "Pump out accumulated water, clear clogged storm inlets, and install surface runoff grade slope.",
        "action_hi": "जमा पानी को पंप से निकालें, बंद नाली को तुरंत खोलें ताकि मच्छर और फिसलन न हो।"
    },
    "encroachment_obstacle": {
        "title_en": "Footpath Obstacle Removal & Clearance Notice",
        "title_hi": "फुटपाथ से अतिक्रमण व रुकावट हटाना",
        "cost_inr": "₹1,500 – ₹3,500",
        "cost_usd": "$18 – $42",
        "sla_hours": 12,
        "materials_en": ["Municipal towing/crane vehicle", "Clearance notice sticker", "Protective pedestrian bollards"],
        "materials_hi": ["क्रेन / नगर निगम जब्ती वाहन", "अतिक्रमण हटाने का नोटिस", "पैदल यात्रियों की सुरक्षा हेतु लोहे के खंभे (Bollards)"],
        "crew": "Encroachment Removal Cell (अतिक्रमण निरोधक दस्ता)",
        "action_en": "Issue immediate clearance order, confiscate unattended blocking debris/vehicles, and install walking bollards.",
        "action_hi": "रास्ते को तुरंत खाली कराएं, सामान या वाहन हटवाएं और पैदल चलने का 1.8 मीटर चौड़ा रास्ता बहाल करें।"
    },
    "damaged_walking_surface": {
        "title_en": "Tactile Surface Resurfacing & Re-grouting",
        "title_hi": "चलने की सतह की री-सर्फेसिंग और मरम्मत",
        "cost_inr": "₹3,000 – ₹6,500",
        "cost_usd": "$36 – $78",
        "sla_hours": 48,
        "materials_en": ["Epoxy grout", "Non-slip abrasive surfacing coat", "Replacement tactile studs"],
        "materials_hi": ["मजबूत सीमेंट व चिपकाने वाला घोल", "फिसलन रोकने वाला लेप", "नई दृष्टिबाधित चेतावनी टाइल"],
        "crew": "Zonal PWD Maintenance Depot (जोनल सड़क रखरखाव डिपो)",
        "action_en": "Re-grout loose cobblestones, replace broken tactile studs, and coat with non-skid walking finish.",
        "action_hi": "उखड़े हुए पत्थरों को मजबूत जोड़ से चिपकाएं और सतह को समतल बनाएं।"
    },
    "waste_overflow": {
        "title_en": "Garbage Heap Clearance & Sanitization",
        "title_hi": "कचरा ढेर की सफाई और कीटाणुनाशन",
        "cost_inr": "₹1,200 – ₹2,800",
        "cost_usd": "$15 – $34",
        "sla_hours": 12,
        "materials_en": ["Compactor garbage truck", "Disinfectant lime powder / spray", "Covered community waste bin"],
        "materials_hi": ["कचरा उठाने वाली गाड़ी", "कीटाणुनाशक चूना पाउडर", "ढक्कन वाला नया डस्टबिन"],
        "crew": "Municipal Sanitation Department (नगर निगम स्वच्छता विभाग)",
        "action_en": "Deploy mechanical loader to clear dumped waste, disinfect ground with lime, and place designated bin.",
        "action_hi": "कचरा तुरंत उठवाएं, जमीन पर दवाई छिड़कें और वहां डस्टबिन लगवाएं।"
    },
    "vegetation_overgrowth": {
        "title_en": "Overhanging Branch Pruning & Hedge Trimming",
        "title_hi": "लटकती डालियों की छंटाई और रास्ता साफ करना",
        "cost_inr": "₹1,000 – ₹2,200",
        "cost_usd": "$12 – $26",
        "sla_hours": 24,
        "materials_en": ["Pole tree pruner / chainsaw", "Waste chipper", "Minimum 2.1m vertical clearance tape"],
        "materials_hi": ["डालियां काटने की मशीन", "सफाई गाड़ी", "रास्ते की ऊंचाई मापने का फीता"],
        "crew": "Horticulture Department (उद्यान / बागवानी विभाग)",
        "action_en": "Prune all branches hanging below 2.1 meters height to clear headroom for pedestrians and white canes.",
        "action_hi": "सिर से टकराने वाली झुकी डालियों को कटवाएं ताकि कम से कम 7 फीट तक का रास्ता बिल्कुल साफ रहे।"
    },
}

DEFAULT_BENCHMARK = {
    "title_en": "General Civic Surface Maintenance",
    "title_hi": "सामान्य सड़क व फुटपाथ रखरखाव",
    "cost_inr": "₹2,000 – ₹5,000",
    "cost_usd": "$25 – $60",
    "sla_hours": 48,
    "materials_en": ["Standard repair toolkit", "Warning caution tape"],
    "materials_hi": ["मरम्मत किट", "सुरक्षा चेतावनी पट्टी"],
    "crew": "Local Ward Engineering Office (वार्ड इंजीनियरिंग कार्यालय)",
    "action_en": "Inspect ground condition and perform routine leveling and barrier removal.",
    "action_hi": "मौके पर जाकर मुआयना करें और रास्ते की रुकावट को ठीक करें।"
}


def get_repair_estimate(issue_type: str, priority_tier: str = "HIGH", lang: str = "en") -> Dict[str, Any]:
    """
    Returns estimated municipal repair budget, resolution SLA, materials, and crew for a given issue.
    """
    data = REPAIR_BENCHMARKS.get(issue_type, DEFAULT_BENCHMARK)
    
    # Adjust SLA based on priority tier
    tier_upper = (priority_tier or "HIGH").upper()
    sla_hours = data["sla_hours"]
    if tier_upper == "CRITICAL":
        sla_hours = min(24, sla_hours)
    elif tier_upper == "MEDIUM":
        sla_hours = sla_hours * 2
    elif tier_upper == "LOW":
        sla_hours = sla_hours * 3

    if lang == "hi":
        return {
            "title": data["title_hi"],
            "cost": data["cost_inr"],
            "sla": f"{sla_hours} घंटे के अंदर (नागरिक चार्टर SLA)",
            "materials": data["materials_hi"],
            "crew": data["crew"],
            "action": data["action_hi"]
        }
    else:
        return {
            "title": data["title_en"],
            "cost": f"{data['cost_inr']} ({data['cost_usd']})",
            "sla": f"Within {sla_hours} Hours (Citizens Charter SLA)",
            "materials": data["materials_en"],
            "crew": data["crew"],
            "action": data["action_en"]
        }
