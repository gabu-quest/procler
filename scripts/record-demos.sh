#!/usr/bin/env bash
# Record terminal demos for Procler README
# Requires: asciinema (uv tool install asciinema)
# Optional: agg for GIF (cargo install agg), svg-term-cli for SVG (npx svg-term-cli)
#
# TODO: Install agg on a box with Rust toolchain and generate GIFs:
#   cargo install agg
#   agg docs/demos/basic-workflow.cast docs/demos/basic-workflow.gif --font-size 14
#   (repeat for group-start and recipe-execution)
set -euo pipefail

DEMO_DIR="docs/demos"
mkdir -p "$DEMO_DIR"

# Helper: record a scripted demo
record_demo() {
    local name="$1"
    local script="$2"
    local cast_file="$DEMO_DIR/${name}.cast"

    echo "Recording: $name"

    # Write the script to a temp file
    local tmp_script
    tmp_script=$(mktemp)
    cat > "$tmp_script" << 'SCRIPT_HEADER'
#!/usr/bin/env bash
set -e
# Simulate typing with delays
type_cmd() {
    echo ""
    echo -n "$ "
    for ((i=0; i<${#1}; i++)); do
        echo -n "${1:$i:1}"
        sleep 0.04
    done
    echo ""
    sleep 0.3
    eval "$1"
    sleep 0.8
}
SCRIPT_HEADER
    echo "$script" >> "$tmp_script"
    chmod +x "$tmp_script"

    asciinema rec "$cast_file" --overwrite -c "bash $tmp_script"
    rm -f "$tmp_script"

    echo "Saved: $cast_file"
}

# Convert .cast to SVG (works on GitHub without images)
convert_to_svg() {
    local name="$1"
    local cast_file="$DEMO_DIR/${name}.cast"
    local svg_file="$DEMO_DIR/${name}.svg"

    if command -v svg-term &>/dev/null || npx --yes svg-term-cli --version &>/dev/null 2>&1; then
        echo "Converting $name to SVG..."
        npx --yes svg-term-cli --in "$cast_file" --out "$svg_file" --window --no-cursor --padding 10
        echo "Saved: $svg_file"
    else
        echo "svg-term-cli not available, skipping SVG conversion"
    fi
}

# Convert .cast to GIF (requires agg)
convert_to_gif() {
    local name="$1"
    local cast_file="$DEMO_DIR/${name}.cast"
    local gif_file="$DEMO_DIR/${name}.gif"

    if command -v agg &>/dev/null; then
        echo "Converting $name to GIF..."
        agg "$cast_file" "$gif_file" --font-size 14 --theme monokai
        echo "Saved: $gif_file"
    else
        echo "agg not available, skipping GIF conversion"
        echo "Install with: cargo install agg"
    fi
}

echo "=== Procler Demo Recordings ==="
echo ""

# Demo 1: Basic Workflow
record_demo "basic-workflow" '
type_cmd "procler config init --force"
type_cmd "procler define --name my-api --command \"echo Server running on port 8000 && sleep 30\""
type_cmd "procler start my-api"
type_cmd "procler status my-api"
type_cmd "procler logs my-api --tail 5"
type_cmd "procler stop my-api"
type_cmd "procler remove my-api"
echo ""
echo "Done!"
sleep 1
'

# Demo 2: Group Start
record_demo "group-start" '
type_cmd "cat .procler/config.yaml"
type_cmd "procler config validate"
type_cmd "procler group start backend"
type_cmd "procler group status backend"
type_cmd "procler group stop backend"
echo ""
echo "Done!"
sleep 1
'

# Demo 3: Recipe Execution
record_demo "recipe-execution" '
type_cmd "procler recipe list"
type_cmd "procler recipe show deploy"
type_cmd "procler recipe run deploy --dry-run"
echo ""
echo "Done!"
sleep 1
'

echo ""
echo "=== Converting to SVG ==="
for demo in basic-workflow group-start recipe-execution; do
    convert_to_svg "$demo"
done

echo ""
echo "=== Converting to GIF ==="
for demo in basic-workflow group-start recipe-execution; do
    convert_to_gif "$demo"
done

echo ""
echo "=== Done ==="
echo "Cast files: $DEMO_DIR/*.cast"
echo "To re-convert: npx svg-term-cli --in FILE.cast --out FILE.svg --window"
echo "To re-convert: agg FILE.cast FILE.gif --font-size 14"
