from fireworks import FiretaskBase, explicit_serialize, Firework, FWAction
from pathlib import Path
import subprocess
import os
import shutil

@explicit_serialize
class GenerateSamplingDirectionsFiretask(FiretaskBase):
    required_params = ["latitude", "longitude", "dni_file", "output_file", "executable"]

    def run_task(self, fw_spec):
        latitude = str(self["latitude"])
        longitude = str(self["longitude"])
        dni_file = Path(self["dni_file"]).resolve()
        output_file = Path(self["output_file"]).resolve()
        exe = Path(self["executable"]).resolve()

        if not exe.exists():
            raise FileNotFoundError(f"Sampling directions generator not found at {exe}")

        print(f"[GenerateSampling] Running: {exe} {latitude} {longitude} {dni_file} {output_file}")
        subprocess.run(
            [str(exe), latitude, longitude, str(dni_file), str(output_file)],
            check=True
        )

        # Clean up launcher dir if inside one
        current_dir = Path.cwd()
        if current_dir.name.startswith("launcher_"):
            os.chdir(current_dir.parent)
            shutil.rmtree(current_dir)

        return FWAction()

def get_generate_sampling_firework(project_manager, executable_path):
    return Firework(
        GenerateSamplingDirectionsFiretask(
            latitude=project_manager.latitude,
            longitude=project_manager.longitude,
            dni_file=str(project_manager.dni_file),
            output_file=str(project_manager.sampling_file),
            executable=str(executable_path)
        ),
        name="Generate Sun Sampling Directions"
    )