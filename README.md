# smart-christmas-village
Christmas village with lighting by vixen. Sequences are played using a combination of motion and gesture detection.
Detected motion increases a temperature variable, an increased temperature increases the chance of a sequence playing.
TODO: Config for sensitivity

## Hardware requirements
* Arduino or arduino clone
* Windows device running Vixen with webserver enabled
* Webcam
* WS2812B pixel string or similar

## Setup
### Vixen lights
1. Setup display -> Add elements: Single item -> They can be any color, full RGB
2. Right click added element and press: Add multiple
3. Add generic serial controller
  -   Outputs: 3x #No. pixels
  -   Send text header: ">>XXX<<" Replacing XXX with number of pixels, 050 for 50 pixels e.g.
  -   Baud rate: match with arduino script
  -   Port: choose correct one
4. In home screen: Tools -> Webserver
  - Select corresponding port with vixen_commands.py
5. Create sequences or import from the sequence pack provided

### Arduino
1. Change variables to available setup
  - Number of leds
  - Baud rate: highest available for your board is likely best performant
  - Data pin: choose the appropriate data pin
Wiring tip: Ensure ground of led string power supply and arduino ground are connected!

### Python
Run both christmas_cv_runner.py and christmas_show_runner.py to have your setup use motion and gesture detection.
Currently implemented gestures:
- Thumbs down: Skips to next song, forces song to be played

## Showcase
https://github.com/rapsac2010/smart-christmas-village/assets/49317512/b1d51dea-57ba-4320-aa3e-f1a1da2d1953


