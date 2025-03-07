import csv
import io
import re
from typing import Dict, List, Tuple, Union, Optional

class PredictiveMaintenanceETL:
    def __init__(self):
        self.field_requirements = {
            "machine_id": {"type": "string"},
            "runtime_hours": {"type": "positive_integer"},
            "vibration_level": {"type": "positive_number"},
            "temperature": {"type": "range", "min": 0, "max": 200},
            "maintenance_threshold": {"type": "range", "min": 0, "max": 100},
            "max_operating_hours": {"type": "positive_integer"},
            "scaling_factor": {"type": "positive_number"}
        }
        self.required_fields = list(self.field_requirements.keys())
        
    def parse_csv_data(self, csv_data: str) -> List[Dict]:
        """Parse CSV data into a list of dictionaries."""
        try:
            # Strip any leading/trailing whitespace and remove any potential BOM
            csv_data = csv_data.strip()
            
            # Parse CSV data
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            records = list(csv_reader)
            
            # Check if any records were parsed
            if not records:
                raise ValueError("No data found in the CSV input")
                
            return records
        except Exception as e:
            return f"ERROR: Invalid data format. Please provide data in CSV format. Details: {str(e)}"
    
    def validate_data(self, records: List[Dict]) -> Tuple[bool, str, List[Dict]]:
        """Validate the parsed CSV data against requirements."""
        valid_records = []
        errors = []
        
        # Check for required fields in header
        first_record = records[0]
        missing_fields = [field for field in self.required_fields if field not in first_record]
        if missing_fields:
            return False, f"ERROR: Missing required field(s): {', '.join(missing_fields)} in header.", []
        
        # Validate each record
        for i, record in enumerate(records, 1):
            row_errors = []
            valid_record = {}
            
            # Check for missing fields
            for field in self.required_fields:
                if field not in record or record[field].strip() == '':
                    row_errors.append(f"Missing required field: {field}")
                    continue
                
                # Validate field values
                value = record[field].strip()
                requirements = self.field_requirements[field]
                
                if requirements["type"] == "string":
                    valid_record[field] = value
                    
                elif requirements["type"] == "positive_integer":
                    try:
                        num_value = int(value)
                        if num_value <= 0:
                            row_errors.append(f"Invalid value for {field}: must be a positive integer")
                        else:
                            valid_record[field] = num_value
                    except ValueError:
                        row_errors.append(f"Invalid value for {field}: must be a positive integer")
                        
                elif requirements["type"] == "positive_number":
                    try:
                        num_value = float(value)
                        if num_value <= 0:
                            row_errors.append(f"Invalid value for {field}: must be a positive number")
                        else:
                            valid_record[field] = num_value
                    except ValueError:
                        row_errors.append(f"Invalid value for {field}: must be a positive number")
                        
                elif requirements["type"] == "range":
                    try:
                        num_value = float(value)
                        if num_value < requirements["min"] or num_value > requirements["max"]:
                            row_errors.append(f"Invalid value for {field}: must be between {requirements['min']} and {requirements['max']}")
                        else:
                            valid_record[field] = num_value
                    except ValueError:
                        row_errors.append(f"Invalid value for {field}: must be a number")
            
            if row_errors:
                errors.append(f"Row {i}: {', '.join(row_errors)}")
            else:
                valid_records.append(valid_record)
        
        if errors:
            return False, "\n".join(errors), []
        
        return True, "", valid_records
    
    def generate_validation_report(self, is_valid: bool, records: List[Dict], error_message: str = "") -> str:
        """Generate a data validation report in markdown format."""
        report = "# Data Validation Report\n"
        
        if records:
            report += "## Data Structure Check:\n"
            report += f"- Number of machines: {len(records)}\n"
            report += f"- Number of fields per record: {len(self.required_fields)}\n\n"
            
            report += "## Required Fields Check:\n"
            for field in self.required_fields:
                status = "present" if field in records[0] else "missing"
                report += f"- {field}: {status}\n"
            
            report += "\n## Validation Summary:\n"
            if is_valid:
                report += "Data validation is successful! Would you like to proceed with analysis or provide another dataset?"
            else:
                report += f"Validation failed with the following errors:\n```\n{error_message}\n```"
        else:
            report += "## Validation Summary:\n"
            report += f"Validation failed with the following errors:\n```\n{error_message}\n```"
        
        return report
    
    def calculate_metrics(self, record: Dict) -> Dict:
        """Calculate all required metrics for a machine record."""
        # Extract input values
        vibration_level = record["vibration_level"]
        scaling_factor = record["scaling_factor"]
        runtime_hours = record["runtime_hours"]
        max_operating_hours = record["max_operating_hours"]
        maintenance_threshold = record["maintenance_threshold"]
        
        # Calculate Predicted Failure Risk
        predicted_failure_risk = vibration_level * scaling_factor
        predicted_failure_risk = round(predicted_failure_risk, 2)
        
        # Calculate Maintenance Urgency Ratio
        maintenance_urgency_ratio = (predicted_failure_risk / runtime_hours) * 100
        maintenance_urgency_ratio = round(maintenance_urgency_ratio, 2)
        
        # Calculate Operating Margin
        operating_margin = ((max_operating_hours - runtime_hours) / max_operating_hours) * 100
        operating_margin = round(operating_margin, 2)
        
        # Calculate Composite Maintenance Score
        composite_score = (operating_margin * 0.3) + ((100 - maintenance_urgency_ratio) * 0.7)
        composite_score = round(composite_score, 2)
        
        # Calculate Efficiency Ratio
        efficiency_ratio = runtime_hours / predicted_failure_risk
        efficiency_ratio = round(efficiency_ratio, 2)
        
        # Determine final recommendation
        is_efficient = 0.90 <= efficiency_ratio <= 9.90
        is_urgent = maintenance_urgency_ratio > maintenance_threshold
        
        if composite_score >= 75 and is_efficient and not is_urgent:
            status = "Optimal"
            recommendation = "No immediate maintenance required"
        else:
            status = "Requires Maintenance"
            recommendation = "Schedule maintenance promptly"
        
        return {
            "predicted_failure_risk": predicted_failure_risk,
            "maintenance_urgency_ratio": maintenance_urgency_ratio,
            "operating_margin": operating_margin,
            "composite_score": composite_score,
            "efficiency_ratio": efficiency_ratio,
            "status": status,
            "recommendation": recommendation
        }
    
    def generate_analysis_report(self, records: List[Dict], calculations: List[Dict]) -> str:
        """Generate a detailed analysis report in markdown format."""
        report = f"# Predictive Maintenance Analysis Summary:\n"
        report += f"- **Total Machines Evaluated:** {len(records)}\n\n"
        
        report += "## Detailed Analysis per Machine:\n"
        
        for i, (record, calc) in enumerate(zip(records, calculations)):
            report += f"**Machine {record['machine_id']}**\n\n"
            
            report += "### Input Data:\n"
            report += f"- **Runtime Hours:** {record['runtime_hours']}\n"
            report += f"- **Vibration Level:** {record['vibration_level']}\n"
            report += f"- **Temperature:** {record['temperature']}\n"
            report += f"- **Maintenance Threshold (%):** {record['maintenance_threshold']}\n"
            report += f"- **Max Operating Hours:** {record['max_operating_hours']}\n"
            report += f"- **Scaling Factor:** {record['scaling_factor']}\n\n"
            
            report += "### Detailed Calculations:\n"
            
            # 1. Predicted Failure Risk
            report += "1. **Predicted Failure Risk Calculation:**\n"
            report += "   - **Formula:** $$ \\text{Predicted Failure Risk} = \\text{vibration_level} \\times \\text{scaling_factor} $$\n"
            report += f"   - **Steps:** Multiply vibration_level ({record['vibration_level']}) by scaling_factor ({record['scaling_factor']}).\n"
            report += f"   - **Final Predicted Failure Risk:** {calc['predicted_failure_risk']}\n\n"
            
            # 2. Maintenance Urgency Ratio
            report += "2. **Maintenance Urgency Ratio Calculation:**\n"
            report += "   - **Formula:** $$ \\text{Maintenance Urgency Ratio} = \\frac{\\text{Predicted Failure Risk}}{\\text{runtime_hours}} \\times 100 $$\n"
            report += f"   - **Steps:** Divide Predicted Failure Risk ({calc['predicted_failure_risk']}) by runtime_hours ({record['runtime_hours']}), then multiply by 100.\n"
            report += f"   - **Final Maintenance Urgency Ratio:** {calc['maintenance_urgency_ratio']}%\n\n"
            
            # 3. Operating Margin
            report += "3. **Operating Margin Calculation:**\n"
            report += "   - **Formula:** $$ \\text{Operating Margin} = \\frac{(\\text{max_operating_hours} - \\text{runtime_hours})}{\\text{max_operating_hours}} \\times 100 $$\n"
            report += f"   - **Steps:** Subtract runtime_hours ({record['runtime_hours']}) from max_operating_hours ({record['max_operating_hours']}), divide by max_operating_hours ({record['max_operating_hours']}), then multiply by 100.\n"
            report += f"   - **Final Operating Margin:** {calc['operating_margin']}%\n\n"
            
            # 4. Composite Maintenance Score
            report += "4. **Composite Maintenance Score Calculation:**\n"
            report += "   - **Formula:** $$ \\text{Composite Score} = (\\text{Operating Margin} \\times 0.3) + ((100 - \\text{Maintenance Urgency Ratio}) \\times 0.7) $$\n"
            report += f"   - **Steps:** Multiply Operating Margin ({calc['operating_margin']}) by 0.3 = {round(calc['operating_margin'] * 0.3, 2)}; subtract Maintenance Urgency Ratio ({calc['maintenance_urgency_ratio']}) from 100 = {round(100 - calc['maintenance_urgency_ratio'], 2)} and multiply by 0.7 = {round((100 - calc['maintenance_urgency_ratio']) * 0.7, 2)}; then add both values.\n"
            report += f"   - **Final Composite Score:** {calc['composite_score']}\n\n"
            
            # 5. Efficiency Ratio
            report += "5. **Efficiency Ratio Calculation:**\n"
            report += "   - **Formula:** $$ \\text{Efficiency Ratio} = \\frac{\\text{runtime_hours}}{\\text{Predicted Failure Risk}} $$\n"
            report += f"   - **Steps:** Divide runtime_hours ({record['runtime_hours']}) by Predicted Failure Risk ({calc['predicted_failure_risk']}).\n"
            report += f"   - **Final Efficiency Ratio:** {calc['efficiency_ratio']}\n\n"
            
            # Final Recommendation
            report += "### Final Recommendation:\n"
            report += f"- **Composite Score:** {calc['composite_score']}\n"
            report += f"- **Maintenance Urgency Ratio:** {calc['maintenance_urgency_ratio']}%\n"
            report += f"- **Efficiency Ratio:** {calc['efficiency_ratio']}\n"
            report += f"- **Status:** {calc['status']}\n"
            report += f"- **Recommended Action:** {calc['recommendation']}\n\n"
            
            if i < len(records) - 1:
                report += "---\n\n"
        
        return report
    
    def process_csv_data(self, csv_data: str) -> str:
        """Process CSV data and generate appropriate reports."""
        # Parse CSV data
        records = self.parse_csv_data(csv_data)
        
        # Check if parsing returned an error
        if isinstance(records, str):
            return records
        
        # Validate data
        is_valid, error_message, valid_records = self.validate_data(records)
        
        # Generate validation report
        validation_report = self.generate_validation_report(is_valid, valid_records, error_message)
        
        # If validation failed, return only the validation report
        if not is_valid:
            return validation_report
        
        # Calculate metrics for each valid record
        calculations = [self.calculate_metrics(record) for record in valid_records]
        
        # Generate analysis report
        analysis_report = self.generate_analysis_report(valid_records, calculations)
        
        return f"{validation_report}\n\n{analysis_report}"


def main():
    """Main function with sample data."""
    etl_processor = PredictiveMaintenanceETL()
    
    print("Greetings! I am CSV_ETL_PredictiveMaintenance-AI, ready to help with your predictive maintenance data processing.")
    
    # Sample data
    sample_data = """machine_id,runtime_hours,vibration_level,temperature,maintenance_threshold,max_operating_hours,scaling_factor
M501,50,2,80,30,200,5
M502,40,3,85,35,300,4
M503,30,2,65,25,100,3
M504,60,4,90,20,120,2
M505,70,3,75,15,150,3
M506,80,2,88,15,200,5
M507,45,3,82,25,150,3
M508,500,1,75,10,600,1
M509,300,2,85,5,400,1
M510,20,2,70,30,80,2"""
    
    print("\nProcessing sample data:")
    print(sample_data)
    print("\nGenerating report...\n")
    
    # Process the sample data
    result = etl_processor.process_csv_data(sample_data)
    print(result)


if __name__ == "__main__":
    main()