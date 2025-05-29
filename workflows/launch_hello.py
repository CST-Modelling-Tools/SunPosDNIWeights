from fireworks import LaunchPad
from hello_task import create_hello_workflow

lp = LaunchPad.auto_load()  # uses my_launchpad.yaml
wf = create_hello_workflow()
lp.add_wf(wf)
print("✅ Hello workflow submitted.")