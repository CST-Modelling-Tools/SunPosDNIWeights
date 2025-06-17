from fireworks import FiretaskBase, Firework, LaunchPad, Workflow, explicit_serialize

@explicit_serialize
class HelloTask(FiretaskBase):
    def run_task(self, fw_spec):
        print("🎉 Hello, FireWorks! Everything is working.")
        return None

def create_hello_workflow():
    task = HelloTask()
    fw = Firework(task, name="HelloFirework")
    return Workflow([fw], name="HelloWorkflow")
