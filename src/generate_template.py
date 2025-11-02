#!/usr/bin/env python3
"""
Generate Garmin Fitness Tracking Excel Template
This creates a template with UUIDs for the EAV metadata system
"""
import pandas as pd
import uuid
from pathlib import Path

def generate_template():
    """Generate complete Garmin fitness tracking template with UUIDs."""
    
    # Areas - Top level categories
    areas_data = [
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Health',
            'icon': '🏥',
            'color': '#4CAF50',
            'sort_order': 1,
            'description': 'Daily health metrics and wellness tracking'
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Training',
            'icon': '💪',
            'color': '#2196F3',
            'sort_order': 2,
            'description': 'Workout activities and training sessions'
        }
    ]
    
    # Categories - Hierarchical structure
    health_uuid = areas_data[0]['uuid']
    training_uuid = areas_data[1]['uuid']
    
    categories_data = [
        # Health categories
        {
            'uuid': str(uuid.uuid4()),
            'area_uuid': health_uuid,
            'parent_uuid': None,
            'name': 'Sleep',
            'description': 'Sleep tracking and analysis',
            'level': 1,
            'sort_order': 1
        },
        {
            'uuid': str(uuid.uuid4()),
            'area_uuid': health_uuid,
            'parent_uuid': None,
            'name': 'Daily Wellness',
            'description': 'Daily health metrics',
            'level': 1,
            'sort_order': 2
        },
        # Training categories
        {
            'uuid': str(uuid.uuid4()),
            'area_uuid': training_uuid,
            'parent_uuid': None,
            'name': 'Cardio',
            'description': 'Cardiovascular training',
            'level': 1,
            'sort_order': 1
        },
        {
            'uuid': str(uuid.uuid4()),
            'area_uuid': training_uuid,
            'parent_uuid': None,
            'name': 'Strength',
            'description': 'Resistance training',
            'level': 1,
            'sort_order': 2
        }
    ]
    
    # Store category UUIDs for attributes
    sleep_uuid = categories_data[0]['uuid']
    wellness_uuid = categories_data[1]['uuid']
    cardio_uuid = categories_data[2]['uuid']
    strength_uuid = categories_data[3]['uuid']
    
    # Add subcategory example under Strength
    upper_body_uuid = str(uuid.uuid4())
    categories_data.append({
        'uuid': upper_body_uuid,
        'area_uuid': training_uuid,
        'parent_uuid': strength_uuid,
        'name': 'Upper Body',
        'description': 'Upper body strength exercises',
        'level': 2,
        'sort_order': 1
    })
    
    # Attributes - Define what data can be captured
    attributes_data = [
        # Sleep attributes
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': sleep_uuid,
            'name': 'Total Sleep',
            'data_type': 'number',
            'unit': 'hours',
            'is_required': True,
            'default_value': None,
            'validation_rules': '{"min": 0, "max": 24}',
            'sort_order': 1
        },
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': sleep_uuid,
            'name': 'Deep Sleep',
            'data_type': 'number',
            'unit': 'hours',
            'is_required': False,
            'default_value': None,
            'validation_rules': '{"min": 0, "max": 12}',
            'sort_order': 2
        },
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': sleep_uuid,
            'name': 'Sleep Quality',
            'data_type': 'number',
            'unit': 'score',
            'is_required': False,
            'default_value': None,
            'validation_rules': '{"min": 0, "max": 100}',
            'sort_order': 3
        },
        # Daily Wellness attributes
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': wellness_uuid,
            'name': 'Steps',
            'data_type': 'number',
            'unit': 'steps',
            'is_required': False,
            'default_value': None,
            'validation_rules': '{"min": 0, "max": 100000}',
            'sort_order': 1
        },
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': wellness_uuid,
            'name': 'Resting HR',
            'data_type': 'number',
            'unit': 'bpm',
            'is_required': False,
            'default_value': None,
            'validation_rules': '{"min": 30, "max": 120}',
            'sort_order': 2
        },
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': wellness_uuid,
            'name': 'HRV',
            'data_type': 'number',
            'unit': 'ms',
            'is_required': False,
            'default_value': None,
            'validation_rules': '{"min": 0, "max": 200}',
            'sort_order': 3
        },
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': wellness_uuid,
            'name': 'Body Battery',
            'data_type': 'number',
            'unit': 'score',
            'is_required': False,
            'default_value': None,
            'validation_rules': '{"min": 0, "max": 100}',
            'sort_order': 4
        },
        # Cardio attributes
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': cardio_uuid,
            'name': 'Duration',
            'data_type': 'number',
            'unit': 'minutes',
            'is_required': True,
            'default_value': None,
            'validation_rules': '{"min": 1, "max": 600}',
            'sort_order': 1
        },
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': cardio_uuid,
            'name': 'Distance',
            'data_type': 'number',
            'unit': 'km',
            'is_required': False,
            'default_value': None,
            'validation_rules': '{"min": 0, "max": 200}',
            'sort_order': 2
        },
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': cardio_uuid,
            'name': 'Avg Heart Rate',
            'data_type': 'number',
            'unit': 'bpm',
            'is_required': False,
            'default_value': None,
            'validation_rules': '{"min": 40, "max": 220}',
            'sort_order': 3
        },
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': cardio_uuid,
            'name': 'Calories',
            'data_type': 'number',
            'unit': 'kcal',
            'is_required': False,
            'default_value': None,
            'validation_rules': '{"min": 0, "max": 5000}',
            'sort_order': 4
        },
        # Strength attributes
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': strength_uuid,
            'name': 'Duration',
            'data_type': 'number',
            'unit': 'minutes',
            'is_required': True,
            'default_value': None,
            'validation_rules': '{"min": 1, "max": 180}',
            'sort_order': 1
        },
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': strength_uuid,
            'name': 'Exercises',
            'data_type': 'text',
            'unit': None,
            'is_required': False,
            'default_value': None,
            'validation_rules': '{}',
            'sort_order': 2
        },
        # Upper Body specific attributes
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': upper_body_uuid,
            'name': 'Bench Press Weight',
            'data_type': 'number',
            'unit': 'kg',
            'is_required': False,
            'default_value': None,
            'validation_rules': '{"min": 0, "max": 300}',
            'sort_order': 1
        },
        {
            'uuid': str(uuid.uuid4()),
            'category_uuid': upper_body_uuid,
            'name': 'Reps',
            'data_type': 'number',
            'unit': 'count',
            'is_required': False,
            'default_value': None,
            'validation_rules': '{"min": 1, "max": 100}',
            'sort_order': 2
        }
    ]
    
    # Create DataFrames
    df_areas = pd.DataFrame(areas_data)
    df_categories = pd.DataFrame(categories_data)
    df_attributes = pd.DataFrame(attributes_data)
    
    # Save to Excel with multiple sheets
    output_path = Path(__file__).parent.parent / 'templates' / 'garmin_fitness_template.xlsx'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_areas.to_excel(writer, sheet_name='Areas', index=False)
        df_categories.to_excel(writer, sheet_name='Categories', index=False)
        df_attributes.to_excel(writer, sheet_name='Attributes', index=False)
    
    print(f"✅ Template created: {output_path}")
    print(f"   - {len(areas_data)} Areas")
    print(f"   - {len(categories_data)} Categories")
    print(f"   - {len(attributes_data)} Attributes")
    
    return output_path

if __name__ == '__main__':
    generate_template()
