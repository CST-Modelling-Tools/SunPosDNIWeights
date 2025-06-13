from pathlib import Path
from fireworks import Workflow, Firework
from firetasks.create_next_population_folder import CreateNextPopulationFolderFiretask
from firetasks.generate_next_parameter_set import GenerateNextParameterSetFiretask
from firetasks.generate_biomimetic_layout_from_parameters import GenerateBiomimeticLayoutFiretask
from firetasks.run_tonatiuh import RunTonatiuhSimulationFiretask
from firetasks.compute_fitness import ComputeFitnessFiretask
from project_manager import ProjectManager

def get_biomimetic_optimization_workflow(project_root: str) -> Workflow:
    project_root = Path(project_root).resolve()
    project_manager = ProjectManager(project_root)

    # Initial Firework: create population folder
    fw_create_folder = Firework(
        CreateNextPopulationFolderFiretask(project_root=str(project_root)),
        name="Create Population Folder"
    )

    population_size = project_manager.population_size
    optimization_config = project_manager.optimization_config
    generation_fws = []

    for i in range(population_size):
        fw_generate_params = Firework(
            GenerateNextParameterSetFiretask(
                project_root=str(project_root),
                parameter_index=i
            ),
            name=f"Generate Params {i}"
        )

        fw_generate_layout = Firework(
            GenerateBiomimeticLayoutFiretask(
                project_root=str(project_root),
                parameter_index=i
            ),
            name=f"Generate Layout {i}"
        )

        fw_run_tonatiuh = Firework(
            RunTonatiuhSimulationFiretask(
                tn_script=None,  # Filled dynamically by fw_spec
                tn_executable=str(project_manager.tonatiuh_exe)
            ),
            name=f"Run Tonatiuh {i}"
        )

        fw_compute_fitness = Firework(
            ComputeFitnessFiretask(
                project_root=str(project_root),
                parameter_index=i
            ),
            name=f"Compute Fitness {i}"
        )

        generation_fws.extend([fw_generate_params, fw_generate_layout, fw_run_tonatiuh, fw_compute_fitness])

        # Set dependencies within each chain
        fw_generate_layout._prev = [fw_generate_params]
        fw_run_tonatiuh._prev = [fw_generate_layout]
        fw_compute_fitness._prev = [fw_run_tonatiuh]

    # Create dependency structure
    all_fireworks = [fw_create_folder] + generation_fws
    links = {fw_create_folder: [fw for fw in generation_fws if "Generate Params" in fw.name]}

    return Workflow(fireworks=all_fireworks, links_dict=links, name=f"{project_manager.project_name}_optimization")