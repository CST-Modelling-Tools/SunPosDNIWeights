from fireworks import LaunchPad, Workflow
from generate_sampling import get_generate_sampling_firework
from project_manager import ProjectManager
from pathlib import Path

def main():
    # Set the path to your project root
    root_dir = Path("C:/Users/manue_6t240gh/Dropbox/OpenSource/SunPosDNIWeights")

    # Create the project manager to read config.json
    pm = ProjectManager(root_dir)

    # Define path to the executable (.exe) built by Visual Studio Code
    build_type = "Release"  # or "Debug"
    exe_path = root_dir / "build" / "tools" / "GenerateSamplingDirectionsAndWeights" / build_type / "GenerateSamplingDirectionsAndWeights.exe"

    # Create the Firework
    fw_generate = get_generate_sampling_firework(pm, exe_path)

    # Assemble the workflow
    wf = Workflow([fw_generate], name=f"GenerateSampling_{pm.project_name}")

    # Load the Firework(s) into the LaunchPad
    lpad = LaunchPad.auto_load()  # Assumes FW_config.yaml is present
    lpad.add_wf(wf)
    print("Workflow added to LaunchPad.")

if __name__ == "__main__":
    main()
