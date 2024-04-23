import argparse
from midiutil import MIDIFile
import vtk

note_mappings = {
    "C4": 60, "D4": 62, "E4": 64, "F4": 65,
    "G4": 67, "A4": 69, "B4": 71,
    "C5": 72, "D5": 74, "E5": 76, "F5": 77
}

def note_to_midi(note):
    return note_mappings.get(note, 60)  # Default to 60 (Middle C) if not found

def load_objects_from_mvo(filename):
    objects = []
    with open(filename, 'r') as file:
        current_object = {}
        for line in file:
            line = line.strip()
            if line == "begin_object":
                current_object = {}
            elif line == "end_object":
                if current_object:
                    objects.append(current_object)
            elif line and ':' in line:
                key, value = line.split(': ', 1)
                if key == "position":
                    current_object[key] = tuple(map(float, value.split(', ')))
                elif key == "size_duration":
                    current_object[key] = float(value)  # Use float for generic handling
                else:
                    current_object[key] = value
    return objects

def create_midi_from_mvo(mvo_filename):
    objects = load_objects_from_mvo(mvo_filename)
    midi = MIDIFile(len(objects))  # Assume max possible tracks; adjust dynamically if necessary

    track_details = {}  # Dictionary to map instruments to tracks
    tempo_set = set()  # Set to keep track of which tracks have had tempo set

    current_track = 0
    for obj in objects:
        instrument = obj["instrument_shape"].split('_')[0]  # Get instrument name
        if instrument not in track_details:
            track_details[instrument] = current_track
            midi.addTrackName(current_track, 0, instrument)
            midi.addTempo(current_track, 0, 120)  # Set tempo to 120 BPM for each new track
            current_track += 1

        track = track_details[instrument]
        channel = 0  # Channels can be reused across different tracks
        note = note_to_midi(obj["note_color"].split('_')[0])
        duration = int(obj["size_duration"])
        volume = 100

        midi.addProgramChange(track, channel, 0, 1)  # Assuming program change if needed, 1 is a placeholder
        midi.addNote(track, channel, note, 0, duration, volume)  # Start time set to 0 for simplicity

    with open("output.mid", "wb") as output_file:
        midi.writeFile(output_file)

def note_to_midi(note):
    return note_mappings.get(note, 60)  # Default to Middle C if not found


def create_vtk_from_mvo(mvo_filename):
    objects = load_objects_from_mvo(mvo_filename)
    colors = vtk.vtkNamedColors()

    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)

    for obj in objects:
        shape = obj["instrument_shape"].split('_')[1]
        color = obj["note_color"].split('_')[1]
        size = obj["size_duration"]

        if shape == "sphere":
            source = vtk.vtkSphereSource()
            source.SetRadius(size)  # size is already a float
        elif shape == "cube":
            source = vtk.vtkCubeSource()
            source.SetXLength(size)
            source.SetYLength(size)
            source.SetZLength(size)
        else:
            continue

        source.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(colors.GetColor3d(color))
        actor.SetPosition(*obj["position"])

        renderer.AddActor(actor)

    render_window.Render()
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    interactor.Start()

def main():
    parser = argparse.ArgumentParser(description="Generate MIDI and VTK files from .mvo format.")
    parser.add_argument("filename", type=str, help="The .mvo file to process")
    parser.add_argument("--midi", action="store_true", help="Generate MIDI file")
    parser.add_argument("--vtk", action="store_true", help="Generate VTK file")

    args = parser.parse_args()

    if args.midi:
        print(f"Generating MIDI from {args.filename}")
        create_midi_from_mvo(args.filename)

    if args.vtk:
        print(f"Generating VTK from {args.filename}")
        create_vtk_from_mvo(args.filename)

if __name__ == "__main__":
    main()
