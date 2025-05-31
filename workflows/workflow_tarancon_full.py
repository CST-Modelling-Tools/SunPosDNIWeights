from fireworks import Workflow
from firetasks.generate_sampling import get_generate_sampling_firework
from firetasks.run_tonatiuh import get_run_tonatiuh_firework
from firetasks.compute_annual_energy import get_compute_annual_energy_firework
from project_manager import ProjectManager
from pathlib import Path

def get_tarancon_workflow(pm: ProjectManager, layout_file: Path) -> Workflow:
    sampling_exe = pm.sampling_exe
    tonatiuh_exe = pm.tonatiuh_exe
    energy_exe = pm.energy_exe

    fw_sampling = get_generate_sampling_firework(pm, sampling_exe)
    fw_tonatiuh = get_run_tonatiuh_firework(pm, tonatiuh_exe)
    fw_energy = get_compute_annual_energy_firework(pm, energy_exe)

    wf = Workflow(
        [fw_sampling, fw_tonatiuh, fw_energy],
        links_dict={
            fw_sampling.fw_id: [fw_tonatiuh.fw_id],
            fw_tonatiuh.fw_id: [fw_energy.fw_id],
        },
        name=f"Tarancon_Full_Optimization_{pm.project_name}"
    )

    wf.metadata = {
        "project": pm.project_name,
        "layout": str(layout_file.name),
        "dni": str(pm.dni_file.name)
    }

    return wf