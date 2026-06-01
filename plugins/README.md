# Pixel Pet Theme Plugins

Pixel Token Pet loads its character art from:

```text
plugins/<theme_id>/pet_theme.json
```

Select a theme from the gear settings panel or by editing `config.json`:

```json
{
  "theme": "default_blob"
}
```

## Bundled Themes

- `default_blob`
- `fox`
- `dog`
- `cat`
- `whale`
- `rabbit`
- `panda`
- `penguin`
- `frog`
- `hamster`
- `owl`

Copy one of these folders when you want to make a new theme.

## Creating A Plugin

1. Create a folder under `plugins/`, for example `plugins/my_pet/`.
2. Add `pet_theme.json`.
3. Set `"theme": "my_pet"` in `config.json` or choose it from the gear settings panel.
4. Restart the app or save settings again.

Theme folders are intentionally self-contained so other people can share only the folder they made.

## Minimal Theme

```json
{
  "schema_version": 1,
  "name": "My Pet",
  "pixel_size": 6,
  "origin": { "x": 18, "y": 16 },
  "palette": {
    "outline": "#5a3d7a",
    "body": "#c9a8ff",
    "eye": "#231b2e",
    "cheek": "#ff8bd4"
  },
  "animations": {
    "idle": {
      "blink_every": 26,
      "blink_frames": [0, 1],
      "bob_every": 18,
      "bob_frames": 9,
      "frames": [
        [
          "0011111100",
          "0112222210",
          "1122222221",
          "1222323221",
          "1222222221",
          "1222442221",
          "0122222210",
          "0012112100",
          "0001001000"
        ]
      ]
    }
  },
  "speech": {
    "title": "PIXEL TOKEN PET",
    "hint": "right click menu / dblclick done",
    "done_title": "DONE!",
    "done_body": "Codex finished the task."
  }
}
```

## Pixel Symbols

- `0`, `.`, and spaces are transparent.
- `1` maps to `palette.outline`.
- `2` maps to `palette.body`.
- `3` maps to `palette.eye`; it is hidden during blink frames.
- `4` maps to `palette.cheek`.
- Any other symbol can map directly to a palette key with the same name.

For example, a row containing `55` will use `palette["5"]` if present.

## Animation Fields

- `frames`: list of pixel-art frames. Multiple frames cycle automatically.
- `blink_every`: frame interval for blinking. Set `0` to disable.
- `blink_frames`: frame indexes inside the blink interval where eye pixels disappear.
- `bob_every`: frame interval for vertical bobbing. Set `0` to disable.
- `bob_frames`: number of frames in the interval where the pet is shifted down by one pixel.

Keep art around 10-16 columns wide and 8-14 rows tall for the current window layout.
