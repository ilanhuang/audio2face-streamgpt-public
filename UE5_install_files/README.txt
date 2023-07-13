# Audio2Face to Unreal Engine Metahuman Animation Redirector

This repository contains the necessary extension and scripts to redirect animations from Audio2Face to a Metahuman in Unreal Engine 5.1 or higher.

## Installation

Follow these steps to install and verify the extension:

1. Copy the `extension` file from this repository.

2. Paste the `extension` file into the following directory (or similar, depending on your system setup):

```
C:\Users\Username\AppData\Local\ov\pkg\audio2face-2022.2.1\exts\omni.audio2face.exporter\config
```

3. Open Audio2Face, navigate to the 'Windows' tab and enable 'Script Editor'.

4. In the script editor, enter the following lines:

```python
import pythonosc
print(pythonosc)
```

5. Click 'Run'. If no errors appear, the extension is installed correctly.

## FacsSolver Setup

1. Copy the `FacsSolver` file from this repository.

2. Paste the `FacsSolver` file into the following directory (or similar, depending on your system setup):

```
C:\Users\Username\AppData\Local\ov\pkg\audio2face-2022.2.1\exts\omni.audio2face.exporter\omni\audio2face\exporter\scripts
```

## INSIDE UE5 - Metahuman Blueprints

Follow this [tutorial video](https://www.youtube.com/watch?v=y1wVykdmJNM) to set up the corresponding blueprint for your metahuman.