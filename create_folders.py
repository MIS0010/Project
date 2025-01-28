import os

def create_project_structure():
    # Create main directories
    directories = [
        'input/documents',
        'output/processed'
    ]
    
    for directory in directories:
        # Create directory
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
        
        # Create .gitkeep file
        gitkeep_path = os.path.join(directory, '.gitkeep')
        with open(gitkeep_path, 'w') as f:
            pass
        print(f"Created .gitkeep in: {directory}")

if __name__ == "__main__":
    create_project_structure() 