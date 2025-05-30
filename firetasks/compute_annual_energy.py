from fireworks import FiretaskBase, explicit_serialize, Firework
from pathlib import Path
import subprocess
import os
import shutil

@explicit_serialize
class ComputeAnnualEnergyFiretask(FiretaskBase):
    """
    Firetask that runs the C++ AnnualEnergy program to compute total energy and average efficiency.

    Required parameters:
        - input_file: Path to the Tonatiuh++ simulation results CSV
        - output_file: Path to save the summary (.csv or .json)
        - executable: Path to AnnualEnergy C++ executable
    """

    required_params = ["input_file", "output_file", "executable"]

    def run_task(self, fw_spec):
        input_file = Path(self["input_file"]).resolve()
        output_file = Path(self["output_file"]).resolve()
        exe = Path(self["executable"]).resolve()

        if not exe.exists():
            raise FileNotFoundError(f"AnnualEnergy executable not found at: {exe}")
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        print(f"Running: {exe} {input_file} {output_file}")
        subprocess.run([str(exe), str(input_file), str(output_file)], check=True)

        print(f"Annual energy results saved to: {output_file}")

        # --- Cleanup: remove launcher dir if inside one ---
        current_dir = Path.cwd()
        if current_dir.name.startswith("launcher_"):
            print(f"Cleaning up launcher directory: {current_dir}")
            os.chdir(current_dir.parent)  # Step out of the folder to allow deletion
            shutil.rmtree(current_dir)


def get_compute_annual_energy_firework(project_manager, executable_path):
    """
    Creates a Firework to run the AnnualEnergy C++ program.

    Args:
        project_manager: ProjectManager instance
        executable_path: Path to the AnnualEnergy binary

    Returns:
        A Firework ready to include in the FireWorks workflow.
    """
    input_file = project_manager.results_dir / f"{project_manager.result_file_prefix}.csv"
    output_file = project_manager.results_dir / "annual_energy.csv"

    return Firework(
        ComputeAnnualEnergyFiretask(
            input_file=str(input_file),
            output_file=str(output_file),
            executable=str(executable_path)
        ),
        name="Compute Annual Energy"
    )