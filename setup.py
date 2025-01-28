import os

# Create output directories
def create_output_dirs():
    base_dir = "Outputs"
    batch_dir = os.path.join(base_dir, "06107-20241205-01")
    
    # Create directories if they don't exist
    os.makedirs(batch_dir, exist_ok=True)
    
    # Create empty .gitkeep files to track empty directories
    with open(os.path.join(batch_dir, ".gitkeep"), "w") as f:
        pass
        
    print("Created output directories:")
    print(f"- {base_dir}/")
    print(f"- {batch_dir}/")

if __name__ == "__main__":
    create_output_dirs() 