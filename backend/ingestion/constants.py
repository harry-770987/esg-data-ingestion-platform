# Column Aliases / Inconsistent Header Mappings for Ingestion
# Allows the parser to find the correct column even if names differ across client systems.
COLUMN_ALIASES = {
    # Transaction Date Aliases
    'transaction_date': [
        'transaction_date', 'date', 'postingdate', 'posting_date', 
        'billingperiodend', 'billing_period_end', 'traveldate', 'travel_date'
    ],
    # Activity Type Aliases (e.g. Fuel Type, Transportation mode, or generic activity name)
    'activity_type': [
        'activity_type', 'fueltype', 'fuel_type', 'transporttype', 
        'transport_type', 'traveltype', 'travel_type', 'activity'
    ],
    # Quantity Aliases
    'quantity': [
        'quantity', 'qty', 'usagequantity', 'usage_quantity', 
        'consumption', 'usage', 'distance'
    ],
    # Unit Aliases
    'unit': [
        'unit', 'usageunit', 'usage_unit', 'distanceunit', 'distance_unit'
    ]
}

# Unit Conversion Mappings
# Structure: (from_unit, to_unit) -> conversion_factor
# Target standardized units: Liters ('L') for Fuel, Kilowatt-hours ('kWh') for Electricity, Kilometers ('km') for Travel.
UNIT_CONVERSION_FACTORS = {
    # Fuel conversions (Target: Liters 'L')
    ('gallons', 'L'): 3.78541,
    ('gallon', 'L'): 3.78541,
    ('gal', 'L'): 3.78541,
    ('liters', 'L'): 1.0,
    ('liter', 'L'): 1.0,
    ('l', 'L'): 1.0,
    
    # Electricity conversions (Target: Kilowatt-hours 'kWh')
    ('mwh', 'kWh'): 1000.0,
    ('megawatt_hour', 'kWh'): 1000.0,
    ('kwh', 'kWh'): 1.0,
    ('kilowatt_hour', 'kWh'): 1.0,
    
    # Travel conversions (Target: Kilometers 'km')
    ('miles', 'km'): 1.60934,
    ('mile', 'km'): 1.60934,
    ('mi', 'km'): 1.60934,
    ('km', 'km'): 1.0,
    ('kilometers', 'km'): 1.0,
    ('kilometer', 'km'): 1.0
}

# Source Type Mappings (Source Type -> (Category, Scope, Standard Unit))
SOURCE_TYPE_METADATA = {
    'SAP_FUEL': {
        'category': 'SCOPE_1_FUEL',
        'scope': 1,
        'standard_unit': 'L'
    },
    'UTILITY_ELEC': {
        'category': 'SCOPE_2_ELEC',
        'scope': 2,
        'standard_unit': 'kWh'
    },
    'TRAVEL_CORP': {
        'category': 'SCOPE_3_TRAVEL',
        'scope': 3,
        'standard_unit': 'km'
    }
}
