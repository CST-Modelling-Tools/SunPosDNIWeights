from fireworks import FiretaskBase, explicit_serialize, Firework
from pathlib import Path
import subprocess

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

        print(f"Running: {exe} {latitude} {longitude} {dni_file} {output_file}")
        subprocess.run(
            [str(exe), str(latitude), str(longitude), str(dni_file), str(output_file)],
            check=True
        )

def get_generate_sampling_firework(project_manager, executable_path):
    """
    Utility function to build the Firework that runs the GenerateSamplingDirectionsAndWeights tool.
    """
    return Firework(
        GenerateSamplingDirectionsFiretask(
            latitude=project_manager.latitude,
            longitude=project_manager.longitude,
            dni_file=project_manager.dni_file,
            output_file=project_manager.sampling_file,
            executable=executable_path
        ),
        name="Generate Sun Sampling Directions"
    )