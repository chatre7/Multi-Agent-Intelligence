
import os
import yaml
import glob

def validate_agent_configs():
    config_dir = r"d:\cmtn-project\Multi-Agent-Intelligence\backend\configs\agents"
    files = glob.glob(os.path.join(config_dir, "**", "*.yaml"), recursive=True)
    
    print(f"Found {len(files)} agent configuration files.")
    print("-" * 60)
    
    helpers_valid = True
    
    for file_path in files:
        rel_path = os.path.relpath(file_path, config_dir)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            agent_id = data.get('id', 'MISSING')
            model = data.get('model_name', 'MISSING')
            
            # Check for generic/invalid models
            status = "[OK]"
            issue = ""
            
            if model == 'MISSING' or model == 'default':
                status = "[WARN]"
                issue = "Model is 'default' or missing. Ensure env LLM_MODEL is set."
            elif "gpt-oss" in model:
                 status = "[NOTE]"
                 issue = f"Using placeholder model '{model}' - ensure this maps to a real backend."
            
            print(f"{status} {rel_path:<30} ID: {agent_id:<15} Model: {model}")
            if issue:
                print(f"      -> {issue}")
                
        except Exception as e:
            print(f"[FAIL] {rel_path}: Failed to parse YAML - {e}")
            helpers_valid = False
            
    print("-" * 60)
    if helpers_valid:
        print("All agent configs are syntactically valid.")
    else:
        print("Some agent configs have errors.")

if __name__ == "__main__":
    validate_agent_configs()
